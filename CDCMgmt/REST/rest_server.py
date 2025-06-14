# RESTserver/server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import bcrypt

app = Flask(__name__)
CORS(app)

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


# Use absolute path to avoid path issues
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PERSISTENCE_FILE = os.path.join(BASE_DIR, 'data', 'zones_data.json')

# Load data from file
def load_data():
    if not os.path.exists(PERSISTENCE_FILE):
        return {"active_zones": {}, "inactive_zones": {}}
    with open(PERSISTENCE_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"active_zones": {}, "inactive_zones": {}}

# Save data to file
def save_data(data):
    os.makedirs(os.path.dirname(PERSISTENCE_FILE), exist_ok=True)
    with open(PERSISTENCE_FILE, 'w') as f:
        json.dump(data, f, indent=4)
# save data to zonegroup_data.json
def load_zonegroup():
    try:
        with open("data/zonegroup_data.json", "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"zone_groups": {}}
def save_zonegroup(zonegroup_data):
    with open("data/zonegroup_data.json", "w") as file:
        json.dump(zonegroup_data, file, indent=4)

#alias data
def load_alias_data():
    try:
        with open("data/alias_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"member_aliases": {}, "free_aliases": {}}

# Save data to file
def save_alias_data(alias_data):
    with open("data/alias_data.json", "w") as file:
        json.dump(alias_data, file, indent=4)

# Load on startup
data = load_data()

# Endpoint to fetch NVMe nodes
# @app.route("/cdc/api/v1/nvmenodes", methods=["GET"])
# def get_nvmenodes():
#     return jsonify(data['nvmenodes'])

# Endpoint to create Zone Group
@app.route("/cdc/api/v1/zgrp/<zgrp_name>", methods=["POST"])
def create_zgrp(zgrp_name):
    data = load_zonegroup()
    if any(g["name"] == zgrp_name for g in data["zone_groups"].values()):
        return jsonify({"error": f"Zone Group '{zgrp_name}' already exists"}), 400

    new_id = str(max([int(i) for i in data["zone_groups"].keys()] + [0]) + 1)
    data["zone_groups"][new_id] = {
        "name": zgrp_name,
        "zones": [],
        "active": False
    }
    save_zonegroup(data)
    return jsonify({"message": f"Zone Group '{zgrp_name}' created successfully"}), 201


@app.route("/cdc/api/v1/zgrp/<zgrp_name>", methods=["DELETE"])
def delete_zgrp(zgrp_name):
    data = load_zonegroup()
    group_id_to_delete = None
    for gid, group in data["zone_groups"].items():
        if group["name"] == zgrp_name:
            group_id_to_delete = gid
            break
    if group_id_to_delete:
        del data["zone_groups"][group_id_to_delete]
        save_zonegroup(data)
        return jsonify({"message": f"Zone Group '{zgrp_name}' deleted successfully"}), 200
    return jsonify({"error": f"Zone Group '{zgrp_name}' not found"}), 404

# Endpoint to create Zone
@app.route("/cdc/api/v1/zones", methods=["GET"])
def get_zones():
    return jsonify({
        "active_zones": data.get("active_zones", {}),
        "inactive_zones": data.get("inactive_zones", {})
    }), 200


@app.route("/cdc/api/v1/zone/<zone_name>", methods=["POST"])
def create_zone(zone_name):
    try:
        all_zone_names = [z["name"] for z in data["active_zones"].values()] + \
                         [z["name"] for z in data["inactive_zones"].values()]
        if zone_name in all_zone_names:
            return jsonify({"error": f"Zone '{zone_name}' already exists"}), 400

        all_ids = list(data["active_zones"].keys()) + list(data["inactive_zones"].keys())
        next_id = str(max([int(i) for i in all_ids] + [0]) + 1)

        data["inactive_zones"][next_id] = {"name": zone_name, "aliases": {}}
        save_data(data)
        return jsonify({"message": f"Zone '{zone_name}' created successfully"}), 201
    except Exception:
        return jsonify({"error": "Internal server error"}), 500

@app.route("/cdc/api/v1/zone/<zone_name>", methods=["DELETE"])
def delete_zone(zone_name):
    try:
        for zone_dict in [data["active_zones"], data["inactive_zones"]]:
            for zone_id, zone in list(zone_dict.items()):
                if zone["name"] == zone_name:
                    del zone_dict[zone_id]
                    save_data(data)
                    return jsonify({"message": f"Zone '{zone_name}' deleted successfully"}), 200
        return jsonify({"error": f"Zone '{zone_name}' not found"}), 404
    except Exception:
        return jsonify({"error": "Internal server error"}), 500

@app.route("/cdc/api/v1/aliases", methods=["GET"])
def get_aliases():
    data = load_alias_data()
    return jsonify(data), 200

# ✅ POST: Create a new alias
@app.route("/cdc/api/v1/alias/<alias_name>", methods=["POST"])
def create_alias(alias_name):
    data = load_alias_data()

    if alias_name in [a["name"] for a in data["free_aliases"].values()] + [a["name"] for a in data["member_aliases"].values()]:
        return jsonify({"error": f"Alias '{alias_name}' already exists"}), 400

    new_id = str(max([int(i) for i in data["free_aliases"].keys() + data["member_aliases"].keys()] + [0]) + 1)
    alias_obj = {
        "name": alias_name,
        "type": request.json.get("type", "Host-Port"),
        "ip": request.json.get("ip", ""),
        "nqn": request.json.get("nqn", "")
    }
    data["free_aliases"][new_id] = alias_obj
    save_alias_data(data)
    return jsonify({"message": f"Alias '{alias_name}' created"}), 201

# ✅ DELETE: Remove alias
@app.route("/cdc/api/v1/alias/<alias_name>", methods=["DELETE"])
def delete_alias(alias_name):
    data = load_alias_data()
    for section in ["free_aliases", "member_aliases"]:
        for alias_id, alias_obj in list(data[section].items()):
            if alias_obj["name"] == alias_name:
                del data[section][alias_id]
                save_alias_data(data)
                return jsonify({"message": f"Alias '{alias_name}' deleted"}), 200
    return jsonify({"error": f"Alias '{alias_name}' not found"}), 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
