from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import mysql.connector
import uuid
import bcrypt
import datetime
import jwt
from mysql.connector import Error
import traceback
from functools import wraps # NEW IMPORT

app = Flask(__name__)
# IMPORTANT: Adjust origins for production
CORS(app, origins=["http://localhost:5173"], supports_credentials=True)

# IMPORTANT: Change this key to a secure, complex value in production
app.config["SECRET_KEY"] = "fanime@2006"


def get_db_connection():
    """Establishes and returns a database connection."""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Fanime@2006",
        database="project"
    )

# --- JWT DECORATOR (New Security Implementation) 🔐 ---

def token_required(f):
    """
    Decorator to verify JWT token in cookies and inject the user_id into the route function.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("token")
        if not token:
            # Check for Authorization header as a fallback/alternative, though cookies are preferred for web apps
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            else:
                return jsonify({"message": "Authentication token is missing"}), 401
        
        try:
            # Decode the token
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            # Inject the user_id into the keyword arguments of the decorated function
            kwargs['user_id'] = data["user_id"] 
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Authentication token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid authentication token"}), 401
        except Exception:
            return jsonify({"message": "Token verification error"}), 401
            
        return f(*args, **kwargs)
    return decorated


# --- USER AUTH ROUTES 🔐 ---
# These remain largely unchanged, as they handle token creation/verification.

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM users WHERE email=%s OR username=%s", (email, username))
        if cursor.fetchone():
            return jsonify({"message": "User already exists"}), 400

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user_id = str(uuid.uuid4())

        cursor.execute(
            "INSERT INTO users (id, username, email, password_hash, created_at) VALUES (%s, %s, %s, %s, %s)",
            (user_id, username, email, hashed.decode("utf-8"), datetime.datetime.utcnow()),
        )
        conn.commit()

        token = jwt.encode(
            {"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)},
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        resp = make_response(jsonify({"message": "Signup successful"}))
        resp.set_cookie("token", token, httponly=True, samesite="Lax")
        return resp, 201
    except Error as e:
        print(f"Database Error: {e}")
        return jsonify({"error": "A database error occurred during signup"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            return jsonify({"message": "Invalid email or password"}), 401

        token = jwt.encode(
            {"user_id": user["id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)},
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        resp = make_response(jsonify({"message": "Login successful", "user_id": user["id"]}))
        resp.set_cookie("token", token, httponly=True, samesite="Lax")
        return resp, 200
    except Exception as e:
        print(f"Error during login: {e}")
        return jsonify({"error": "An error occurred during login"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/verify-token", methods=["GET"])
def verify_token():
    token = request.cookies.get("token")
    if not token:
        return jsonify({"logged_in": False}), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        decoded = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        # Now we also return the user_id so the frontend can use it (since it's no longer in the URL)
        user_id = decoded["user_id"] 
        
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"logged_in": False}), 401

        return jsonify({"logged_in": True, "username": user["username"], "user_id": user_id}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"logged_in": False, "message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"logged_in": False, "message": "Invalid Token"}), 401
    except Exception:
        return jsonify({"logged_in": False, "message": "Verification error"}), 401
    finally:
        cursor.close()
        conn.close()

@app.route("/logout", methods=["POST"])
def logout():
    """Removes the authentication cookie (JWT) to log the user out."""
    resp = make_response(jsonify({"message": "Logged out successfully"}), 200)
    resp.set_cookie("token", "", expires=0, httponly=True, samesite="Lax")
    return resp
    
# --- GET DATA ROUTES (MODIFIED TO USE DECORATOR) 🥗 ---

# Note: The original /get-pantry route was fetching all pantry items, which is unsafe.
# I'm keeping the original function name and changing it to use the new decorator
# and enforce user-specific retrieval.

@app.route("/pantry", methods=["GET"])
@token_required
def get_pantry_by_user(user_id):
    # user_id is passed by the token_required decorator
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT pantry.id, pantry.ingredient_id, pantry.quantity, pantry.unit, 
                   pantry.expiration_date, ingredient.name AS name
            FROM pantry
            JOIN ingredient ON pantry.ingredient_id = ingredient.id
            WHERE pantry.user_id = %s
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception as e:
        print(f"Error getting pantry for user {user_id}: {e}")
        traceback.print_exc()
        return jsonify({"error": "Failed to fetch pantry items"}), 500
    finally:
        cursor.close()
        conn.close()

# /ingredients does not need authentication if it lists global ingredients
@app.route("/ingredients", methods=["GET"])
def get_all_ingredients():
    """Fetches all ingredients from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM ingredient ORDER BY name") 
        rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception as e:
        print("MySQL Error:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/recipes", methods=["GET"])
