from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import mysql.connector
import uuid
import bcrypt
import datetime
import jwt

app = Flask(__name__)
app.config["SECRET_KEY"] = "fanime@2006"

CORS(app, origins=["http://localhost:5173"], supports_credentials=True)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Fanime@2006",
    database="project"
)
cursor = db.cursor(dictionary=True)

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    cursor.execute("SELECT * FROM users WHERE email=%s OR username=%s", (email, username))
    if cursor.fetchone():
        return jsonify({"message": "User already exists"}), 400

    user_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO users (id, username, email, password_hash) VALUES (%s, %s, %s, %s)",
        (user_id, username, email, hashed)
    )
    db.commit()

    token = jwt.encode(
        {"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)},
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    resp = make_response(jsonify({"message": "Signup successful"}))
    resp.set_cookie("token", token, httponly=True, samesite="Lax", secure=False, path="/")
    return resp, 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    if not user or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return jsonify({"message": "Invalid email or password"}), 401

    token = jwt.encode(
        {"user_id": user["id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)},
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    resp = make_response(jsonify({"message": "Login successful"}))
    resp.set_cookie("token", token, httponly=True, samesite="Lax", secure=False, path="/")
    return resp, 200

@app.route("/verify-token", methods=["GET"])
def verify_token():
    token = request.cookies.get("token")
    if not token:
        return jsonify({"logged_in": False, "reason": "No token"}), 401

    try:
        decoded = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        cursor.execute("SELECT * FROM users WHERE id=%s", (decoded["user_id"],))
        user = cursor.fetchone()
        if not user:
            return jsonify({"logged_in": False}), 401

        return jsonify({"logged_in": True, "username": user["username"]}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"logged_in": False, "message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"logged_in": False, "message": "Invalid Token"}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)