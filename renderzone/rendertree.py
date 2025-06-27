#renderzone/rendertree.py
import streamlit as st
from typing import Dict, Tuple
import json
import os
from pathlib import Path

# def transform_zone_data
def transform_zone_data(json_data: Dict) -> Tuple[Dict, Dict]:
    try:
        # 🔁 Build a dummy root for all active groups
        active_tree = {
            "name": "All Active Groups",
            "id": -1,
            "type": "root",
            "status": "active",
            "children": [],
        }

        for group in json_data["active"]:
            group_node = {
                "name": group["ZoneGrpName"],
                "id": group["ZoneGrpId"],
                "type": "group",
                "status": "active",
                "children": [],
            }

            for zone in group["ZoneMembers"]:
                zone_node = {
                    "name": zone["ZoneName"],
                    "id": zone["ZoneId"],
                    "type": "zone",
                    "status": "active",
                    "children": [],
                }

                for alias in zone["AliasMembers"]:
                    alias_node = {
                        "name": alias["AliasName"],
                        "id": alias["AliasId"],
                        "type": "alias",
                        "status": "active",
                        "ip": alias.get("IPAddress", "N/A"),
                        "nqn": alias.get("NQN", "N/A"),
                    }
                    zone_node["children"].append(alias_node)

                group_node["children"].append(zone_node)

            active_tree["children"].append(group_node)

        # 👇 Same as before for inactive
        first_inactive_group = json_data["inactive"][0]
        inactive_tree = {
            "name": first_inactive_group["ZoneGrpName"],
            "id": first_inactive_group["ZoneGrpId"],
            "type": "root",
            "status": "inactive",
            "children": [],
        }

        for zone in first_inactive_group["ZoneMembers"]:
            zone_node = {
                "name": zone["ZoneName"],
                "id": zone["ZoneId"],
                "type": "zone",
                "status": "inactive",
                "children": [],
            }

            for alias in zone["AliasMembers"]:
                alias_node = {
                    "name": alias["AliasName"],
                    "id": alias["AliasId"],
                    "type": "alias",
                    "status": "inactive",
                    "ip": alias.get("IPAddress", "N/A"),
                    "nqn": alias.get("NQN", "N/A"),
                }
                zone_node["children"].append(alias_node)

            inactive_tree["children"].append(zone_node)

        return active_tree, inactive_tree

    except KeyError as e:
        raise Exception(f"Invalid JSON structure. Missing key: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing JSON data: {str(e)}")



