#zc_cdc/zonegroup.py
import streamlit as st
import json
import re
import time
import requests
import pandas as pd
from .data_utils import load_zones, load_zonegroup, save_zonegroup


# def load_zonegroup():
#     try:
#         with open("../CDCMgmt/data/zonegroup_data.json", "r") as file:
#             return json.load(file)
#     except (json.JSONDecodeError, FileNotFoundError):
#         return {"zone_groups": {}}
# def save_zonegroup(zonegroup_data):
#     with open("../CDCMgmt/data/zonegroup_data.json", "w") as file:
#         json.dump(zonegroup_data, file, indent=4)

data = load_zonegroup()
 
def get_next_group_id(data):
    if not data["zone_groups"]:
        return "1"
    return str(max(map(int, data["zone_groups"].keys())) + 1)

def create_zone_group(name):
    data = load_zonegroup()
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise ValueError("Group name must be alphanumeric with _ or -")
    for g in data["zone_groups"].values():
        if g["name"] == name:
            raise ValueError(f"Group '{name}' already exists")
    new_id = get_next_group_id(data)
    
    # Add new group to data
    data["zone_groups"][new_id] = {
        "name": name,
        "zones": [],  # Stores selected zones
        "active": False
    }
    save_zonegroup(data)
    from .config_manager import update_zone_config  # 👈 local import here
    update_zone_config()
    return name


def CreateZoneGroup(callback_logging):
    st.subheader("Zone Group Creation")
    col1, col2 = st.columns([1, 3])
    with col1:
        group_name = st.text_input("Enter Zone Group Name")
    with col2:
        st.write("  ")
        st.write("  ")
        if st.button("Create Zone Group"):
            try:
                if not group_name:
                    st.warning("Please enter a group name.")
                    return
                else:
                    resp = requests.post(f"http://localhost:5001/cdc/api/v1/zgrp/{group_name}")
                    if resp.status_code != 201:
                        raise ValueError(resp.json().get("error", "Failed to create zone group"))
                    callback_logging(f"Zone Group '{group_name}' created")
                    st.success(f"Zone Group '{group_name}' created!")
                    st.toast(f"Zone Group '{group_name}' created successfully!", icon="✅")
                    time.sleep(1) 
                    st.rerun()
            except Exception as e:
                st.error(str(e))

st.divider()

