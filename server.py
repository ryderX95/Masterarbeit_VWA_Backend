from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text  # Allows executing raw SQL queries

app = Flask(__name__)
CORS(app)

# 🛠️ Secret Key for JWT
app.config["JWT_SECRET_KEY"] = "supersecret"  # 🔴 Weak key, vulnerable!
jwt = JWTManager(app)

# 🛠️ Database Config
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://vuln_user:vuln_password@localhost/vulnerable_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# 🛠️ User Model (Still No Hashing for Vulnerability)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

# 🛠️ Vulnerable Registration Endpoint
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    new_user = User(username=data["username"], password=data["password"])  # No password hashing!
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered"}), 201

# 🛠️ **Vulnerable Login with SQL Injection**
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data["username"]
    password = data["password"]

    query = text("SELECT id, username FROM \"user\" WHERE username = :username AND password = :password")
    user = db.session.execute(query, {"username": username, "password": password}).fetchone()

    if user:
        user_id, user_name = user  # Unpack user tuple
        access_token = create_access_token(identity=user_name)
        return jsonify({
            "message": "Logged in successfully",
            "token": access_token,
            "user": {"id": user_id, "username": user_name}
        }), 200

    # **Username Enumeration via Verbose Error**
    check_user = db.session.execute(text("SELECT username FROM \"user\" WHERE username = :username"), {"username": username}).fetchone()
    if check_user:
        return jsonify({"error": "Invalid password"}), 401  # ✅ This leaks that the username exists!
    
    return jsonify({"error": "Username does not exist"}), 401  # ✅ This leaks username is invalid!

# 🛠️ **Forgot Password Feature (Username Enumeration)**
@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    username = data.get("username", "")

    query = text("SELECT username FROM \"user\" WHERE username = :username")
    user = db.session.execute(query, {"username": username}).fetchone()

    if user:
        return jsonify({"message": "User exists in database!"}), 200
    else:
        return jsonify({"error": "Username not found!"}), 404


# 🛠️ **Protected Dashboard Route (Requires Token)**
@app.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    current_user = get_jwt_identity()
    return jsonify({"message": "Welcome to the dashboard!", "user": current_user})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
