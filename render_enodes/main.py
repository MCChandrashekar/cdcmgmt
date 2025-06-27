import time
import streamlit as st

import render_enodes.render_regd_nodes as dispenodes


def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'client' not in st.session_state:
        st.session_state.client = None
    if 'cdc_status' not in st.session_state:
        st.session_state.cdc_status = None
    if 'page' not in st.session_state:
        st.session_state.page = 0
    if 'initialization_done' not in st.session_state:
        st.session_state.initialization_done = False
    if 'auto_login_attempted' not in st.session_state:
        st.session_state.auto_login_attempted = False
    if 'main_container' not in st.session_state:
        st.session_state.main_container = st.empty()

def set_page(page_number):
    """Set the page number in session state"""
    st.session_state.page = page_number

def disp_sidebar_navigation():
    st.sidebar.header("Connection Status")
    st.sidebar.success("Connected to Server, CDC is running")
    st.sidebar.title("Navigation")
    
    if st.sidebar.button("CDC Dashboard", key="nav_0"):
        print("Setting Page to 0")
        set_page(0)
        st.rerun()
    if st.sidebar.button("Configure CDC", key="nav_1"):
        print("Setting Page to 1")
        set_page(1)
        st.rerun()
    if st.sidebar.button("Display End Nodes", key="nav_2"):
        print("Setting Page to 2")
        set_page(2)
        st.rerun()
    if st.sidebar.button("Configure Zone", key="nav_3"):
        print("Setting Page to 3")
        set_page(3)
        st.rerun()
    if st.sidebar.button("Display Zones", key="nav_4"):
        print("Setting Page to 4")
        set_page(4)
        st.rerun()

def render_page_content():
    """Render the main page content based on current page"""
    # Clear previous content
    st.session_state.main_container.empty()
    
    # Create new container for current content
    print("Starting main_container")
    with st.session_state.main_container.container():
        if st.session_state.page == 0:
            #st.write("CDC Dashboard, Page 0")
            print("CDC Dashboard, Page 0")
            dashboard.cdc_page0_dashboard_text()
        elif st.session_state.page == 1:
            #st.write("executing configure_cdc")
            print("executing configure_cdc")
            configcdc.configure_cdc_settings()
            #st.write("CDC Config, Page 1")
        elif st.session_state.page == 2:
            print("CDC End Nodes, Page 2")
            dispenodes.render_hosts_subsystems()
            #st.write("CDC End Nodes, Page 2")
        elif st.session_state.page == 3:
            print("CDC Zone Config, Page 3")
            cfgzones.configure_aliases_zones()
            #st.write("CDC Zone Config, Page 3")
        elif st.session_state.page == 4:
            print("CDC Zone view, Page 4")
            dispzones.fetch_zonecfg_and_render()
            #st.write("CDC Zone view, Page 4")

def handle_auto_login():
    """Handle automatic login with predefined credentials"""
    login_container = st.empty()
    with login_container.container():
        if not st.session_state.auto_login_attempted:
            with st.spinner("Attempting auto-login..."):
                ssh_manager = utils.get_ssh_manager()
                client = ssh_manager.connect(host="10.22.14.249", username="mcc", password="rakesh")
                
                if client:
                    st.session_state.client = client
                    st.session_state.server = "10.22.14.249"
                    st.session_state.username = "mcc"
                    st.session_state.password = "rakesh"
                    st.session_state.cdc_status = "Connected"
                    st.success("Auto-login successful!")
                else:
                    st.error("Auto-login failed. Please login manually.")
                    
                st.session_state.auto_login_attempted = True
                time.sleep(1)  # Give user time to see the message
                st.rerun()
    login_container.empty()

def main():
    initialize_session_state()
    args = utils.parse_inp_args()
    
    # Login phase
    if not st.session_state.initialization_done:
        if args.auto_login:
            handle_auto_login()
        else:
            login_container = st.empty()
            with login_container.container():
                utils.display_login_page()
            if st.session_state.cdc_status == "Connected":
                login_container.empty()
    
    print(f"connection status @1 = {st.session_state.cdc_status}")
    # CDC verification phase
    if st.session_state.cdc_status == "Connected":
        verify_container = st.empty()
        with verify_container.container():
            utils.verify_cdc_cfg_running()
        if st.session_state.cdc_status == "CDCRunning":
            verify_container.empty()
            st.session_state.initialization_done = True
            st.rerun()
    
    print(f"connection status @2 = {st.session_state.cdc_status}")
    # Main application phase
    #if st.session_state.cdc_status == "CDCRunning": 
        #print(f"connection status @3 = {st.session_state.cdc_status}")
        #restncache.restapi_init()
        #st.session_state.status = "Steady"
    
    if st.session_state.cdc_status == "Steady" or st.session_state.cdc_status == "CDCRunning": 
        print(f"connection status @4 = {st.session_state.cdc_status}")
        disp_sidebar_navigation()
        print(f"connection status @5 = {st.session_state.cdc_status}")
        restncache.restapi_init()
        time.sleep(1.5)
        render_page_content()
        print(f"connection status @6 = {st.session_state.cdc_status}")

if __name__ == "__main__":
    if 'refresh_count' not in st.session_state:
        st.session_state.refresh_count = 0
    else:
        st.session_state.refresh_count+=1
        print(f"Refresh count {st.session_state.refresh_count}")

    main()