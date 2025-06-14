import streamlit as st
import json
import re
import time
from .activate_zone import load_data
import requests





def load_zonegroup():
    try:
        with open("../CDCMgmt/data/zonegroup_data.json", "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"zone_groups": {}}
def save_zonegroup(zonegroup_data):
    with open("../CDCMgmt/data/zonegroup_data.json", "w") as file:
        json.dump(zonegroup_data, file, indent=4)

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
    group_name = st.text_input("Enter Zone Group Name")

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
    st.write("### Zone Group Manager")

    data = load_zonegroup()
    zone_data = load_data()  # active + inactive zones

    group_names = {v["name"]: k for k, v in data["zone_groups"].items()}
    selected_group_name = st.selectbox("Select a Zone Group", list(group_names.keys()))

    if selected_group_name:
        group_id = group_names[selected_group_name]
        group = data["zone_groups"][group_id]
        current_zones = group["zones"]

        # Prepare available zones (not in any group)
        grouped_zones = {z for g in data["zone_groups"].values() for z in g["zones"]}
        all_active_zones = {k: v["name"] for k, v in zone_data["active_zones"].items()}
        ungrouped_zones = {k: v for k, v in all_active_zones.items() if k not in grouped_zones}

        col1, col2 = st.columns(2)

        with col1:
            st.write("##### Remove Zones from Group")
            zones_to_remove = st.multiselect(
                "Zones in this Group",
                options=current_zones,
                format_func=lambda z: all_active_zones.get(z, z)
            )
            st.table([{"Zone ID": z_id,
                    "Name": zone_data["active_zones"].get(z_id, {}).get("name") or 
                    zone_data["inactive_zones"].get(z_id, {}).get("name")}
                  for z_id in current_zones])
            if st.button("Remove", key="remove_zones"):
                group["zones"] = [z for z in current_zones if z not in zones_to_remove]
                data["zone_groups"][group_id] = group
                save_zonegroup(data)
                from .config_manager import update_zone_config  # 👈 local import here
                update_zone_config()
                callback_logging(f"Removed zones {zones_to_remove} from group {selected_group_name}")
                time.sleep(1)
                st.rerun()
            
        with col2:
            st.write("##### Add Zones to Group")
            zones_to_add = st.multiselect(
                "Available Zones",
                options=ungrouped_zones.keys(),
                format_func=lambda z: ungrouped_zones[z]
            )
            st.table([{"Zone ID": z_id,
                    "Name": zone_data["active_zones"].get(z_id, {}).get("name") or
                    zone_data["inactive_zones"].get(z_id, {}).get("name")}
                    for z_id in ungrouped_zones.keys()])
            if st.button("Add", key="add_zones"):
                group["zones"].extend([z for z in zones_to_add if z not in group["zones"]])
                data["zone_groups"][group_id] = group
                save_zonegroup(data)
                from .config_manager import update_zone_config  # 👈 local import here
                update_zone_config()

                callback_logging(f"Added zones {zones_to_add} to group {selected_group_name}")
                time.sleep(1)
                st.rerun()
    st.write("##### Delete Zone Group")
    group_names = {v["name"]: k for k, v in data["zone_groups"].items()}
    group_to_delete = st.selectbox("Select a Zone Group to Delete", list(group_names.keys())) if group_names else None
    if st.button("Delete Zone Group"):
        if group_to_delete:
            group_id = group_names[group_to_delete]
            resp = requests.delete(f"http://localhost:5001/cdc/api/v1/zgrp/{group_to_delete}")
            if resp.status_code != 200:
                st.error(resp.json().get("error", "Failed to delete zone group"))
                return

            from .config_manager import update_zone_config  # 👈 local import here
            update_zone_config()

            callback_logging(f"Deleted zone group {group_to_delete}")
            st.success(f"Zone Group '{group_to_delete}' deleted!")
            st.toast(f"Zone Group '{group_to_delete}' deleted successfully!", icon="✅")
            time.sleep(1) 
            st.rerun()
        else:
            st.warning("Please select a group to delete.")

if __name__ == "__main__":
    CreateZoneGroup(st.write)
    ZoneGroupManager(st.write)
