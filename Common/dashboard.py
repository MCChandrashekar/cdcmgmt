import streamlit as st 
import utils, restncache
import pandas as pd
import jsonify
import requests
from streamlit_extras.colored_header import colored_header # type: ignore
# Disable SSL warnings (useful if accessing a self-signed certificate)
from requests.packages.urllib3.exceptions import InsecureRequestWarning # type: ignore
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_dashboard():
    st.title("NVMe-oF Storage Fabric Statistics")

    # Sample data - replace with your actual data
    stats = {
        "zones": {
            "active": 10,
            "empty": 2,
            "one_member": 3,
            "two_members": 3,
            "more_members": 2,
            "inactive": 5,
            "configured": 15,
            "max_allowed": 50
        },
        "hosts": {
            "total": 20,
            "one_port": 5,
            "two_ports": 8,
            "three_ports": 4,
            "four_ports": 2,
            "more_ports": 1,
            "total_ports": 45
        },
        "controllers": {
            "total": 8,
            "zero_subsystem": 2,
            "one_subsystem": 6,
            "total_subsystems": 12,
            "arrays": 4
        },
        "networks": {
            "configured": 3,
            "max_supported": 10
        }
    }

    # Create layout with three columns
    col1, col2, col3 = st.columns(3)

    with col1:
        # Zone Statistics
        fig1 = go.Figure(data=[
            go.Bar(name='Zone Distribution',
                  x=['Empty', '1 Member', '2 Members', '>2 Members'],
                  y=[stats['zones']['empty'], 
                     stats['zones']['one_member'],
                     stats['zones']['two_members'], 
                     stats['zones']['more_members']],
                  marker_color=['#FFA07A', '#98FB98', '#87CEEB', '#DDA0DD'])
        ])
        fig1.update_layout(title='Zone Distribution', height=300)
        st.plotly_chart(fig1, use_container_width=True)

        # Zone Status Gauge
        fig2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=stats['zones']['configured'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Configured Zones"},
            gauge={'axis': {'range': [None, stats['zones']['max_allowed']]},
                  'bar': {'color': "#1f77b4"}}))
        fig2.update_layout(height=250)
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        # Host Port Distribution
        fig3 = go.Figure(data=[
            go.Pie(labels=['1 Port', '2 Ports', '3 Ports', '4 Ports', '>4 Ports'],
                  values=[stats['hosts']['one_port'],
                         stats['hosts']['two_ports'],
                         stats['hosts']['three_ports'],
                         stats['hosts']['four_ports'],
                         stats['hosts']['more_ports']])
        ])
        fig3.update_layout(title='Host Port Distribution', height=300)
        st.plotly_chart(fig3, use_container_width=True)

        # Controller Statistics
        fig4 = go.Figure(data=[
            go.Bar(name='Controller Distribution',
                  x=['0 Subsystem', '1 Subsystem'],
                  y=[stats['controllers']['zero_subsystem'],
                     stats['controllers']['one_subsystem']],
                  marker_color=['#FF9999', '#66B2FF'])
        ])
        fig4.update_layout(title='Controller Distribution', height=250)
        st.plotly_chart(fig4, use_container_width=True)

    with col3:
        # Summary Metrics
        st.metric("Total Hosts", stats['hosts']['total'])
        st.metric("Total Host Ports", stats['hosts']['total_ports'])
        st.metric("Total Controllers", stats['controllers']['total'])
        st.metric("Total Subsystems", stats['controllers']['total_subsystems'])
        st.metric("Total Arrays", stats['controllers']['arrays'])
        st.metric("Configured Networks", 
                 f"{stats['networks']['configured']}/{stats['networks']['max_supported']}")
        

