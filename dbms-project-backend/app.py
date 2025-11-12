from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import mysql.connector
import uuid
import bcrypt
import datetime
import jwt
from mysql.connector import Error
import traceback

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"], supports_credentials=True)

app.config["SECRET_KEY"] = "fanime@2006"


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Fanime@2006",
        database="project"
    )

# --- USER AUTH ROUTES ---

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email=%s OR username=%s", (email, username))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"message": "User already exists"}), 400

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    user_id = str(uuid.uuid4())

    cursor.execute(
        "INSERT INTO users (id, username, email, password_hash, created_at) VALUES (%s, %s, %s, %s, %s)",
        (user_id, username, email, hashed.decode("utf-8"), datetime.datetime.utcnow()),
    )
    conn.commit()
    cursor.close()
    conn.close()

    token = jwt.encode(
        {"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)},
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )

    resp = make_response(jsonify({"message": "Signup successful"}))
    resp.set_cookie("token", token, httponly=True, samesite="Lax")
    return resp, 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        return jsonify({"message": "Invalid email or password"}), 401

    token = jwt.encode(
        {"user_id": user["id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)},
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )

    resp = make_response(jsonify({"message": "Login successful"}))
    resp.set_cookie("token", token, httponly=True, samesite="Lax")
    return resp, 200

@app.route("/verify-token", methods=["GET"])
def verify_token():
    token = request.cookies.get("token")
    if not token:
        return jsonify({"logged_in": False}), 401

    try:
        decoded = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (decoded["user_id"],))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return jsonify({"logged_in": False}), 401

        return jsonify({"logged_in": True, "username": user["username"]}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"logged_in": False, "message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"logged_in": False, "message": "Invalid Token"}), 401

# --- GET DATA ROUTES ---

@app.route("/get-pantry", methods=["GET"])
def get_pantry():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT pantry.*, ingredient.name AS ingredient_name
            FROM pantry
            JOIN ingredient ON pantry.ingredient_id = ingredient.id
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        print("MySQL Error:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/pantry/<user_id>", methods=["GET"])
def get_pantry_by_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT pantry.id, pantry.ingredient_id, pantry.quantity, pantry.unit, pantry.expiration_date, ingredient.name AS name
        FROM pantry
        JOIN ingredient ON pantry.ingredient_id = ingredient.id
        WHERE pantry.user_id = %s
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows), 200

@app.route("/ingredients", methods=["GET"])
def get_all_ingredients():
    """Fetches all ingredients from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM ingredient ORDER BY name") 
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows), 200
    except Exception as e:
        print("MySQL Error:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/recipes/<user_id>", methods=["GET"])
def get_recipes(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM recipe WHERE user_id = %s", (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows), 200

@app.route("/recipe-ingredients/<user_id>", methods=["GET"])
def get_recipe_ingredients(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
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
    cursor.close()
    conn.close()
    return jsonify(rows), 200

@app.route("/shopping-list/<user_id>", methods=["GET"])
def get_shopping_list(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
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
    cursor.close()
    conn.close()
    return jsonify(rows), 200

# --- POST/UPDATE ROUTES (abbreviated for length, focusing on new/modified) ---

# ... (add_pantry_item, add_ingredient, add_recipe, generate_shopping_list remain the same) ...

@app.route("/buy-item/<user_id>/<item_id>", methods=["POST"])
def buy_item(user_id, item_id):
    # This remains the same, handles shopping list checkout
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT ingredient_id, quantity, unit
            FROM shopping_list
            WHERE id = %s AND user_id = %s
        """, (item_id, user_id))
        item = cursor.fetchone()

        if not item:
            cursor.close()
            conn.close()
            return jsonify({"error": "Item not found in shopping list"}), 404

        cursor.execute("""
            SELECT id, quantity FROM pantry WHERE user_id = %s AND ingredient_id = %s
        """, (user_id, item["ingredient_id"]))
        existing = cursor.fetchone()

        expiration_date = datetime.date.today() + datetime.timedelta(days=30)
        
        if existing:
            new_qty = float(existing["quantity"]) + float(item["quantity"])
            cursor.execute("UPDATE pantry SET quantity = %s, expiration_date = %s WHERE id = %s", (new_qty, expiration_date, existing["id"]))
        else:
            pantry_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO pantry (id, user_id, ingredient_id, quantity, unit, expiration_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (pantry_id, user_id, item["ingredient_id"], item["quantity"], item["unit"], expiration_date))

        cursor.execute("DELETE FROM shopping_list WHERE id = %s", (item_id,))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Item purchased and added to pantry"}), 200

    except Exception as e:
        print("MySQL Error:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/buy-new-item", methods=["POST"])
def buy_new_item():
    # This remains the same, handles buying new items (new to pantry or new to DB)
    data = request.json
    user_id = data.get("user_id")
    ingredient_name = data.get("name")
    quantity = data.get("quantity")
    unit = data.get("unit")
    exp_date_str = data.get("expiration_date")

    if not all([user_id, ingredient_name, quantity, unit]):
        return jsonify({"error": "Missing required fields (user_id, name, quantity, unit)"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM ingredient WHERE name = %s", (ingredient_name,))
        ingredient_row = cursor.fetchone()
        ingredient_id = None

        if ingredient_row:
            ingredient_id = ingredient_row["id"]
        else:
            ingredient_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO ingredient (id, name, description) VALUES (%s, %s, %s)",
                (ingredient_id, ingredient_name, f"Automatically added ingredient: {ingredient_name}"),
            )
            print(f"New ingredient created: {ingredient_name} with ID {ingredient_id}")
            conn.commit()

        if exp_date_str:
            expiration_date = datetime.date.fromisoformat(exp_date_str)
        else:
            expiration_date = datetime.date.today() + datetime.timedelta(days=30)

        cursor.execute(
            "SELECT id, quantity FROM pantry WHERE user_id = %s AND ingredient_id = %s",
            (user_id, ingredient_id),
        )
        existing_pantry_item = cursor.fetchone()

        if existing_pantry_item:
            new_qty = float(existing_pantry_item["quantity"]) + float(quantity)
            cursor.execute(
                "UPDATE pantry SET quantity = %s, expiration_date = %s WHERE id = %s",
                (new_qty, expiration_date, existing_pantry_item["id"]),
            )
            message = f"Pantry updated: Added {quantity} {unit} of {ingredient_name}. Total: {new_qty} {unit}"
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
        cursor.close()
        conn.close()
        return jsonify({"message": message}), 201

    except Error as e:
        print("MySQL Error:", e)
        traceback.print_exc()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print("General Error:", e)
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/recipe-ingredient", methods=["POST"])
def add_recipe_ingredient():
    # This remains the same, handles adding ingredient to a recipe
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

        cursor.execute("SELECT id FROM ingredient WHERE id = %s", (ingredient_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid ingredient_id"}), 400
        
        cursor.execute("SELECT id FROM recipe WHERE id = %s", (recipe_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid recipe_id"}), 400

        ri_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO recipe_ingredient (id, recipe_id, ingredient_id, quantity, unit) VALUES (%s, %s, %s, %s, %s)",
            (ri_id, recipe_id, ingredient_id, quantity, unit),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Ingredient added to recipe successfully"}), 201
    except Exception as e:
        print("MySQL Error:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/recipe", methods=["POST"])
def add_recipe():
    """Adds a new recipe to the database."""
    data = request.json
    user_id = data.get("user_id")
    title = data.get("title")
    description = data.get("description")
    
    if not all([user_id, title]):
        return jsonify({"error": "Missing required fields (user_id, title)"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        recipe_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO recipe (id, user_id, title, description) VALUES (%s, %s, %s, %s)",
            (recipe_id, user_id, title, description),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Recipe created successfully", "recipe_id": recipe_id}), 201
    except Error as e:
        print("MySQL Error:", e)
        traceback.print_exc()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print("General Error:", e)
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)