def ZoneGroupManager(callback_logging):
    st.write("### Zone Group Management")
    data = load_zonegroup()
    zone_data = load_zones()

    if not data["zone_groups"]:
        st.info("No zone groups created yet")
    else:
        groups_df = pd.DataFrame([
            {
                "ID": group_id,
                "Name": group["name"],
                "Member Count": len(group["zones"]),
                "Select": False,
            }
            for group_id, group in data["zone_groups"].items()
        ])
        selected_group = st.data_editor(
            groups_df,
            column_config={
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Member Count": st.column_config.NumberColumn("Members", width="small"),
                "ID": st.column_config.TextColumn("ID", width="small", disabled=True),
                "Select": st.column_config.CheckboxColumn("Select", width="small"),
            },
            hide_index=True,
            disabled=["Name", "Member Count", "ID"],
            key="group_selection"
        )
        # Get selected group
        selected_group_id = None
        if not selected_group[selected_group["Select"]].empty:
            selected_group_id = selected_group[selected_group["Select"]].iloc[0]["ID"]
    

    if selected_group_id:
        group = data["zone_groups"][selected_group_id]
        current_zones = group["zones"]
        
        col1, col2 = st.columns([1,3])  
        with col1:
            st.write("### Delete Zone Group:")
        with col2:
            if selected_group_id:  # Only show if a group is selected
                group_name = data["zone_groups"][selected_group_id]["name"]
                
                if st.button(f"Delete Zone Group '{group_name}'", type="primary"):
                    # Check if group has members
                    if data["zone_groups"][selected_group_id]["zones"]:
                        st.error(f"Cannot delete '{group_name}': Please remove all zones from this group first")
                        st.info(f"Current zones in group: {len(data['zone_groups'][selected_group_id]['zones'])}")
                    else:
                        del data["zone_groups"][selected_group_id]
                        save_zonegroup(data)

                        callback_logging(f"Deleted zone group '{group_name}'")
                        st.success(f"Zone Group '{group_name}' deleted successfully!")
                        st.rerun()

        cols1 , cols2 = st.columns(2)
        with cols1:
            st.write(f"#### Members of {group['name']}")
            if not current_zones:
                st.info("No zones in this group")
            else:
                current_zones_df = pd.DataFrame([
                    {
                        "ID": zone_id,
                        "Name": zone_data["active_zones"].get(zone_id, {}).get("name") or 
                            zone_data["inactive_zones"].get(zone_id, {}).get("name"),
                        "Select": False,
                    }
                    for zone_id in current_zones
                ])
                
                edited_current = st.data_editor(
                    current_zones_df,
                    column_config={
                        "ID": st.column_config.TextColumn("ID", width="small"),
                        "Name": st.column_config.TextColumn("Name", width="medium"),
                        "Select": st.column_config.CheckboxColumn("Select", width="small"),
                    },
                    hide_index=True,
                    disabled=["ID", "Name"],
                    key=f"current_{selected_group_id}"
                )
                
                if st.button("➖ Remove Selected", key=f"remove_{selected_group_id}"):
                    zones_to_remove = edited_current[edited_current["Select"]]["ID"].tolist()
                    group["zones"] = [z for z in current_zones if z not in zones_to_remove]
                    save_zonegroup(data)
                    from .config_manager import update_zone_config
                    update_zone_config()
                    callback_logging(f"Removed zones from {group['name']}")
                    st.rerun()

        with cols2:
            st.write("#### Available Zones")
            grouped_zones = {z for g in data["zone_groups"].values() for z in g["zones"]}
            available_zones = {
                k: v for k, v in {**zone_data["active_zones"], **zone_data["inactive_zones"]}.items()
                if k not in grouped_zones
            }
            if not available_zones:
                st.info("No available zones to add")
            else:
                available_zones_df = pd.DataFrame([
                    {
                        "ID": zone_id,
                        "Name": zone["name"],
                        "Select": False
                    }
                    for zone_id, zone in available_zones.items()
                ])
                edited_available = st.data_editor(
                    available_zones_df,
                    column_config={
                        "ID": st.column_config.TextColumn("ID", width="small"),
                        "Name": st.column_config.TextColumn("Name", width="medium"),
                        "Select": st.column_config.CheckboxColumn("Select", width="small"),
                    },
                    hide_index=True,
                    disabled=["ID", "Name"],
                    key=f"available_{selected_group_id}"
                )
                if st.button("➕ Add Selected", key=f"add_{selected_group_id}"):
                    zones_to_add = edited_available[edited_available["Select"]]["ID"].tolist()
                    data["zone_groups"][selected_group_id]["zones"].extend(zones_to_add)
                    save_zonegroup(data)
                    from .config_manager import update_zone_config
                    update_zone_config()
                    callback_logging(f"Added zones to {group['name']}")
                    st.rerun()

   
if __name__ == "__main__":
    CreateZoneGroup(st.write)
    ZoneGroupManager(st.write)

    # group_names = {v["name"]: k for k, v in data["zone_groups"].items()}
    # group_to_delete = st.selectbox(
    #     "Select a Zone Group to Delete", 
    #     list(group_names.keys()),
    #     key="delete_group_select"
    # ) if group_names else None

    # if group_to_delete:
    #     group_id = group_names[group_to_delete]
    #     group = data["zone_groups"][group_id]
        
    #     if st.button("Delete Zone Group", key="delete_group_btn"):
    #         # Check if group has zones
    #         if group["zones"]:
    #             st.error(f"Cannot delete group '{group_to_delete}': It contains {len(group['zones'])} zone(s)")
    #             st.info("Please remove all zones from the group before deletion")

    #         else:
    #             del data["zone_groups"][group_id]
    #             save_zonegroup(data)
                        
    #             from .config_manager import update_zone_config
    #             update_zone_config()

    #             callback_logging(f"Deleted zone group {group_to_delete}")
    #             st.success(f"Zone Group '{group_to_delete}' deleted!")
    #             st.toast(f"Zone Group '{group_to_delete}' deleted successfully!", icon="✅")
    #             st.session_state.confirm_group_delete = False
    #             time.sleep(1)
    #             st.rerun()
               
    # else:
    #     st.warning("Please select a group to delete.")
                   


