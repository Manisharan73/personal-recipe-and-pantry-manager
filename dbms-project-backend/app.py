from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import mysql.connector
import uuid
import bcrypt
import datetime
import jwt
from mysql.connector import Error

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

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user_id = str(uuid.uuid4())

    cursor.execute("INSERT INTO users (id, username, email, password_hash, created_at) VALUES (%s, %s, %s, %s, %s)",
                   (user_id, username, email, hashed.decode('utf-8'), datetime.datetime.utcnow()))
    conn.commit()
    cursor.close()
    conn.close()

    token = jwt.encode(
        {"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)},
        app.config["SECRET_KEY"],
        algorithm="HS256"
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

    if not user or not bcrypt.checkpw(password.encode('utf-8'), user["password_hash"].encode('utf-8')):
        return jsonify({"message": "Invalid email or password"}), 401

    token = jwt.encode(
        {"user_id": user["id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)},
        app.config["SECRET_KEY"],
        algorithm="HS256"
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
        cursor.execute("""
            SELECT pantry.*, ingredient.name AS ingredient_name
            FROM pantry
            JOIN ingredient ON pantry.ingredient_id = ingredient.id
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows)
    except Error as e:
        print("MySQL Error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/pantry/<user_id>", methods=["GET"])
def get_pantry_by_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT pantry.*, ingredient.name AS name
        FROM pantry
        JOIN ingredient ON pantry.ingredient_id = ingredient.id
        WHERE pantry.user_id = %s
    """, (user_id,))
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
    cursor.execute("""
        SELECT ri.*, r.title AS recipe_title, i.name AS ingredient_name
        FROM recipe_ingredient ri
        JOIN recipe r ON ri.recipe_id = r.id
        JOIN ingredient i ON ri.ingredient_id = i.id
        WHERE r.user_id = %s
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows), 200

@app.route("/shopping-list/<user_id>", methods=["GET"])
def get_shopping_list(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT sl.*, i.name AS ingredient_name
        FROM shopping_list sl
        JOIN ingredient i ON sl.ingredient_id = i.id
        WHERE sl.user_id = %s
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows), 200

if __name__ == "__main__":
    app.run(debug=True)