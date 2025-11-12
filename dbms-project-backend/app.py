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
        SELECT pantry.id, pantry.quantity, pantry.unit, pantry.expiration_date, ingredient.name AS name
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
        SELECT sl.id, sl.quantity, sl.unit, i.name AS ingredient_name
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

@app.route("/pantry", methods=["POST"])
def add_pantry_item():
    data = request.json
    user_id = data.get("user_id")
    ingredient_id = data.get("ingredient_id")
    quantity = data.get("quantity")
    unit = data.get("unit")
    expiration_date = data.get("expiration_date")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        pantry_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO pantry (id, user_id, ingredient_id, quantity, unit, expiration_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (pantry_id, user_id, ingredient_id, quantity, unit, expiration_date),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Pantry item added successfully"}), 201
    except Exception as e:
        print("MySQL error: ", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/ingredient", methods=["POST"])
def add_ingredient():
    data = request.json
    name = data.get("name")
    description = data.get("description", None)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        ingredient_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO ingredient (id, name, description) VALUES (%s, %s, %s)",
            (ingredient_id, name, description),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Ingredient added successfully"}), 201
    except Exception as e:
        print("MySQL Error:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/recipe", methods=["POST"])
def add_recipe():
    data = request.json
    user_id = data.get("user_id")
    title = data.get("title")
    description = data.get("description", None)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        recipe_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO recipe (id, title, description, created_at, user_id) VALUES (%s, %s, %s, %s, %s)",
            (recipe_id, title, description, datetime.datetime.utcnow(), user_id),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Recipe added successfully"}), 201
    except Exception as e:
        print("MySQL Error:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/generate-shopping-list/<user_id>/<recipe_id>", methods=["POST"])
def generate_shopping_list(user_id, recipe_id):
    print("generate-shopping-list called:", user_id, recipe_id)
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT ri.ingredient_id, ri.quantity AS required_qty, ri.unit, i.name
            FROM recipe_ingredient ri
            JOIN ingredient i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = %s
            """,
            (recipe_id,),
        )
        required = cursor.fetchall()
        print("required:", required)

        cursor.execute(
            """
            SELECT id, ingredient_id, quantity AS available_qty, unit, expiration_date
            FROM pantry
            WHERE user_id = %s
            """,
            (user_id,),
        )
        pantry = cursor.fetchall()
        print("pantry raw:", pantry)

        pantry_dict = {
            item["ingredient_id"]: {
                "pantry_id": item["id"],
                "available_qty": float(item["available_qty"]) if item["available_qty"] is not None else 0,
                "expiration_date": item["expiration_date"],
                "unit": item.get("unit"),
            }
            for item in pantry
        }

        missing_items = []
        today = datetime.date.today()

        for item in required:
            pantry_item = pantry_dict.get(item["ingredient_id"])
            expired_or_missing = False
            available_qty = 0

            if pantry_item:
                exp_date = pantry_item["expiration_date"]
                exp = None
                try:
                    if exp_date is not None:
                        if isinstance(exp_date, datetime.datetime):
                            exp = exp_date.date()
                        elif isinstance(exp_date, datetime.date):
                            exp = exp_date
                        else:
                            exp = datetime.date.fromisoformat(str(exp_date).split()[0])
                except Exception:
                    exp = None

                if exp and exp <= today:
                    expired_or_missing = True
                    cursor.execute("DELETE FROM pantry WHERE id = %s", (pantry_item["pantry_id"],))
                else:
                    available_qty = pantry_item["available_qty"]
            else:
                expired_or_missing = True

            if expired_or_missing or available_qty < float(item["required_qty"]):
                required_qty = float(item["required_qty"])
                missing_qty = max(required_qty - available_qty, 0)
                
                if missing_qty > 0 or expired_or_missing:
                    if expired_or_missing and available_qty == 0:
                        missing_qty = required_qty
                    
                    missing_items.append(
                        {
                            "ingredient_id": item["ingredient_id"],
                            "ingredient_name": item["name"],
                            "quantity": missing_qty,
                            "unit": item["unit"],
                        }
                    )

        for item in missing_items:
            cursor.execute(
                "SELECT id, quantity FROM shopping_list WHERE user_id = %s AND ingredient_id = %s",
                (user_id, item["ingredient_id"]),
            )
            existing = cursor.fetchone()

            if existing:
                new_qty = float(existing["quantity"]) + float(item["quantity"])
                cursor.execute("UPDATE shopping_list SET quantity = %s WHERE id = %s", (new_qty, existing["id"]))
            else:
                shopping_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO shopping_list (id, user_id, ingredient_id, quantity, unit) VALUES (%s, %s, %s, %s, %s)",
                    (shopping_id, user_id, item["ingredient_id"], item["quantity"], item["unit"]),
                )

        conn.commit()
        cursor.close()
        conn.close()

        return (
            jsonify(
                {
                    "message": "Shopping list updated (expired items removed from pantry and added to list)",
                    "items_added": missing_items,
                }
            ),
            200,
        )
    except Exception as e:
        print("MySQL Error:", e)
        traceback.print_exc()
        return jsonify({"error": "Failed to generate shopping list. Details logged on server."}), 500


if __name__ == "__main__":
    app.run(debug=True)