import streamlit as st
import json
import time
from .config_manager import update_zone_config
# Load data from file
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

# Save data to file
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
    # Refresh the data in session state
    st.session_state['aliases'] = load_alias()
    st.session_state['zones'] = load_zones()

def Alias2ZoneLink(callback_logging):
    if 'aliases' not in st.session_state or 'zones' not in st.session_state:
        refresh_data()
    
    # Add refresh button at the top
    if st.button("🔄 Refresh Alias Data"):
        refresh_data()
        st.rerun()
    alias_data = st.session_state['aliases']
    zone_data = st.session_state['zones']

    st.write("#### Link Aliases to Zones")
    st.write("##### Select Zone")
    # Select a zone from the list
    all_zones = {**zone_data["active_zones"], **zone_data["inactive_zones"]}
    selected_zone_id = st.selectbox(
        "Select Zone to Configure",
        options=list(all_zones.keys()),
        format_func=lambda x: f"{all_zones[x]['name']} (ID: {x})"
    )
    selected_zone_name = all_zones[selected_zone_id]
    zone_aliases_dict = selected_zone_name.get("aliases", {})
    cleaned_aliases = {}
    for alias_id, alias_info in zone_aliases_dict.items():
        if alias_id in alias_data["member_aliases"]:
            cleaned_aliases[alias_id] = alias_info
        else:
            callback_logging(f"Cleaned up orphaned alias reference: {alias_id}")
    selected_zone_name["aliases"] = cleaned_aliases
    zone_alias_ids = list(zone_aliases_dict.keys())
    # zone_alias = selected_zone_name.get("aliases", [])
    st.write(f"Selected Zone: {selected_zone_name.get('name') }")
    st.write("#### Manage Selected Zone, its members")
    col1, col2 = st.columns(2)
    
    # Left Column - Member Aliases
    with col1:
        st.write("##### Remove aliases")
        q1, q2 = st.columns(2, vertical_alignment='bottom')
        with q1:
            # Aliases currently in the selected zone
            # member_alias_dict = {v["name"]: k for k, v in alias_data["member_aliases"].items()}
            zone_member_aliases = {k: v for k, v in alias_data["member_aliases"].items() if k in zone_alias_ids}
            # Check for alias IDs in zone that aren't in member_aliases
            missing_ids = [aid for aid in zone_alias_ids if aid not in alias_data["member_aliases"]]
            if missing_ids:
                st.warning(f"Warning: The following alias IDs are in zone data but missing from member_aliases: {missing_ids}")

            member_alias_dict = {v["name"]: k for k, v in zone_member_aliases.items()}

            aliases_for_remove = st.multiselect(
                "Select aliases to Remove",
                options=list(zone_member_aliases.values()), 
                format_func=lambda x: x["name"]
            )
        
        with q2:
            if st.button("Remove", key="Remove"):
                if aliases_for_remove:
                    for alias in aliases_for_remove:
                        alias_id = member_alias_dict[alias["name"]]
                        alias_data["free_aliases"][alias_id] = alias_data["member_aliases"].pop(alias_id)

                        if selected_zone_id in zone_data["active_zones"]:
                            zone_obj = zone_data["active_zones"][selected_zone_id]
                        elif selected_zone_id in zone_data["inactive_zones"]:
                            zone_obj = zone_data["inactive_zones"][selected_zone_id]
                        else:
                            st.error("Zone not found!")
                            return
                        # Remove the alias from the zone
                        if alias_id in zone_obj.get("aliases", {}):
                            zone_obj["aliases"].pop(alias_id)
                        save_alias_data(alias_data)
                        save_zone_data(zone_data)
                        st.toast(f"Alias {alias['name']} removed from {selected_zone_name.get('name')}")
                        #st.write(f"Removing alias id {alias_id} from zone={selected_zone_name}")
                        callback_logging(f"Removing alias id {alias_id} from zone={selected_zone_name}")
                        st.session_state['zones'] = zone_data
                        time.sleep(1)
                        st.rerun()
                else:
                    st.toast("No aliases selected for removal.", icon="⚠️")
                    
        st.write("##### Aliases Currently in the Zone")
        st.table([{"ID": k, "Name": v["name"], "Type": v["type"]} for k, v in zone_member_aliases.items()])
        st.caption("Aliases that are already added to the selected zone.")

    # Right Column - Free Aliases
    with col2:
        st.write("##### Add aliases")
        q3, q4 = st.columns(2, vertical_alignment='bottom')
        with q3:
            # Aliases not currently in the selected zone
            zone_free_aliases = {k: v for k, v in alias_data["free_aliases"].items() if k not in zone_alias_ids}
            other_member_aliases = {k: v for k, v in alias_data["member_aliases"].items()if k not in zone_aliases_dict}
            # Combine both sources of available aliases
            all_available_aliases = {**zone_free_aliases, **other_member_aliases}
            free_alias_dict = {v["name"]: k for k, v in all_available_aliases.items()}
            aliases_for_add = st.multiselect(
                "Select aliases to Add",
                options=list(all_available_aliases.values()),
                format_func=lambda x: x["name"]
            )
        with q4:
            if st.button("Add", key="add"):
                if aliases_for_add:
                    for alias in aliases_for_add:
                        alias_id = free_alias_dict[alias["name"]]
                        if alias_id in alias_data["free_aliases"]:
                            alias_data["member_aliases"][alias_id] = alias_data["free_aliases"].pop(alias_id)
                        if selected_zone_id in zone_data["active_zones"]:
                            zone_obj = zone_data["active_zones"][selected_zone_id]
                        elif selected_zone_id in zone_data["inactive_zones"]:
                            zone_obj = zone_data["inactive_zones"][selected_zone_id]
                        else:
                            st.error("Zone not found!")
                            return
                        if "aliases" not in selected_zone_name:
                            zone_obj["aliases"] = {}
                        if alias_id not in selected_zone_name["aliases"]:
                            zone_obj["aliases"][alias_id] = alias_data["member_aliases"][alias_id]
                        st.toast(f"Alias {alias['name']} added to {selected_zone_name.get('name')}")
                        #st.write(f"Alias {alias['name']} added to Zone {selected_zone_name}")
                        callback_logging(f"Alias {alias['name']} added to Zone {selected_zone_name}")
                        save_alias_data(alias_data)
                        save_zone_data(zone_data)
                        st.session_state['zones'] = zone_data
                        time.sleep(1)
                        st.rerun()
                else:
                    st.toast("No aliases selected for addition.", icon="⚠️")
                    
        st.write("##### Available Aliases to Add")
        st.table([{"ID": k, "Name": v["name"], "Type": v.get("type", ""), "Status": "Free" if k in alias_data["free_aliases"] else "In Other Zone"} for k, v in all_available_aliases.items()])
        st.caption("These aliases are not part of the selected zone and can be added.")


if __name__ == "__main__":
    Alias2ZoneLink(st.write)