# def ZoneGroupManager(callback_logging):
#     st.write("### Zone Group Manager")
#     data = load_zonegroup()
#     zone_data = load_data()  

#     group_names = {v["name"]: k for k, v in data["zone_groups"].items()}
#     selected_group_name = st.selectbox("Select a Zone Group", list(group_names.keys()))
#     if selected_group_name:
#         group_id = group_names[selected_group_name]
#         group = data["zone_groups"][group_id]
#         current_zones = group["zones"]

#         # Prepare available zones (not in any group)
#         grouped_zones = {z for g in data["zone_groups"].values() for z in g["zones"]}
#         all_zones = {**zone_data["active_zones"], **zone_data["inactive_zones"]}
#         ungrouped_zones = {k: v for k, v in all_zones.items() if k not in grouped_zones}

#         col1, col2 = st.columns(2)

#         with col1:
#             st.write("##### Remove Zones from Group")
#             zones_to_remove = st.multiselect(
#                 "Zones in this Group",
#                 options=current_zones,
#                 format_func=lambda z: all_zones.get(z, {}).get("name", z)
#             )
#             st.table([{"Zone ID": z_id,
#                     "Name": zone_data["active_zones"].get(z_id, {}).get("name") or 
#                     zone_data["inactive_zones"].get(z_id, {}).get("name")}
#                   for z_id in current_zones])

#             if st.button("Remove", key="remove_zones"):
#                 for zone_id in zones_to_remove:
#                     # Move zone to inactive when removed from group
#                     if zone_id in zone_data["active_zones"]:
#                         zone_data["inactive_zones"][zone_id] = zone_data["active_zones"].pop(zone_id)
#                         callback_logging(f"Zone {zone_id} deactivated (removed from group)")
                
#                 group["zones"] = [z for z in current_zones if z not in zones_to_remove]
#                 data["zone_groups"][group_id] = group
#                 save_zonegroup(data)
#                 from .activate_zone import save_zones
#                 save_zones(zone_data)
#                 from .config_manager import update_zone_config
#                 update_zone_config()
#                 if 'zones' in st.session_state:
#                     del st.session_state['zones']

#                 time.sleep(1)
#                 st.rerun()
            
#         with col2:
#             st.write("##### Add Zones to Group")
#             zones_to_add = st.multiselect(
#                 "Available Zones",
#                 options=ungrouped_zones.keys(),
#                 format_func=lambda z: ungrouped_zones[z].get("name", z)
#             )
            
#             st.table([{"Zone ID": z_id,
#                     "Name": zone_data["active_zones"].get(z_id, {}).get("name") or
#                     zone_data["inactive_zones"].get(z_id, {}).get("name")}
#                     for z_id in ungrouped_zones.keys()])
            
#             if st.button("Add", key="add_zones"):
#                 for zone_id in zones_to_add:
#                     # Move zone to active when added to group
#                     if zone_id in zone_data["inactive_zones"]:
#                         zone_data["active_zones"][zone_id] = zone_data["inactive_zones"].pop(zone_id)
#                         callback_logging(f"Zone {zone_id} activated (added to group)")
                
#                 group["zones"].extend([z for z in zones_to_add if z not in group["zones"]])
#                 data["zone_groups"][group_id] = group

#                 save_zonegroup(data)
#                 from .activate_zone import save_zones
#                 save_zones(zone_data)
#                 from .config_manager import update_zone_config
#                 update_zone_config()

#                 if 'zones' in st.session_state:
#                     del st.session_state['zones']

#                 time.sleep(1)
#                 st.rerun()