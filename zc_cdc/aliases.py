#zc_cdc/aliases.py
import streamlit as st
import json
from .config_manager import update_zone_config
from .data_utils import load_alias, load_zones, save_alias, save_zones


# # Initialize session state for aliases
# if 'aliases' not in st.session_state:
#     st.session_state['aliases'] = load_alias()
# # Initialize session state for zones
# if 'zones' not in st.session_state:
#     st.session_state['zones'] = load_zones()

def refresh_data():
    st.session_state['aliases'] = load_alias()
    st.session_state['zones'] = load_zones()

