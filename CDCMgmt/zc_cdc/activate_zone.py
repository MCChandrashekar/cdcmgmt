import streamlit as st
import json
import time
import requests

def create_zone_api(zone_name):
    try:
        res = requests.post(f"http://localhost:5001/cdc/api/v1/zone/{zone_name}")
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response from server"}

def delete_zone_api(zone_name):
    try:
        res = requests.delete(f"http://localhost:5001/cdc/api/v1/zone/{zone_name}")
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response from server"}


# Load data from file
def fetch_zones_from_api():
    res = requests.get("http://localhost:5001/cdc/api/v1/zones")
    return res.json() if res.status_code == 200 else {}

# Save data to file
def save_zones(data):
    with open("../CDCMgmt/data/zones_data.json", "w") as file:
        json.dump(data, file, indent=4)

# data = load_data()

def load_data():
    """Load zones data from file."""
    try:
        with open("../CDCMgmt/data/zones_data.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        # Return default structure if file does not exist
        return {"active_zones": {}, "inactive_zones": {}}

def CreateActivateZone(callback_logging):
    st.write("#### Create Zone")

    # Initialize session state
    if 'zones' not in st.session_state:
        st.session_state.zones = load_data()
    data = st.session_state.zones

    # Create new zone
    zone_name = st.text_input("Enter zone name")
    if st.button("Create Zone"):
        if zone_name in [v["name"] for v in data["active_zones"].values()] + \
                        [v["name"] for v in data["inactive_zones"].values()]:
            st.error("Zone name already exists!", icon="🚫")
            st.stop()

        if zone_name:
            resp = create_zone_api(zone_name)

            if "error" in resp:
                st.error(resp["error"])
            else:
                st.success(f"Zone '{zone_name}' created successfully!")

                # 🔒 Protect this with error handling
                try:
                    res = requests.get("http://localhost:5001/cdc/api/v1/zones")
                    if res.status_code == 200:
                        zone_data = res.json()
                        if isinstance(zone_data, dict) and "active_zones" in zone_data:
                            st.session_state.zones = zone_data
                        else:
                            st.warning("Received unexpected zone format from server.")
                except Exception as e:
                    st.error(f"Failed to fetch updated zones: {e}")

            st.rerun()
        else:
            st.error("Please provide a valid zone name.")



    col1, col2 = st.columns(2)

    # Left Column - Active Zones
    with col1:
        st.write("##### Deactivate Zones")
        active_zone_dict = {v["name"]: k for k, v in data["active_zones"].items()}
        zones_to_deactivate = st.multiselect(
            "Select zones to deactivate",
            options=list(data["active_zones"].values()),
            format_func=lambda x: x["name"]
        )

        if st.button("Deactivate", key="deactivate"):
            if zones_to_deactivate:
                for zone in zones_to_deactivate:
                    zone_id = active_zone_dict[zone["name"]]
                    data["inactive_zones"][zone_id] = data["active_zones"].pop(zone_id)
                    callback_logging(f"Zone {zone['name']} has been deactivated")
                save_zones(data)
                st.toast(f"Zones deactivated successfully!")
                time.sleep(1)
                st.rerun()
            else:
                st.toast("No zones selected for deactivation", icon="⚠️")

        st.write("##### Active Zones")
        st.table([ {"ID": k, "Name": v["name"] , "Alias Count": len(v.get("aliases", {})) } for k, v in data["active_zones"].items()])

    # Right Column - Inactive Zones
    with col2:
        st.write("##### Activate Zones")
        inactive_zone_dict = {v["name"]: k for k, v in data["inactive_zones"].items()}
        zones_to_activate = st.multiselect(
            "Select zones to activate",
            options=list(data["inactive_zones"].values()),
            format_func=lambda x: x["name"]
        )

        if st.button("Activate", key="activate"):
            if zones_to_activate:
                for zone in zones_to_activate:
                    zone_id = inactive_zone_dict[zone["name"]]
                    data["active_zones"][zone_id] = data["inactive_zones"].pop(zone_id)
                    callback_logging(f"Zone {zone['name']} has been activated")
                save_zones(data)
                st.toast(f"Zones activated successfully!")
                time.sleep(1)
                st.rerun()
            else:
                st.toast("No zones selected for activation", icon="⚠️")

        st.write("##### Inactive Zones")
        # st.table([{"ID": k, "Name": v["name"]} for k, v in data["inactive_zones"].items()])
        st.table([{"ID": k, "Name": v["name"],
                   "Alias Count": len(v.get("aliases", {}))} for k, v in data["inactive_zones"].items()])
    
    st.write("##### delete zones")
    delete_zone_dict = {v["name"]: k for k, v in data["inactive_zones"].items()} 
    zones_to_delete = st.multiselect(
        "Select zones to delete",
        options=list(data["inactive_zones"].values()),
        format_func=lambda x: x["name"]
    )
    if st.button("Delete", key="delete"):
        if zones_to_delete:
            for zone in zones_to_delete:
                resp = delete_zone_api(zone["name"])
                if "error" in resp:
                    st.error(resp["error"])
                else:
                    st.success(f"Zone '{zone['name']}' deleted successfully!")

            # ✅ After deletion, reload latest zone data
            try:
                res = requests.get("http://localhost:5001/cdc/api/v1/zones")
                if res.status_code == 200:
                    zone_data = res.json()
                    if isinstance(zone_data, dict) and "active_zones" in zone_data:
                        st.session_state.zones = zone_data
            except Exception as e:
                st.warning(f"Failed to refresh zones after delete: {e}")

            st.rerun()
        else:
            st.toast("No zones selected for deletion", icon="⚠️")


if __name__ == "__main__":
    CreateActivateZone(st.write)
