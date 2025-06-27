import streamlit as st
from typing import Dict, Tuple
import json
import os

# Set wide layout
st.set_page_config(layout="wide")

def transform_zone_data(json_data: Dict) -> Tuple[Dict, Dict]:
    """
    Transform zone configuration data into D3.js compatible format.

    Args:
        json_data: JSON object containing zone configuration

    Returns:
        Tuple[Dict, Dict]: A tuple containing (active_tree, inactive_tree)
    """
    try:
        # Transform active zones
        active_tree = {
            "name": json_data["active"]["ZoneGrpName"],
            "id": json_data["active"]["ZoneGrpId"],
            "type": "root",
            "status": "active",
            "children": []
        }

        for zone in json_data["active"]["ZoneMembers"]:
            zone_node = {
                "name": zone["ZoneName"],
                "id": zone["ZoneId"],
                "type": "zone",
                "status": "active",
                "children": []
            }

            for alias in zone["AliasMembers"]:
                alias_node = {
                    "name": alias["AliasName"],
                    "id": alias["AliasId"],
                    "type": "alias",
                    "status": "active"
                }
                zone_node["children"].append(alias_node)

            active_tree["children"].append(zone_node)

        # Transform inactive zones
        inactive_tree = {
            "name": json_data["inactive"]["ZoneGrpName"],  # Updated
            "id": json_data["inactive"]["ZoneGrpId"],      # Updated
            "type": "root",
            "status": "inactive",
            "children": []
        }

        for zone in json_data["inactive"]["ZoneMembers"]:  # Fixed loop
            zone_node = {
                "name": zone["ZoneName"],
                "id": zone["ZoneId"],
                "type": "zone",
                "status": "inactive",
                "children": []
            }

            for alias in zone["AliasMembers"]:
                alias_node = {
                    "name": alias["AliasName"],
                    "id": alias["AliasId"],
                    "type": "alias",
                    "status": "inactive"
                }
                zone_node["children"].append(alias_node)

            inactive_tree["children"].append(zone_node)

        return active_tree, inactive_tree

    except KeyError as e:
        raise Exception(f"Invalid JSON structure. Missing key: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing JSON data: {str(e)}")


def transform_zone_data1(json_data: Dict) -> Tuple[Dict, Dict]:
    """
    Transform zone configuration data into D3.js compatible format.
    
    Args:
        json_data: JSON object containing zone configuration
        
    Returns:
        Tuple[Dict, Dict]: A tuple containing (active_tree, inactive_tree)
    """
    try:
        # Transform active zones
        active_tree = {
            "name": json_data["active"]["ZoneGrpName"],
            "id": json_data["active"]["ZoneGrpId"],
            "type": "root",
            "status": "active",
            "children": []
        }
        
        # Add active zones
        for zone in json_data["active"]["ZoneMembers"]:
            zone_node = {
                "name": zone["ZoneName"],
                "id": zone["ZoneId"],
                "type": "zone",
                "status": "active",
                "children": []
            }
            
            # Add aliases for the zone
            for alias in zone["AliasMembers"]:
                alias_node = {
                    "name": alias["AliasName"],
                    "id": alias["AliasId"],
                    "type": "alias",
                    "status": "active"
                }
                zone_node["children"].append(alias_node)
                
            active_tree["children"].append(zone_node)
        
        # Transform inactive zones
        inactive_tree = {
            "name": "Inactive Zones",
            "type": "root",
            "status": "inactive",
            "children": []
        }
        
        # Add inactive zones
        for zone in json_data["inactive"]:
            zone_node = {
                "name": zone["ZoneName"],
                "id": zone["ZoneId"],
                "type": "zone",
                "status": "inactive",
                "children": []
            }
            
            # Add aliases for the zone
            for alias in zone["AliasMembers"]:
                alias_node = {
                    "name": alias["AliasName"],
                    "id": alias["AliasId"],
                    "type": "alias",
                    "status": "inactive"
                }
                zone_node["children"].append(alias_node)
                
            inactive_tree["children"].append(zone_node)
        
        return active_tree, inactive_tree
        
    except KeyError as e:
        raise Exception(f"Invalid JSON structure. Missing key: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing JSON data: {str(e)}")
    

def read_file_content(filename):
    """Read content of a file from the static directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'static', filename)
    with open(file_path, 'r') as file:
        return file.read()

def load_zone_config():
    """Load the zone configuration from the default JSON file."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, 'data/zone_config.json')
        
        with open(config_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise Exception("zone_config.json file not found in the application directory")
    except json.JSONDecodeError:
        raise Exception("Invalid JSON format in zone_config.json")
    except Exception as e:
        raise Exception(f"Error reading zone_config.json: {str(e)}")

def render_zone_config(json_data):
    st.title("Zone Configuration Visualization")
    
    try:
        # Transform the JSON data
        active_tree, inactive_tree = transform_zone_data(json_data)
        
        # Read static files
        css_content = read_file_content('style.css')
        js_content = read_file_content('tree.js')
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                {css_content}
                .tree-container {{
                    margin-bottom: 50px;
                    border: 1px solid #ccc;
                    padding: 20px;
                    border-radius: 5px;
                    overflow: auto;
                }}
                .tree-title {{
                    font-size: 20px;
                    font-weight: bold;
                    margin-bottom: 20px;
                    color: #333;
                }}
                svg {{
                    display: block;
                    width: 100%;
                    height: 600px;
                    background: #fff;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="tree-container">
                    <div class="tree-title">Active Zones(Scroll down for Inactive zones)</div>
                    <svg id="active-tree-svg"></svg>
                </div>
                
                <div class="tree-container">
                    <div class="tree-title">Inactive Zones</div>
                    <svg id="inactive-tree-svg"></svg>
                </div>
            </div>

            <script>{js_content}</script>
            <script>
                console.log('Starting tree initialization');
                console.log('Active tree data:', {json.dumps(active_tree)});
                console.log('Inactive tree data:', {json.dumps(inactive_tree)});
                
                // Create separate tree instances
                const activeTree = new TreeChart('#active-tree-svg', {json.dumps(active_tree)}, 1200, 600);
                const inactiveTree = new TreeChart('#inactive-tree-svg', {json.dumps(inactive_tree)}, 1200, 600);
            </script>
        </body>
        </html>
        """
        
        # Render the HTML content with increased height
        st.components.v1.html(html_content, height=1400, scrolling=True)
        
    except Exception as e:
        st.error(f"Error: {str(e)}")

def fetch_zonecfg_and_render():
    zonedata_json = load_zone_config()
    #st.write(zonedata_json)
    render_zone_config(zonedata_json)
    
if __name__ == "__main__":
    fetch_zonecfg_and_render()