def read_file_content(filename: str) -> str:
    """Read content of a file from the Static directory."""
    current_dir = Path(__file__).parent.parent
    print(f"Current directory: {current_dir}")
    file_path = os.path.join(current_dir, "renderzone", "Static", filename)
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"{filename} not found in Static directory at {file_path}"
        )
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def load_zone_config() -> Dict:
    """Load the zone configuration from the JSON file inside RenderZones/data/."""
    try:
        config_path = "../CDCMgmt/data/zone_config.json"

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"zone_config.json file not found at {config_path}")

        with open(config_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        raise Exception("Invalid JSON format in zone_config.json")
    except Exception as e:
        raise Exception(f"Error reading zone_config.json: {str(e)}")


def render_zone_config(json_data: Dict):
    st.title("Zone Configuration Visualization")

    try:
        # Transform the JSON data
        active_tree, inactive_tree = transform_zone_data(json_data)

        # Read static files for CSS and JS
        css_content = read_file_content("style.css")
        js_content = read_file_content("tree.js")

        # HTML content with proper subheadings and containers
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
                    background: #fff;
                }}
                .tree-title {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 15px;
                    color: #222;
                }}
                svg {{
                    display: block;
                    width: 100%;
                    height: 600px;
                    background: #fafafa;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
                                  Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
                    margin: 0;
                    padding: 10px 20px;
                    background-color: #f8f9fa;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="tree-container" id="active-tree-container">
                    <div class="tree-title">Active Zones</div>
                    <svg id="active-tree-svg"></svg>
                </div>

                <div class="tree-container" id="inactive-tree-container">
                    <div class="tree-title">Inactive Zones</div>
                    <svg id="inactive-tree-svg"></svg>
                </div>
            </div>

            <script>{js_content}</script>
            <script>
                const activeTree = new TreeChart('#active-tree-svg', {json.dumps(active_tree)}, 1200, 600);
                const inactiveTree = new TreeChart('#inactive-tree-svg', {json.dumps(inactive_tree)}, 1200, 600);
            </script>
        </body>
        </html>
        """

        # Render the HTML with enough height for scroll
        st.components.v1.html(html_content, height=1400, scrolling=True)

    except Exception as e:
        st.error(f"Error: {str(e)}")


def fetch_zonecfg_and_render():
    zonedata_json = load_zone_config()
    # st.write(zonedata_json)
    render_zone_config(zonedata_json)


def main():
    fetch_zonecfg_and_render()


# Optional: Call main if running directly
if __name__ == "__main__":
    main()

#---OLD CODE---#
# #renderzone/rendertree.py
# import streamlit as st
# from typing import Dict, Tuple
# import json
# import os
# from pathlib import Path

# # def transform_zone_data
# def transform_zone_data(json_data: Dict) -> Tuple[Dict, Dict]:
#     """
#     Transform zone configuration data into D3.js compatible format.
#     Args:
#         json_data: JSON object containing zone configuration
#     Returns:
#         Tuple[Dict, Dict]: A tuple containing (active_tree, inactive_tree)
#     """
#     try:
#         # Transform active zones
#         first_active_group = json_data["active"][0]
#         active_tree = {
#             "name": first_active_group["ZoneGrpName"],
#             "id": first_active_group["ZoneGrpId"],
#             "type": "root",
#             "status": "active",
#             "children": [],
#         }

#         for zone in first_active_group["ZoneMembers"]:
#             zone_node = {
#                 "name": zone["ZoneName"],
#                 "id": zone["ZoneId"],
#                 "type": "zone",
#                 "status": "active",
#                 "children": [],
#             }

#             for alias in zone["AliasMembers"]:
#                 alias_node = {
#                     "name": alias["AliasName"],
#                     "id": alias["AliasId"],
#                     "type": "alias",
#                     "status": "active",
#                     "ip": alias.get("IPAddress", "N/A"),
#                     "nqn": alias.get("NQN", "N/A")
#                 }
#                 zone_node["children"].append(alias_node)

#             active_tree["children"].append(zone_node)

#         first_inactive_group = json_data["inactive"][0]
#         inactive_tree = {
#             "name": first_inactive_group["ZoneGrpName"],
#             "id": first_inactive_group["ZoneGrpId"],
#             "type": "root",
#             "status": "inactive",
#             "children": [],
#         }

#         for zone in first_inactive_group["ZoneMembers"]:
#             zone_node = {
#                 "name": zone["ZoneName"],
#                 "id": zone["ZoneId"],
#                 "type": "zone",
#                 "status": "inactive",
#                 "children": [],
#             }

#             for alias in zone["AliasMembers"]:
#                 alias_node = {
#                     "name": alias["AliasName"],
#                     "id": alias["AliasId"],
#                     "type": "alias",
#                     "status": "inactive",
#                     "ip": alias.get("IPAddress", "N/A"),
#                     "nqn": alias.get("NQN", "N/A")
#                 }
#                 zone_node["children"].append(alias_node)

#             inactive_tree["children"].append(zone_node)

#         return active_tree, inactive_tree

#     except KeyError as e:
#         raise Exception(f"Invalid JSON structure. Missing key: {str(e)}")
#     except Exception as e:
#         raise Exception(f"Error processing JSON data: {str(e)}")


# def read_file_content(filename: str) -> str:
#     """Read content of a file from the Static directory."""
#     current_dir = Path(__file__).parent.parent
#     print(f"Current directory: {current_dir}")
#     file_path = os.path.join(current_dir, "renderzone", "Static", filename)
#     if not os.path.exists(file_path):
#         raise FileNotFoundError(
#             f"{filename} not found in Static directory at {file_path}"
#         )
#     with open(file_path, "r", encoding="utf-8") as file:
#         return file.read()


# def load_zone_config() -> Dict:
#     """Load the zone configuration from the JSON file inside RenderZones/data/."""
#     try:
#         config_path = "../CDCMgmt/data/zone_config.json"

#         if not os.path.exists(config_path):
#             raise FileNotFoundError(f"zone_config.json file not found at {config_path}")

#         with open(config_path, "r", encoding="utf-8") as file:
#             return json.load(file)
#     except json.JSONDecodeError:
#         raise Exception("Invalid JSON format in zone_config.json")
#     except Exception as e:
#         raise Exception(f"Error reading zone_config.json: {str(e)}")


# def render_zone_config(json_data: Dict):
#     st.title("Zone Configuration Visualization")

#     try:
#         # Transform the JSON data
#         active_tree, inactive_tree = transform_zone_data(json_data)

#         # Read static files for CSS and JS
#         css_content = read_file_content("style.css")
#         js_content = read_file_content("tree.js")

#         # HTML content with proper subheadings and containers
#         html_content = f"""
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <script src="https://d3js.org/d3.v7.min.js"></script>
#             <style>
#                 {css_content}
#                 .tree-container {{
#                     margin-bottom: 50px;
#                     border: 1px solid #ccc;
#                     padding: 20px;
#                     border-radius: 5px;
#                     overflow: auto;
#                     background: #fff;
#                 }}
#                 .tree-title {{
#                     font-size: 24px;
#                     font-weight: bold;
#                     margin-bottom: 15px;
#                     color: #222;
#                 }}
#                 svg {{
#                     display: block;
#                     width: 100%;
#                     height: 600px;
#                     background: #fafafa;
#                 }}
#                 body {{
#                     font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
#                                   Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
#                     margin: 0;
#                     padding: 10px 20px;
#                     background-color: #f8f9fa;
#                 }}
#             </style>
#         </head>
#         <body>
#             <div class="container">
#                 <div class="tree-container" id="active-tree-container">
#                     <div class="tree-title">Active Zones</div>
#                     <svg id="active-tree-svg"></svg>
#                 </div>

#                 <div class="tree-container" id="inactive-tree-container">
#                     <div class="tree-title">Inactive Zones</div>
#                     <svg id="inactive-tree-svg"></svg>
#                 </div>
#             </div>

#             <script>{js_content}</script>
#             <script>
#                 const activeTree = new TreeChart('#active-tree-svg', {json.dumps(active_tree)}, 1200, 600);
#                 const inactiveTree = new TreeChart('#inactive-tree-svg', {json.dumps(inactive_tree)}, 1200, 600);
#             </script>
#         </body>
#         </html>
#         """

#         # Render the HTML with enough height for scroll
#         st.components.v1.html(html_content, height=1400, scrolling=True)

#     except Exception as e:
#         st.error(f"Error: {str(e)}")


# def fetch_zonecfg_and_render():
#     zonedata_json = load_zone_config()
#     # st.write(zonedata_json)
#     render_zone_config(zonedata_json)


# def main():
#     fetch_zonecfg_and_render()


# # Optional: Call main if running directly
# if __name__ == "__main__":
#     main()