# Function to fetch data from the API
def fetch_nvmenode_data(cdc_server_ip):
    url = "https://"+cdc_server_ip+":8080/cdc/api/v1/nvmenode"

    try:
        # Send GET request to the API (verify=False is used to bypass SSL verification)
        response = requests.get(url, verify=False)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON responses
            data = response.json()
            
            # Extract relevant parts of the JSON data
            cdc_config = data["commandout"]["data"]["Info"]
        
            # Print the output in the desired format
            for key, val in cdc_config.items():
                st.write(f"{key}                                 :  {val}")

            return data
        else:
            return {"error": f"Failed to fetch data, status code: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        # Catch any exceptions (such as connection errors)
        return {"error": str(e)}
 
def send_get_command(cdc_server_ip, command):
    url = f"https://{cdc_server_ip}:8080/cdc/api/v1/{command}"
    try:
        # Send GET request to the API (verify=False is used to bypass SSL verification)
        response = requests.get(url, verify=False)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            json_data = response.json()
            #st.json(json_data)
            return json_data
        else:
            return {"error": f"Failed to fetch data, status code: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        # Catch any exceptions (such as connection errors)
        return {"error": str(e)}

@st.cache_data
def get_initial_summary(cdc_ip, cmdstr):
    if 'init' not in st.session_state:
        #Initialize session state if not already initialized
        st.session_state.init = True
        dfsummary = send_get_command(cdc_ip, cmdstr)    
        # Initialize the DataFrame in session state
        #st.session_state.summery_prev_df = dfsummary.copy()
        #st.session_state.summary_curr_df = dfsummary.copy()    
        return dfsummary


# Page 0
def cdc_page0_dashboard_text():  #Should be removed
    utils.page_header_title('Registered Storage Nodes')
    
    output = get_initial_summary(st.session_state.server, "summary")
    cdc_config = output["data"]["Info"]

    #st.write(cdc_config)
    
    create_dashboard()
    st.divider()
        
    # Display as a table in Streamlit
    colored_header(label="Current Configuration", description="CDC Current State", color_name="orange-70")
    
    st.markdown(f""" 
    - **No of Registrations**:`{str(cdc_config["No of Regd Endnodes"])}`
    - **No of Interfaces**:`{str(cdc_config['No of Regd Ifaces'])}`
    - **No of Registered Portals**:`{str(cdc_config['No of Regd Portals'])}`
    - **No of Aliases Configured**:`{str(cdc_config['No of Aliases'])}`
    - **No of Zones Configured**:`{str(cdc_config['No of Zones'])}`
    """
    )
    
    colored_header(label="CDC information", description="CDC Static Configuration", color_name="orange-70")    
    st.markdown(f"""
    - **CDC Version**: `{str(cdc_config['CDC Version'])}` 
    - **CDC NQN**: `{str(cdc_config['CDC NQN'])}`
    - **Zone mode**: `{str(cdc_config['Zone mode'])}`
    - **NVMe TCP Port**: `{str(cdc_config['NVMe TCP Port'])}`
    - **MDNS Supported**: {"✅ Supported" if str(cdc_config["MDNS supported"]) else "❌ Not Supported"}`
    - **KATO Value**: `{str(cdc_config['KATO value']), 'ms'}`
    - **Buffer to LDAP Sync Q Depth Max**: `{str(cdc_config['Buf2LDAP Q depth'])}`
    - **CDC mode**: `{str(cdc_config['CDC mode'])}`
    - **Config File Location**: `{str(cdc_config['Config file location'])}`
    """)


    tab1, tab2, tab3, tab4 = st.tabs(["|**Active Interfaces**", "|**Backup Configuration**", "|**Logs Configuration**", "|**HA Configuration**"])

    with tab1:
        output = send_get_command(st.session_state.server, "interfaces")
        st.markdown(f"**Active Interfaces :** `{str(output['data']['count'])}`")
        df = pd.DataFrame(output["data"]["cdc_interfaces"])
        st.table(df)
    with tab2:
        st.markdown(f'''**Backup Enabled**: `{"✅ Enabled" if str(cdc_config["Backup enabled"]) else "❌ Disabled"}`''')
        st.markdown(f'''**Backup File Location**: `{str(cdc_config['Backup file location'])}`''')
    with tab3:
        st.markdown(f'''**Log Level**: `{str(cdc_config['log-level'])}`''')
        st.markdown(f'''**Log File Location**: `{str(cdc_config['Backup file location'])}`''')
    with tab4:
        # VRRP instance data
        ha_info = [
            {
                "name": "ldapdb",
                "details": """
        | Property | Value |
        |----------|-------|
        | State | MASTER |
        | Interface | vlan10 |
        | Using src_ip | 172.17.10.1 |
        | Virtual Router ID | 50 |
        | Priority | 80 |
        | Effective priority | 80 |
        | Virtual IP | 172.17.10.100/24 |
        | Unicast Peer | 172.17.10.2 |
                """
            },
            {
                "name": "otherinterface1",
                "details": """
        | Property | Value |
        |----------|-------|
        | State | MASTER |
        | Interface | vlan20 |
        | Using src_ip | 172.17.20.1 |
        | Virtual Router ID | 51 |
        | Priority | 80 |
        | Effective priority | 80 |
        | Virtual IP | 172.17.20.100/24 |
        | Unicast Peer | 172.17.20.2 |
                """
            },
            {
                "name": "otherinterface2",
                "details": """
        | Property | Value |
        |----------|-------|
        | State | MASTER |
        | Interface | vlan30 |
        | Using src_ip | 172.17.30.1 |
        | Virtual Router ID | 52 |
        | Priority | 80 |
        | Effective priority | 80 |
        | Virtual IP | 172.17.30.100/24 |
        | Unicast Peer | 172.17.30.2 |
                """
            }
        ]

        # Display each instance in an expander
        for instance in ha_info:
            with st.expander(f"VRRP Instance: {instance['name']}", expanded=True):
                st.markdown(instance["details"])

    st.session_state.cdc_status = "Steady"

def configure_cdc():
    st.write("I am in page 1. Configuring CDC")


def cdc_page_dashboard():
    utils.page_header_title('CDC Dashboard')

    output = send_get_command(st.session_state.server, "summary")
    cdc_config = output["data"]["Info"]
    #st.write(cdc_config)

    colored_header(label="Current Configuration", description="CDC Current State", color_name="green-70")
    st.markdown(f"""
    - **No of Regd Portals**: `{str(cdc_config["No of Regd Portals"])}`
    - **No of Regd Endnodes**: `{str(cdc_config["No of Regd Endnodes"])}`
    - **No of Zones**: `{str(cdc_config["No of Zones"])}`
    - **No of Aliases**: `{str(cdc_config["No of Aliases"])}`
    - **No of Regd Ifaces**: `{str(cdc_config["No of Regd Ifaces"])}`
    """)

    colored_header(label="CDC information", description="CDC Static Configuration", color_name="green-70")
    st.markdown(f"""
    - **CDC Version**: `{str(cdc_config["CDC Version"])}`
    - **CDC NQN**: `{str(cdc_config["CDC NQN"])}`
    - **NVMe TCP Port**: `{str(cdc_config["NVMe TCP Port"])}`
    - **MDNS supported**: `{str(cdc_config["MDNS supported"])}`
    - **KATO value**: `{str(cdc_config["KATO value"])}`
    - **Buf2LDAP Q depth**: `{str(cdc_config["Buf2LDAP Q depth"])}`
    - **Zone mode**: `{str(cdc_config["Zone mode"])}`
    - **CDC mode**: `{str(cdc_config["CDC mode"])}`
    - **log-level**: `{str(cdc_config["log-level"])}`
    - **Config file location**: `{str(cdc_config["Config file location"])}`
    - **Backup file location**: `{str(cdc_config["Backup file location"])}`
    - **Backup enabled**: `{str(cdc_config["Backup enabled"])}`
    """)

    tab1, tab2, tab3, tab4 = st.tabs(["|**Active Interfaces**", "|**Backup Configuration**", "|**Logs Configuration**", "|**HA Configuration**"])

    with tab1:
        output = restncache.send_get_command(st.session_state.server, "interfaces")
        st.markdown(f"**Active Interfaces :** `{str(output['data']['count'])}`")
        q1,q2,q3,q4=st.columns(4)
        with q1:
            df = pd.DataFrame(output["data"]["cdc_interfaces"])
            st.table(df)
    with tab2:
        st.markdown(f'''**Backup Enabled**: `{"✅ Enabled" if str(cdc_config["Backup enabled"]) else "❌ Disabled"}`''')
        st.markdown(f'''**Backup File Location**: `{str(cdc_config['Backup file location'])}`''')
    with tab3:
        st.markdown(f'''**Log Level**: `{str(cdc_config['log-level'])}`''')
        st.markdown(f'''**Log File Location**: `{str(cdc_config['Backup file location'])}`''')
    with tab4:
        st.markdown("**HA Configuration**")

    st.session_state.cdc_status = "Steady"

if __name__ == "__main__":
    # Streamlit UI components
    st.title("Registered NVMe Nodes")

    # Button to fetch and display data
    if st.button('Get Registered NVMe Nodes'):
        # Fetch data when button is pressed
        df = send_get_command('nvmenode')
        st.write(df)