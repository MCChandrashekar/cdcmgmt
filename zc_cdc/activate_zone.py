#zc_cdc/activate_zone.py
import streamlit as st
import json
import requests
import pandas as pd
from .data_utils import load_zones, save_zones, load_alias, save_alias, load_zonegroup
from .config_manager import update_zone_config


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

def fetch_zones_from_api():
    res = requests.get("http://localhost:5001/cdc/api/v1/zones")
    return res.json() if res.status_code == 200 else {}

# def save_zones(data):
#     with open("../CDCMgmt/data/zones_data.json", "w") as file:
#         json.dump(data, file, indent=4)
#     # update_zone_config()

# def save_aliases(data):
#     with open("../CDCMgmt/data/alias_data.json", "w") as file:
#         json.dump(data, file, indent=4)


# def load_data():
#     """Load zones data from file."""
#     try:
#         with open("../CDCMgmt/data/zones_data.json", "r") as file:
#             return json.load(file)
#     except FileNotFoundError:
#         return {"active_zones": {}, "inactive_zones": {}}

# def load_alias():
#     try:
#         with open("../CDCMgmt/data/alias_data.json", "r") as file:
#             return json.load(file)
#     except (json.JSONDecodeError, FileNotFoundError):
#         return {"member_aliases": {}, "free_aliases": {}}
    
