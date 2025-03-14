from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text  # Import text for raw SQL execution
import os

app = Flask(__name__)
CORS(app)

# 🔴 **Insecure Database Configuration**
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://vuln_user:vuln_password@localhost/vulnerable_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "supersecret"  # 🔴 Weak JWT key
app.config["SECRET_KEY"] = "very_secret_key"  # ✅ Fix session error


db = SQLAlchemy(app)
jwt = JWTManager(app)

# 🔴 **Vulnerable User Model (No Password Hashing!)**
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  # Stored in plain text! 🔴

# ✅ Ensure tables exist
with app.app_context():
    db.create_all()

# 🔴 **Vulnerable Registration (No Input Validation)**
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    new_user = User(username=data["username"], password=data["password"])  # No password hashing! 🔴
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered"}), 201

# 🔴 **Vulnerable Login with SQL Injection**
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    # 🚨 **Vulnerable SQL Execution with Injection**
    query = text(f"SELECT * FROM \"user\" WHERE username = '{username}' AND password = '{password}'")

    try:
        users = db.session.execute(query).fetchall()  # Fetch ALL matching users
        if users:
            first_user = users[0]  # Take the first user in case of multiple
            return jsonify({
                "message": "Logged in successfully",
                "user": {"id": first_user[0], "username": first_user[1]}
            })
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# 🔴 **Vulnerable Route to Fetch All Users (No Authentication)**
@app.route('/users', methods=['GET'])
def get_users():
    query = text('SELECT id, username, password FROM "user";')  # 🔴 Exposes all users
    users = db.session.execute(query).fetchall()

    # ✅ Convert rows to dictionary properly
    user_list = [{"id": row[0], "username": row[1], "password": row[2]} for row in users]

    return jsonify(user_list)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # Debug Mode 🔴
