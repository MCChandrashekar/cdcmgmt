import streamlit as st
import requests
import json
import pandas as pd

# Configuration
REST_SERVER_URL = "http://localhost:5000"

# Page title and description
st.title("Zone Management Client")
st.markdown("This application allows you to manage zones through a REST API.")

# Add a sidebar for different operations
operation = st.sidebar.radio(
    "Select Operation",
    ["Create Zone", "List All Zones", "Get Zone Details", "Delete Zone"]
)

# Function to display a success or error message
def display_message(success, message, details=None):
    if success:
        st.success(message)
        if details:
            st.json(details)
    else:
        st.error(message)
        if details:
            st.json(details)

# Function to call the REST API
def call_api(method, endpoint, data=None):
    url = f"{REST_SERVER_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            return False, "Invalid method", None
        
        response_data = response.json()
        
        if response.status_code >= 200 and response.status_code < 300:
            return True, "Success", response_data
        else:
            return False, response_data.get("error", "Unknown error"), response_data
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}", None
    except Exception as e:
        return False, f"Error: {str(e)}", None

# Create Zone Section
if operation == "Create Zone":
    st.header("Create Zone")
    st.markdown("Create a new zone by providing a name.")
    
    # Input field for zone name
    zone_name = st.text_input("Zone Name", 
                             help="Enter an alphanumeric name (hyphens and underscores allowed)")
    
    # Create button
    if st.button("Create Zone"):
        if zone_name:
            success, message, data = call_api(
                "POST", 
                "/zone", 
                {"command": "CREATE", "zone_name": zone_name}
            )
            display_message(success, message, data)
        else:
            st.warning("Please enter a zone name")

# List All Zones Section
elif operation == "List All Zones":
    st.header("List All Zones")
    st.markdown("View all existing zones.")
    
    # Refresh button
    if st.button("Refresh Zone List"):
        with st.spinner("Loading zones..."):
            success, message, data = call_api("GET", "/zones")
            
            if success and data and "zones" in data:
                if data["zones"]:
                    # Convert to DataFrame for better display
                    zones_df = pd.DataFrame(data["zones"])
                    st.dataframe(zones_df)
                else:
                    st.info("No zones found")
            else:
                display_message(success, message, data)

# Get Zone Details Section
elif operation == "Get Zone Details":
    st.header("Get Zone Details")
    st.markdown("View details for a specific zone.")
    
    # Get all zones first to populate the dropdown
    success, _, data = call_api("GET", "/zones")
    zone_names = []
    
    if success and data and "zones" in data:
        zone_names = [zone["name"] for zone in data["zones"]]
    
    # Dropdown to select zone
    selected_zone = st.selectbox("Select Zone", 
                               options=zone_names if zone_names else ["No zones available"],
                               disabled=not zone_names)
    
    # Get details button
    if st.button("Get Zone Details"):
        if zone_names and selected_zone != "No zones available":
            with st.spinner("Loading zone details..."):
                success, message, data = call_api("GET", f"/zone/{selected_zone}")
                
                if success and data and "zone" in data:
                    st.json(data["zone"])
                else:
                    display_message(success, message, data)
        else:
            st.info("No zones available to display")

# Delete Zone Section
elif operation == "Delete Zone":
    st.header("Delete Zone")
    st.markdown("Delete an existing zone.")
    
    # Get all zones first to populate the dropdown
    success, _, data = call_api("GET", "/zones")
    zone_names = []
    
    if success and data and "zones" in data:
        zone_names = [zone["name"] for zone in data["zones"]]
    
    # Dropdown to select zone
    selected_zone = st.selectbox("Select Zone to Delete", 
                               options=zone_names if zone_names else ["No zones available"],
                               disabled=not zone_names)
    
    # Delete button with confirmation
    if zone_names and selected_zone != "No zones available":
        if st.button("Delete Zone", type="primary", help="This action cannot be undone"):
            with st.spinner(f"Deleting zone {selected_zone}..."):
                success, message, data = call_api("DELETE", f"/zone/{selected_zone}")
                display_message(success, message, data)
    else:
        st.info("No zones available to delete")

# Footer
st.markdown("---")
st.caption("Zone Management REST Client - Connected to " + REST_SERVER_URL)

# Add error handling for server connection
if st.sidebar.button("Check Server Connection"):
    with st.spinner("Checking connection..."):
        try:
            response = requests.get(f"{REST_SERVER_URL}/zones", timeout=5)
            if response.status_code >= 200 and response.status_code < 300:
                st.sidebar.success("Server is online")
            else:
                st.sidebar.error(f"Server returned: {response.status_code}")
        except requests.exceptions.RequestException:
            st.sidebar.error("Cannot connect to server")

