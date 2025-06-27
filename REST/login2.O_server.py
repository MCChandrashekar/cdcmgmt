# RESTserver/login_server.py
from flask import Flask, request, jsonify
import json
import bcrypt

app = Flask(__name__)

with open("data/login_credentials.json", "r") as f:
    credentials = json.load(f)

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username in credentials:
        hashed_pw = credentials[username].encode()
        if bcrypt.checkpw(password.encode(), hashed_pw):
            return jsonify({"success": True, "message": "Login successful"}), 200

    return jsonify({"success": False, "message": "Invalid credentials"}), 401

if __name__ == "__main__":
    app.run(port=5002, debug=True)
