from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/authentication_service_db"
app.config["JWT_SECRET_KEY"] = "secret_key_for_jwt_token"

mongo = PyMongo(app)
jwt = JWTManager(app)


class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password


def get_user(username):
    user = mongo.db.users.find_one({"username": username})
    if user:
        return User(username=user["username"], password=user["password"])
    return None


@app.route("/register", methods=["POST"])
def register():
    username = request.json.get("username")
    password = request.json.get("password")
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400
    if mongo.db.users.find_one({"username": username}):
        return jsonify({"msg": "Username already taken"}), 400
    mongo.db.users.insert_one({"username": username, "password": generate_password_hash(password)})
    return jsonify({"msg": "User created successfully"}), 201


@app.route("/login", methods=["POST"])
def login():
    username = request.json.get("username")
    password = request.json.get("password")
    user = get_user(username)
    if not user or not check_password_hash(user.password, password):
        return jsonify({"msg": "Invalid username or password"}), 401
    access_token = create_access_token(identity=user.username)
    return jsonify({"access_token": access_token}), 200


@app.route("/logout", methods=["POST"])
def logout():
    return "Logout successful", 200


@app.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    # Get the username from the JWT identity
    username = get_jwt_identity()
    # Retrieve the user document from the database
    user = mongo.db.users.find_one({"username": username})
    # Remove the password field from the user document
    del user["password"]

    user["_id"] = str(user["_id"])

    print(user)

    # Return the user document as JSON response
    return jsonify(user), 200


@app.route("/status")
def status():
    return "Authentication Service is running"


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"msg": "Not found"}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
