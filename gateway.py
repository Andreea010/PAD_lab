import threading

from flask import Flask, jsonify, request, abort
import requests
import random
import time

app = Flask(__name__)

# Service registry
auth_services = ["http://localhost:5001", "http://localhost:5001"]
ticket_services = ["http://localhost:5002", "http://localhost:5002"]


# Service discovery
def check_services():
    while True:
        for service in auth_services:
            try:
                requests.get(service + "/status")
            except requests.exceptions.RequestException:
                auth_services.remove(service)
        for service in ticket_services:
            try:
                requests.get(service + "/status")
            except requests.exceptions.RequestException:
                ticket_services.remove(service)
        time.sleep(60)


# High availability
def get_auth_service():
    if not auth_services:
        abort(503)
    while True:
        service = round_robin(auth_services)  # random.choice(auth_services)
        try:
            response = requests.get(service + "/status")
            if response.ok:
                return service
        except requests.exceptions.RequestException:
            auth_services.remove(service)


def get_ticket_service():
    if not ticket_services:
        abort(503)
    while True:
        service = round_robin(ticket_services)  # random.choice(ticket_services)
        try:
            response = requests.get(service + "/status")
            if response.ok:
                return service
        except requests.exceptions.RequestException:
            ticket_services.remove(service)


# Load balancing
def round_robin(services):
    services.append(services.pop(0))
    return services[0]


@app.route("/")
def home():
    return "Gateway Service"


@app.route("/login", methods=["POST"])
def login():
    service = get_auth_service()
    url = service + "/login"
    response = requests.post(url, json=request.get_json())
    return response.content, response.status_code, response.headers.items()


@app.route("/register", methods=["POST"])
def register():
    service = get_auth_service()
    url = service + "/register"
    response = requests.post(url, json=request.get_json(), headers=request.headers)
    return response.content, response.status_code, response.headers.items()


@app.route("/logout", methods=["POST"])
def logout():
    service = get_auth_service()
    url = service + "/logout"
    response = requests.post(url, headers=request.headers)
    return response.content, response.status_code, response.headers.items()


@app.route("/profile", methods=["GET"])
def profile():
    service = get_auth_service()
    url = service + "/profile"
    response = requests.get(url, headers=request.headers)
    return response.content, response.status_code, response.headers.items()


@app.route("/tickets", methods=["GET"])
def list_tickets():
    service = get_ticket_service()
    url = service + "/tickets"
    response = requests.get(url, headers=request.headers)
    return response.content, response.status_code, response.headers.items()


@app.route("/tickets/<string:id>", methods=["GET"])
def get_ticket(id):
    service = get_ticket_service()
    url = service + "/tickets/{}".format(id)
    response = requests.get(url, headers=request.headers)
    return response.content, response.status_code, response.headers.items()


@app.route("/buy", methods=["POST"])
def buy_ticket():
    service = get_ticket_service()
    url = service + "/buy"
    response = requests.post(url, json=request.get_json(), headers=request.headers)
    return response.content, response.status_code, response.headers.items()


if __name__ == "__main__":
    # Start service discovery thread
    discovery_thread = threading.Thread(target=check_services)
    discovery_thread.start()

    # Start Flask app
    app.run(host='0.0.0.0', port=5000)