def CreateActivateZone(callback_logging):
    st.write("#### Create Zone")

    zones =load_zones()
    st.session_state.zones = load_zones()
    data = zones
    st.session_state.alias_data = load_alias()
    zonegroup_data = load_zonegroup()
    # Create reverse mapping: zone_id -> group_name
    zone_to_group = {}
    for group_id, group in zonegroup_data["zone_groups"].items():
        for zone_id in group["zones"]:
            zone_to_group[zone_id] = group["name"]

    # Create new zone section
    col1, col2 = st.columns([2,3])  
    with col1:
        zone_name = st.text_input("Enter zone name")
    with col2:
        st.write("   ")
        st.write("   ")
        if st.button("Create Zone"):
            if zone_name in [v["name"] for v in data["active_zones"].values()] + \
                            [v["name"] for v in data["inactive_zones"].values()]:
                st.error("Zone name already exists!", icon="🚫")
                st.stop()
            if not zone_name:
                st.error("Please provide a valid zone name.")
            elif zone_name in [v["name"] for v in data["active_zones"].values()] + \
                                [v["name"] for v in data["inactive_zones"].values()]:
                    st.error("Zone name already exists!")
            else:
                resp = create_zone_api(zone_name)
                if "error" in resp:
                    st.error(resp["error"])
                else:
                        # New zones are created as inactive by default
                    zone_id = str(len(data["inactive_zones"]) + len(data["active_zones"]) + 1)
                    data["inactive_zones"][zone_id] = {"name": zone_name, "aliases": {}}
                    save_zones(data)
                    from .config_manager import update_zone_config
                    update_zone_config()
                    st.success(f"Zone '{zone_name}' created successfully!")
                    st.rerun()

    # Combine all zones for selection
    all_zones = {**data["active_zones"], **data["inactive_zones"]}

    # Zone selection section
    st.write("### Select Zone to Configure")
    if not all_zones:
        st.info("No zones available. Create a zone first.")
        return

    # table data with group information
    zone_rows = []
    for zone_id, zone in {**data["active_zones"], **data["inactive_zones"]}.items():
        zone_rows.append({
            "ID": zone_id,
            "Zone Name": zone["name"],
            # "Status": "Active" if zone_id in data["active_zones"] else "Inactive",
            "Member of": zone_to_group.get(zone_id, " "),  
            "Alias Count": len(zone.get("aliases", {})),
            "Select": False
        })

    zone_df = pd.DataFrame(zone_rows)

    # zone_df = pd.DataFrame([
    #     {
    #         "Zone Name": zone["name"],
    #         "ID": zone_id,
    #         "Status": "Active" if zone_id in data["active_zones"] else "Inactive",
    #         "Alias Count": len(zone.get("aliases", {})),
    #         "Select": False
    #     }
    #     for zone_id, zone in all_zones.items()
    # ])

    # def select_row(row):
    #     return {"Select": st.radio("", [False, True], index=0, label_visibility="collapsed", key=f"select_{row['ID']}")}
    
    edited_df = st.data_editor(
        zone_df,
        width=900,         
        column_config={
            "Select": st.column_config.CheckboxColumn("Select", default=False),
            "ID": st.column_config.TextColumn("ID", width="small"),
            "Zone Name": st.column_config.TextColumn("Zone Name"),
            "Member of": st.column_config.TextColumn("Member of", width="medium"),
            # "Status": st.column_config.TextColumn("Status"),
            "Alias Count": st.column_config.NumberColumn("Alias Count")
        },
        hide_index=True,
        disabled=["Zone Name","Member of" , "Alias Count"]
    )
    
    selected_row = edited_df[edited_df["Select"]]
    if len(selected_row) == 0:
        st.info("Please select a zone to configure")
        return
    
    selected_zone_id = selected_row.iloc[0]["ID"]
    selected_zone = all_zones[selected_zone_id]

    st.write(f" #### Selected Zone: {selected_zone['name']} (ID: {selected_zone_id})")
    selected_zone = all_zones[selected_zone_id]

    # Delete zone section
    col1, col2 = st.columns([1,5])  # Adjust the ratio as needed
    with col1:
        st.write("#### Delete Zone: ")

    with col2:
        if st.button(f"Delete Zone '{selected_zone['name']}'", type="primary"):
            if 'aliases' in selected_zone and selected_zone['aliases']:
                st.error("Cannot delete zone: Please remove all aliases from this zone first")
                st.info(f"Current aliases in zone: {len(selected_zone['aliases'])}")
            else:
                if selected_zone_id in st.session_state.zones["active_zones"]:
                    del st.session_state.zones["active_zones"][selected_zone_id]
                else:
                    del st.session_state.zones["inactive_zones"][selected_zone_id]  
                save_zones(st.session_state.zones)
                update_zone_config()
                st.success(f"Zone '{selected_zone['name']}' deleted successfully!")
                st.session_state.confirm_delete = False
                st.rerun()
                
    alias_data = load_alias()
    col1, col2 = st.columns(2)
    # Left column - Current zone aliases
    with col1:
        st.write(f"#### Aliases in Zone: {selected_zone['name']}")
        if 'aliases' not in selected_zone or not selected_zone['aliases']:
            st.info("No aliases in this zone")
        else:
            current_aliases = pd.DataFrame([
                {
                    "ID": k, 
                    "Name": v["name"], 
                    "Type": v.get("type", ""),
                    "Select": False
                } 
                for k, v in selected_zone['aliases'].items()
            ])
            # Display editable table
            edited_current = st.data_editor(
                current_aliases,
                column_config={
                    "ID": st.column_config.TextColumn("ID", width="small"),
                    "Name": st.column_config.TextColumn("Name", width="medium"),
                    "Type": st.column_config.TextColumn("Type", width="small"),
                    "Select": st.column_config.CheckboxColumn("Select", width="small")
                },
                hide_index=True,
                disabled=["ID", "Name", "Type"],
                key=f"current_{selected_zone_id}"
            )
            # Remove selected button
            if st.button("➖ Remove Selected", key=f"remove_{selected_zone_id}"):
                aliases_to_remove = edited_current[edited_current["Select"]]["ID"].tolist()
                for alias_id in aliases_to_remove:
                    selected_zone['aliases'].pop(alias_id, None)
                save_zones(data)
                save_alias(alias_data)
                from .config_manager import update_zone_config
                update_zone_config()
                st.success(f"Removed {len(aliases_to_remove)} aliases")
                st.rerun()
            # # st.table(alias_list)
            
            # # Multiselect for removal
            # aliases_to_remove = st.multiselect(
            #     "Select aliases to remove:",
            #     options=list(current_aliases.keys()),
            #     format_func=lambda x: current_aliases[x]["name"]
            # )
            
            # if st.button("Remove Selected Aliases"):
            #     for alias_id in aliases_to_remove:
            #         selected_zone['aliases'].pop(alias_id)
            #     save_zones(data)
            #     st.success(f"Removed {len(aliases_to_remove)} aliases from zone")
            #     st.rerun()
    
    # Right column - Available aliases to add
    with col2:
        st.write("#### Available Aliases")
        alias_data = load_alias()  
        current_alias_ids = set(selected_zone.get('aliases', {}).keys())
        available_aliases = {
            k: v for k, v in alias_data["free_aliases"].items() 
            if k not in current_alias_ids
        }
        if not available_aliases:
            st.info("No available aliases to add")
        else:
            # Create table with checkboxes
            available_alias = pd.DataFrame([
                {
                    "ID": k, 
                    "Name": v["name"], 
                    "Type": v.get("type", ""),
                    "Select": False
                } 
                for k, v in available_aliases.items()
            ])
             # Display editable table
            edited_available = st.data_editor(
                available_alias,
                column_config={
                    "ID": st.column_config.TextColumn("ID", width="small"),
                    "Name": st.column_config.TextColumn("Name", width="medium"),
                    "Type": st.column_config.TextColumn("Type", width="small"),
                    "Select": st.column_config.CheckboxColumn("Select", width="small")
                },
                hide_index=True,
                disabled=["ID", "Name", "Type"],
                key=f"available_{selected_zone_id}"
            )
            
            # Add selected button
            if st.button("➕ Add Selected", key=f"add_{selected_zone_id}"):
                aliases_to_add = edited_available[edited_available["Select"]]["ID"].tolist()
                for alias_id in aliases_to_add:
                    if alias_id in available_aliases:
                        selected_zone.setdefault('aliases', {})[alias_id] = available_aliases[alias_id]
                save_zones(data)
                save_alias(alias_data)
                from .config_manager import update_zone_config
                update_zone_config()
                st.success(f"Added {len(aliases_to_add)} aliases")
                st.rerun()
            # st.table(alias_list)
            
            # # Multiselect for addition
            # aliases_to_add = st.multiselect(
            #     "Select aliases to add:",
            #     options=list(available_aliases.keys()),
            #     format_func=lambda x: available_aliases[x]["name"]
            # )
            
            # if st.button("Add Selected Aliases"):
            #     for alias_id in aliases_to_add:
            #         if alias_id in available_aliases:
            #             if 'aliases' not in selected_zone:
            #                 selected_zone['aliases'] = {}
            #             selected_zone['aliases'][alias_id] = available_aliases[alias_id]
            #     save_zones(data)
            #     st.success(f"Added {len(aliases_to_add)} aliases to zone")
            #     st.rerun()

