#main.py
import streamlit as st
st.set_page_config(layout="wide")
import time
import dashboard
import config_cdc.configure_cdc as configure_cdc
import zc_cdc.config as config
import requests
from renderzone import rendertree
from render_enodes import render_regd_nodes
from restncache import load_zone_config, get_zone_data,read_json_from_data


def login_ui():
    # Initialize session states if not already
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0

    # Centered layout
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🔐 CDC Login</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Please enter your credentials to continue.</p>", unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        if st.session_state.login_attempts >= 3:
            st.error("Too many failed attempts. Please restart the app.")
            return

        if st.button("Login"):
            try:
                response = requests.post("http://localhost:5001/login", json={
                    "username": username,
                    "password": password
                })

                if response.status_code == 200 and response.json().get("success"):
                    st.session_state.authenticated = True
                    st.session_state.login_attempts = 0
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.session_state.login_attempts += 1
                    st.error(f"❌ Invalid username or password. Attempt {st.session_state.login_attempts}/3")
            except Exception as e:
                st.error(f"Login failed. Error: {str(e)}")



def initialize_session_state():
    if 'client' not in st.session_state:
        st.session_state.client = None
    if 'cdc_status' not in st.session_state:
        st.session_state.cdc_status = "CDCRunning"  
    if 'page' not in st.session_state:
        st.session_state.page = 0
    if 'initialization_done' not in st.session_state:
        st.session_state.initialization_done = True
    if 'auto_login_attempted' not in st.session_state:
        st.session_state.auto_login_attempted = True
    if 'main_container' not in st.session_state:
        st.session_state.main_container = st.empty()
    if 'backup_message' not in st.session_state:
        st.session_state.backup_message = None
    if 'refresh_message' not in st.session_state:
        st.session_state.refresh_message = None


def set_page(page_number):
    st.session_state.page = page_number


def disp_sidebar_navigation():
    st.sidebar.button("🏠 Home", key="nav_0", on_click=set_page, args=(0,))
    st.sidebar.header("Connection Status")

    if st.session_state.cdc_status in ("CDCRunning", "Steady"):
        st.sidebar.success("✅ Connected to Server")
    else:
        st.sidebar.warning("⚠️ Not Connected")

    st.sidebar.title("Navigation")

    st.sidebar.button("CDC Dashboard", key="nav_1", on_click=set_page, args=(1,))
    st.sidebar.button("Configure CDC", key="nav_2", on_click=set_page, args=(2,))
    st.sidebar.button("Zone Management", key="nav_3", on_click=set_page, args=(3,))
    st.sidebar.button("Display Zones", key="nav_4", on_click=set_page, args=(4,))
    st.sidebar.button("Display Enodes", key="nav_5", on_click=set_page, args=(5,))
    st.sidebar.button("View Zone Config", key="nav_6", on_click=set_page, args=(6,))


    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()


def render_page_content():
    st.session_state.main_container.empty()
    with st.session_state.main_container.container():
        if st.session_state.page == 0:
            st.title("🚀 HPE Project")
            st.markdown("Web-Based Interface for Centralized Discovery Controller Management")

        elif st.session_state.page == 1:
            dashboard.cdc_page0_dashboard_text()

            if st.session_state.get('cdc_server_ip'):
                try:
                    node_data = restncache.fetch_nvmenode_data(st.session_state.cdc_server_ip)
                    st.write("Node Data:", node_data)
                except Exception as e:
                    st.error(f"Error fetching node data: {str(e)}")

        elif st.session_state.page == 2:
            configure_cdc.main()

        elif st.session_state.page == 3:
            config.main()

        elif st.session_state.page == 4:
            rendertree.main()

        elif st.session_state.page == 5:
            render_regd_nodes.main()


        elif st.session_state.page == 6:
            st.title("📄 Cached Zone Configuration")


            # File options
            file_options = {
                "🧠 Zone Config": "zone_config.json",
                "📦 Zones": "zones_data.json",
                "📂 Zone Groups": "zonegroup_data.json",
                "🔗 Aliases": "alias_data.json"
            }

            selected_file_label = st.selectbox("Select a file to view", list(file_options.keys()))
            selected_file_path = file_options[selected_file_label]

            if st.button("🔄 Refresh"):
                st.cache_data.clear()
                st.success("Cache cleared. Latest data loaded.")
                
            try:
                file_data = read_json_from_data(selected_file_path)
                st.subheader(f"Showing: {selected_file_label}")
                st.json(file_data)

            except Exception as e:
                st.error(f"Error loading {selected_file_path}: {str(e)}")




def main():
    initialize_session_state()

    if st.session_state.cdc_status in ("CDCRunning", "Steady"):
        disp_sidebar_navigation()
        render_page_content()

if __name__ == "__main__":
    if 'refresh_count' not in st.session_state:
        st.session_state.refresh_count = 0
    else:
        st.session_state.refresh_count += 1
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        login_ui()
    else:
        main()