from bson import ObjectId
from flask import Flask, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required, JWTManager
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/ticket_service_db"
app.config["JWT_SECRET_KEY"] = "secret_key_for_jwt_token"

jwt = JWTManager(app)

mongo = PyMongo(app)


@app.route("/tickets", methods=["GET"])
def get_tickets():
    tickets = []
    for ticket in mongo.db.tickets.find():
        ticket["_id"] = str(ticket["_id"])
        tickets.append(ticket)
    return jsonify(tickets), 200


@app.route("/tickets/<string:id>", methods=["GET"])
def get_ticket(id):
    ticket = mongo.db.tickets.find_one({"_id": ObjectId(str(id))})
    if ticket:
        return jsonify({
            "id": str(ticket["_id"]),
            "name": ticket["name"],
            "price": ticket["price"]
        }), 200
    else:
        return "Ticket not found", 404


@app.route("/buy", methods=["POST"])
@jwt_required()
def buy_ticket():
    # Get the user_id from the JWT identity
    user_id = get_jwt_identity()
    ticket_id = request.json.get("ticket_id")
    if not ticket_id:
        return jsonify({"msg": "Missing ticket_id"}), 400
    ticket = mongo.db.tickets.find_one({"_id": ObjectId(ticket_id)})
    if not ticket:
        return jsonify({"msg": "Ticket not found"}), 404
    if ticket["status"] != "available":
        return jsonify({"msg": "Ticket not available"}), 409
    mongo.db.tickets.update_one({"_id": ticket["_id"]}, {"$set": {"status": "sold", "user_id": user_id}})
    return jsonify({"msg": "Ticket bought successfully"}), 200


@app.route("/status")
def status():
    return "Ticket Service is running"


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"msg": "Not found"}), 404


tickets = [
{"name": "Train Ticket 1", "price": 10.0, "status": "available"},
{"name": "Train Ticket 2", "price": 20.0, "status": "available"},
{"name": "Train Ticket 3", "price": 30.0, "status": "available"}
]

mongo.db.tickets.insert_many(tickets)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