if __name__ == "__main__":
    CreateActivateZone(st.write)




# -----OLD CODE-----
# import streamlit as st
# import json
# import time
# import requests

# def create_zone_api(zone_name):
#     try:
#         res = requests.post(f"http://localhost:5001/cdc/api/v1/zone/{zone_name}")
#         res.raise_for_status()
#         return res.json()
#     except requests.exceptions.RequestException as e:
#         return {"error": f"Request failed: {str(e)}"}
#     except json.JSONDecodeError:
#         return {"error": "Invalid JSON response from server"}

# def delete_zone_api(zone_name):
#     try:
#         res = requests.delete(f"http://localhost:5001/cdc/api/v1/zone/{zone_name}")
#         res.raise_for_status()
#         return res.json()
#     except requests.exceptions.RequestException as e:
#         return {"error": f"Request failed: {str(e)}"}
#     except json.JSONDecodeError:
#         return {"error": "Invalid JSON response from server"}


# # Load data from file
# def fetch_zones_from_api():
#     res = requests.get("http://localhost:5001/cdc/api/v1/zones")
#     return res.json() if res.status_code == 200 else {}

# # Save data to file
# def save_zones(data):
#     with open("../CDCMgmt/data/zones_data.json", "w") as file:
#         json.dump(data, file, indent=4)

# # data = load_data()

# def load_data():
#     """Load zones data from file."""
#     try:
#         with open("../CDCMgmt/data/zones_data.json", "r") as file:
#             return json.load(file)
#     except FileNotFoundError:
#         # Return default structure if file does not exist
#         return {"active_zones": {}, "inactive_zones": {}}

# def CreateActivateZone(callback_logging):
#     st.write("#### Create Zone")

#     # Initialize session state
#     if 'zones' not in st.session_state:
#         st.session_state.zones = load_data()
#     data = st.session_state.zones

#     # Create new zone
#     zone_name = st.text_input("Enter zone name")
#     if st.button("Create Zone"):
#         if zone_name in [v["name"] for v in data["active_zones"].values()] + \
#                         [v["name"] for v in data["inactive_zones"].values()]:
#             st.error("Zone name already exists!", icon="🚫")
#             st.stop()

#         if zone_name:
#             resp = create_zone_api(zone_name)
#             if "error" in resp:
#                 st.error(resp["error"])
#             else:
#                 # New zones are created as inactive by default
#                 zone_id = str(len(data["inactive_zones"]) + len(data["active_zones"]) + 1)
#                 data["inactive_zones"][zone_id] = {"name": zone_name, "aliases": {}}
#                 save_zones(data)
#                 st.success(f"Zone '{zone_name}' created successfully!")
#                 st.rerun()

#     # Display all zones (grouped zones will appear as active)
#     st.write("##### All Zones")
#     all_zones = {**data["active_zones"], **data["inactive_zones"]}
#     st.table([{
#         "ID": k, 
#         "Name": v["name"],
#         "Status": "Active" if k in data["active_zones"] else "Inactive",
#         "Alias Count": len(v.get("aliases", {}))
#     } for k, v in all_zones.items()])

#     st.write("##### Delete Zones")
#     zones_to_delete = st.multiselect(
#         "Select zones to delete",
#         options=list(all_zones.values()),
#         format_func=lambda x: x["name"]
#     )
    
#     if st.button("Delete", key="delete"):
#         if zones_to_delete:
#             for zone in zones_to_delete:
#                 zone_id = next(k for k, v in all_zones.items() if v["name"] == zone["name"])
#                 resp = delete_zone_api(zone["name"])
#                 if "error" in resp:
#                     st.error(resp["error"])
#                 else:
#                     if zone_id in data["active_zones"]:
#                         data["active_zones"].pop(zone_id)
#                     else:
#                         data["inactive_zones"].pop(zone_id)
#                     save_zones(data)
#                     st.success(f"Zone '{zone['name']}' deleted successfully!")
#             st.rerun()

# if __name__ == "__main__":
#     CreateActivateZone(st.write)
