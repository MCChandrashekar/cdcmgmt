from flask import Flask, request, jsonify
from Simulator import create_zone, delete_zone, get_all_zones, get_zone

app = Flask(__name__)

@app.route('/zone', methods=['POST'])
def zone_create():
    data = request.json
    
    # Validate request
    if not data:
        return jsonify({"error": "Missing request body"}), 400
    
    command = data.get('command')
    zone_name = data.get('zone_name')
    
    # Validate command type
    if not command or command != "CREATE":
        return jsonify({"error": "Invalid or missing command. Expected 'CREATE'"}), 400
    
    # Validate zone name
    if not zone_name:
        return jsonify({"error": "Missing zone_name parameter"}), 400
    
    # Forward the command to simulator
    try:
        result = create_zone(zone_name)
        return jsonify({"message": f"Zone '{zone_name}' created successfully", "zone": result}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create zone: {str(e)}"}), 500

@app.route('/zone/<zone_name>', methods=['DELETE'])
def zone_delete(zone_name):
    if not zone_name:
        return jsonify({"error": "Missing zone_name parameter"}), 400
    
    # Forward the command to simulator
    try:
        result = delete_zone(zone_name)
        return jsonify({"message": f"Zone '{zone_name}' deleted successfully", "result": result}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to delete zone: {str(e)}"}), 500

@app.route('/zones', methods=['GET'])
def zones_list():
    try:
        zones = get_all_zones()
        return jsonify({"zones": zones}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve zones: {str(e)}"}), 500

@app.route('/zone/<zone_name>', methods=['GET'])
def zone_get(zone_name):
    if not zone_name:
        return jsonify({"error": "Missing zone_name parameter"}), 400
    
    try:
        zone = get_zone(zone_name)
        if zone:
            return jsonify({"zone": zone}), 200
        else:
            return jsonify({"error": f"Zone '{zone_name}' not found"}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve zone: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