@token_required
def get_recipes(user_id):
    # user_id is passed by the token_required decorator
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM recipe WHERE user_id = %s", (user_id,))
        rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception as e:
        print(f"Error getting recipes for user {user_id}: {e}")
        return jsonify({"error": "Failed to fetch recipes"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/recipe-ingredients", methods=["GET"])
@token_required
def get_recipe_ingredients(user_id):
    # user_id is passed by the token_required decorator
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT ri.id, ri.quantity, ri.unit, r.title AS recipe_title, i.name AS ingredient_name
            FROM recipe_ingredient ri
            JOIN recipe r ON ri.recipe_id = r.id
            JOIN ingredient i ON ri.ingredient_id = i.id
            WHERE r.user_id = %s
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception as e:
        print(f"Error getting recipe ingredients for user {user_id}: {e}")
        return jsonify({"error": "Failed to fetch recipe ingredients"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/shopping-list", methods=["GET"])
@token_required
def get_shopping_list(user_id):
    # user_id is passed by the token_required decorator
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT sl.id, sl.quantity, sl.unit, i.name AS ingredient_name, sl.ingredient_id
            FROM shopping_list sl
            JOIN ingredient i ON sl.ingredient_id = i.id
            WHERE sl.user_id = %s
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception as e:
        print(f"Error getting shopping list for user {user_id}: {e}")
        return jsonify({"error": "Failed to fetch shopping list"}), 500
    finally:
        cursor.close()
        conn.close()

# --- POST/UPDATE/DELETE ROUTES (MODIFIED TO USE DECORATOR) 🛒 ---
# Note: For POST/PATCH/DELETE, data (like item_id) is taken from the JSON body or URL,
# while the critical user_id is taken from the token.

@app.route("/buy-item/<item_id>", methods=["POST"])
@token_required
def buy_item(user_id, item_id):
    """Handles checking out an item from the shopping list and adding it to the pantry, enforcing unit match."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Get item from shopping list (ensure user ownership)
        cursor.execute("""
            SELECT ingredient_id, quantity, unit
            FROM shopping_list
            WHERE id = %s AND user_id = %s
        """, (item_id, user_id))
        item = cursor.fetchone()

        if not item:
            return jsonify({"error": "Item not found in shopping list or does not belong to user"}), 404

        # 2. Check for existing pantry item
        cursor.execute("""
            SELECT id, quantity, unit FROM pantry 
            WHERE user_id = %s AND ingredient_id = %s
        """, (user_id, item["ingredient_id"]))
        existing = cursor.fetchone()

        expiration_date = datetime.date.today() + datetime.timedelta(days=30)
        
        if existing:
            # 3. CRITICAL: Check unit consistency
            if existing["unit"] != item["unit"]:
                # If units don't match, we insert a new pantry item instead of updating the existing one.
                # This prevents incorrect quantity summing (e.g., adding 1 cup to 500g).
                pantry_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO pantry (id, user_id, ingredient_id, quantity, unit, expiration_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (pantry_id, user_id, item["ingredient_id"], item["quantity"], item["unit"], expiration_date))
                message = "Item added as a separate entry because units differed from existing stock."
            else:
                # Units match, safe to combine
                new_qty = float(existing["quantity"]) + float(item["quantity"])
                cursor.execute("UPDATE pantry SET quantity = %s, expiration_date = %s WHERE id = %s", 
                               (new_qty, expiration_date, existing["id"]))
                message = "Item purchased and combined with existing pantry stock."
        else:
            # Insert new item
            pantry_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO pantry (id, user_id, ingredient_id, quantity, unit, expiration_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (pantry_id, user_id, item["ingredient_id"], item["quantity"], item["unit"], expiration_date))
            message = "Item purchased and added to pantry."

        # 4. Delete from shopping list
        cursor.execute("DELETE FROM shopping_list WHERE id = %s", (item_id,))

        conn.commit()
        return jsonify({"message": message}), 200

    except Exception as e:
        print("MySQL Error:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/buy-new-item", methods=["POST"])
@token_required
def buy_new_item(user_id):
    """Handles buying an item not on the shopping list and adding it to the pantry, enforcing unit match."""
    data = request.json
    ingredient_name = data.get("name")
    quantity = data.get("quantity")
    unit = data.get("unit")
    exp_date_str = data.get("expiration_date")

    if not all([ingredient_name, quantity, unit]):
        return jsonify({"error": "Missing required fields (name, quantity, unit)"}), 400

    try:
        quantity = float(quantity) # Type Coercion/Validation
    except ValueError:
         return jsonify({"error": "Quantity must be a valid number."}), 400
         
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Find or create ingredient (unchanged)
        cursor.execute("SELECT id FROM ingredient WHERE name = %s", (ingredient_name,))
        ingredient_row = cursor.fetchone()
        # ... (rest of finding/creating ingredient is unchanged)
        if ingredient_row:
            ingredient_id = ingredient_row["id"]
        else:
            ingredient_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO ingredient (id, name, description) VALUES (%s, %s, %s)",
                (ingredient_id, ingredient_name, f"Automatically added ingredient: {ingredient_name}"),
            )
            conn.commit()


        # 2. Determine expiration date (unchanged)
        if exp_date_str:
            # Add basic date format validation
            try:
                expiration_date = datetime.date.fromisoformat(exp_date_str)
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
        else:
            expiration_date = datetime.date.today() + datetime.timedelta(days=30)

        # 3. Update or insert into pantry
        cursor.execute(
            "SELECT id, quantity, unit FROM pantry WHERE user_id = %s AND ingredient_id = %s",
            (user_id, ingredient_id),
        )
        existing_pantry_item = cursor.fetchone()
        
        message = ""

        if existing_pantry_item:
            # CRITICAL: Check unit consistency
            if existing_pantry_item["unit"].lower() == unit.lower():
                 # Units match, safe to combine
                new_qty = float(existing_pantry_item["quantity"]) + quantity
                cursor.execute(
                    "UPDATE pantry SET quantity = %s, expiration_date = %s WHERE id = %s",
                    (new_qty, expiration_date, existing_pantry_item["id"]),
                )
                message = f"Pantry updated: Added {quantity} {unit} of {ingredient_name}. Total: {new_qty} {unit}"
            else:
                 # Units don't match, insert as new entry
                pantry_id = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO pantry (id, user_id, ingredient_id, quantity, unit, expiration_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (pantry_id, user_id, ingredient_id, quantity, unit, expiration_date),
                )
                message = f"Pantry item added: {quantity} {unit} of {ingredient_name}. (Units were inconsistent, added separately.)"
        else:
            pantry_id = str(uuid.uuid4())
            cursor.execute(
                """
                INSERT INTO pantry (id, user_id, ingredient_id, quantity, unit, expiration_date)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (pantry_id, user_id, ingredient_id, quantity, unit, expiration_date),
            )
            message = f"Pantry item added: {quantity} {unit} of {ingredient_name}."

        conn.commit()
        return jsonify({"message": message}), 201

    except Error as e:
        # ... (rest of error handling is unchanged)
        print("MySQL Error:", e)
        traceback.print_exc()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print("General Error:", e)
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/recipe-ingredient", methods=["POST"])
@token_required
def add_recipe_ingredient(user_id):
    """Handles adding an ingredient to a specific recipe."""
    data = request.json
    recipe_id = data.get("recipe_id")
    ingredient_id = data.get("ingredient_id")
    quantity = data.get("quantity")
    unit = data.get("unit")

    if not all([recipe_id, ingredient_id, quantity, unit]):
        return jsonify({"error": "Missing required fields (recipe_id, ingredient_id, quantity, unit)"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Validation: Check if ingredient exists
        cursor.execute("SELECT id FROM ingredient WHERE id = %s", (ingredient_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Invalid ingredient_id"}), 400
        
        # Validation: Check if recipe exists AND belongs to the user
        cursor.execute("SELECT id FROM recipe WHERE id = %s AND user_id = %s", (recipe_id, user_id))
        if not cursor.fetchone():
            return jsonify({"error": "Invalid recipe_id or recipe does not belong to user"}), 403

        ri_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO recipe_ingredient (id, recipe_id, ingredient_id, quantity, unit) VALUES (%s, %s, %s, %s, %s)",
            (ri_id, recipe_id, ingredient_id, quantity, unit),
        )
        conn.commit()
        return jsonify({"message": "Ingredient added to recipe successfully"}), 201
    except Exception as e:
        print("MySQL Error:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/recipe", methods=["POST"])
@token_required
def add_recipe(user_id):
    """Adds a new recipe to the database."""
    data = request.json
    title = data.get("title")
    description = data.get("description")
    
    # user_id is passed by the token_required decorator

    if not title:
        return jsonify({"error": "Missing required field (title)"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        recipe_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO recipe (id, user_id, title, description) VALUES (%s, %s, %s, %s)",
            (recipe_id, user_id, title, description),
        )
        conn.commit()
        return jsonify({"message": "Recipe created successfully", "recipe_id": recipe_id}), 201
    except Error as e:
        print("MySQL Error:", e)
        traceback.print_exc()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print("General Error:", e)
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

# --- THE MODIFIED SHOPPING LIST GENERATION ROUTE (WITH DELETION) ---

@app.route("/generate-shopping-list", methods=["POST"])
@token_required
def generate_shopping_list(user_id):
    """
    Generates a shopping list based on missing recipe ingredients 
    AND expiring pantry items. It also automatically deletes truly expired items.
    """
    # user_id is passed by the token_required decorator
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        today = datetime.date.today()

        # 1. DELETE TRULY EXPIRED ITEMS
        cursor.execute(
            """
            DELETE FROM pantry
            WHERE user_id = %s AND expiration_date < %s
            """,
            (user_id, today)
        )
        deleted_count = cursor.rowcount
        print(f"Deleted {deleted_count} expired pantry items for user {user_id}.")

        # 2. Clear existing shopping list for the user
        cursor.execute("DELETE FROM shopping_list WHERE user_id = %s", (user_id,))
        conn.commit()

        # --- A. Check for EXPIRING Pantry Items ---
        expiration_threshold = today + datetime.timedelta(days=7)
        
        # Get ingredients that will expire soon (today or within 7 days)
        cursor.execute(
            """
            SELECT p.ingredient_id, p.quantity, p.unit, i.name AS ingredient_name
            FROM pantry p
            JOIN ingredient i ON p.ingredient_id = i.id
            WHERE p.user_id = %s AND p.expiration_date <= %s
            """,
            (user_id, expiration_threshold),
        )
        expiring_items = cursor.fetchall()
        
        shopping_list_items = {} # {ingredient_id: {qty, unit, name}}
        
        # Add expiring items to the shopping list (full replacement quantity)
        for item in expiring_items:
            if item["quantity"] > 0: 
                 shopping_list_items[item["ingredient_id"]] = {
                    "quantity": float(item["quantity"]),
                    "unit": item["unit"],
                    "name": item["ingredient_name"],
                }

        # --- B. Check for Missing Recipe Ingredients (Standard Logic) ---
        
        # Get total required ingredients for all user's recipes
        cursor.execute(
            """
            SELECT ri.ingredient_id, ri.quantity, ri.unit
            FROM recipe_ingredient ri
            JOIN recipe r ON ri.recipe_id = r.id
            WHERE r.user_id = %s
            """,
            (user_id,)
        )
        required_ingredients = cursor.fetchall()

        # Get current (clean) pantry stock
        cursor.execute(
            "SELECT ingredient_id, quantity, unit FROM pantry WHERE user_id = %s",
            (user_id,)
        )
        pantry_stock = {item["ingredient_id"]: float(item["quantity"]) for item in cursor.fetchall()}

        
        # Calculate missing quantities
        for req in required_ingredients:
            req_id = req["ingredient_id"]
            required_qty = float(req["quantity"])
            
            # If item is already marked for replacement due to being close to expiration (A), skip.
            if req_id in shopping_list_items:
                continue

            current_qty = pantry_stock.get(req_id, 0.0)
            
            missing_qty = required_qty - current_qty
            
            if missing_qty > 0:
                # Get ingredient name
                cursor.execute("SELECT name FROM ingredient WHERE id = %s", (req_id,))
                ing_name = cursor.fetchone()
                
                shopping_list_items[req_id] = {
                    "quantity": missing_qty,
                    "unit": req["unit"],
                    "name": ing_name["name"] if ing_name else "Unknown Ingredient",
                }

        # --- C. Insert final aggregated items into the shopping_list table ---
        insert_statements = []
        for ing_id, item_data in shopping_list_items.items():
            sl_id = str(uuid.uuid4())
            insert_statements.append((sl_id, user_id, ing_id, item_data["quantity"], item_data["unit"]))
        
        if insert_statements:
            cursor.executemany(
                """
                INSERT INTO shopping_list (id, user_id, ingredient_id, quantity, unit)
                VALUES (%s, %s, %s, %s, %s)
                """,
                insert_statements
            )


        conn.commit()
        
        message = f"Shopping list generated successfully. {deleted_count} expired item(s) automatically deleted from pantry."
        return jsonify({"message": message, "count": len(shopping_list_items)}), 200

    except Error as e:
        print("MySQL Error:", e)
        traceback.print_exc()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print("General Error:", e)
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/pantry/<pantry_id>", methods=["DELETE"])
@token_required
def delete_pantry_item(user_id, pantry_id):
    """Deletes a specific pantry item, ensuring it belongs to the authenticated user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM pantry WHERE id = %s AND user_id = %s",
            (pantry_id, user_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Pantry item not found or does not belong to user"}), 404
            
        return jsonify({"message": "Pantry item deleted successfully"}), 200
    except Error as e:
        print(f"Database Error: {e}")
        return jsonify({"error": "Failed to delete pantry item"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/recipe/<recipe_id>", methods=["DELETE"])
@token_required
def delete_recipe(user_id, recipe_id):
    """Deletes a recipe and its associated ingredients, ensuring it belongs to the authenticated user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if recipe belongs to the user
        cursor.execute("SELECT id FROM recipe WHERE id = %s AND user_id = %s", (recipe_id, user_id))
        if not cursor.fetchone():
            return jsonify({"error": "Recipe not found or does not belong to user"}), 404

        # 1. Delete associated recipe_ingredient entries (Cascade Delete)
        cursor.execute("DELETE FROM recipe_ingredient WHERE recipe_id = %s", (recipe_id,))
        
        # 2. Delete the recipe itself
        cursor.execute("DELETE FROM recipe WHERE id = %s", (recipe_id,))
        conn.commit()
        
        return jsonify({"message": "Recipe and all associated ingredients deleted successfully"}), 200
    except Error as e:
        print(f"Database Error: {e}")
        return jsonify({"error": "Failed to delete recipe"}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # IMPORTANT: Set debug=False in production
    app.run(debug=True)