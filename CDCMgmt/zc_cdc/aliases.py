import streamlit as st
import json
from .config_manager import update_zone_config

def load_alias():
    try:
        with open("../CDCMgmt/data/alias_data.json", "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"member_aliases": {}, "free_aliases": {}}

def load_zones():
    try:
        with open("../CDCMgmt/data/zones_data.json", "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"active_zones": {}, "inactive_zones": {}}

def save_alias_data(alias_data):
    with open("../CDCMgmt/data/alias_data.json", "w") as file:
        json.dump(alias_data, file, indent=4)

def save_zone_data(zone_data):
    with open("../CDCMgmt/data/zones_data.json", "w") as file:
        json.dump(zone_data, file, indent=4)   
    update_zone_config()

# # Initialize session state for aliases
# if 'aliases' not in st.session_state:
#     st.session_state['aliases'] = load_alias()
# # Initialize session state for zones
# if 'zones' not in st.session_state:
#     st.session_state['zones'] = load_zones()

def refresh_data():
    st.session_state['aliases'] = load_alias()
    st.session_state['zones'] = load_zones()

