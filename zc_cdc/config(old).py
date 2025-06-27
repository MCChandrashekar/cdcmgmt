import streamlit as st
from .activate_zone import CreateActivateZone, load_data, save_zones,fetch_zones_from_api, create_zone_api, delete_zone_api
from .aliases import Alias2ZoneLink , load_alias , save_alias_data, refresh_data
from .zonegroup import CreateZoneGroup , ZoneGroupManager
from datetime import datetime
import pandas as pd
import json
from .config_manager import update_zone_config, ZONE_CONFIG_PATH
import requests


# st.set_page_config(layout="wide")

def add_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {message}")

def create_legend():
    """Create a legend with colored boxes and labels"""
    legend_html = '''
    <style>
        .legend-container {
            display: flex;
            gap: 40px;
            margin: 10px 0;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .color-box {
            width: 40px;
            height: 20px;
            border: 1px solid #ccc;
        }
    </style>
    <div class="legend-container">
        <div class="legend-item">
            <div class="color-box" style="background-color: #A1E6C1"></div>
            <span>Hosts</span>
        </div>
        <div class="legend-item">
            <div class="color-box" style="background-color: #DEFBEB"></div>
            <span>Host-Ports</span>
        </div>
        <div class="legend-item">
            <div class="color-box" style="background-color: #9E9EF3"></div>
            <span>Controllers</span>
        </div>
        <div class="legend-item">
            <div class="color-box" style="background-color: #D8D8FA"></div>
            <span>Subsystems</span>
        </div>
    </div>
    '''
    return legend_html

if 'logs' not in st.session_state:
        st.session_state.logs = []

def load_registered_nodes():
    try:
        with open('zc_cdc/data/nodes.json', 'r') as f:
            data = json.load(f)
        return data['nodes']  # Assuming 'nodes' is the key for your list
    except FileNotFoundError:
        st.error("data/nodes.json not found!")
        return []
    except json.JSONDecodeError:
        st.error("Error decoding registered_nodes.json. Check the file.")
        return []

def save_registered_nodes(nodes_data):
    with open('zc_cdc/data/nodes.json', 'w') as f:
        json.dump({'nodes': nodes_data}, f, indent=4)


def handle_edit(edited_df):
    """Handle changes in the editable table"""
    main_df = st.session_state.current_df.copy()
    main_df['Alias'] = edited_df['Alias']
    main_df['Create a Zone'] = edited_df['Create a Zone']
    main_df['Activate'] = edited_df['Activate']
    
    alias_data = load_alias()
    new_aliases = main_df[main_df['Alias'] != '']['Alias'].tolist()
    
    # Check for duplicates in the current edit
    if len(new_aliases) != len(set(new_aliases)):
        st.error("Duplicate alias names in the table!")
        return
    
    if not main_df.equals(st.session_state.current_df):
        st.session_state.current_df = main_df
        # Save changes to the JSON file
        nodes_data = main_df.to_dict(orient='records')
        save_registered_nodes(nodes_data)

        update_aliases_and_zones_from_nodes(nodes_data)
        refresh_data() 
        st.session_state['zones'] = load_data() # Refresh zones data
        update_zone_config()
        st.rerun() 
        # return True
    return False

def update_aliases_and_zones_from_nodes(nodes_data):
    # Load current alias and zone data
    alias_data = load_alias()
    zone_data = load_data()
    
    # Create mappings for existing zones by name
    existing_zones_by_name = {}
    for zone_id, zone in {**zone_data["active_zones"], **zone_data["inactive_zones"]}.items():
        existing_zones_by_name[zone["name"]] = zone_id
    
    # Process each node to update aliases and zones
    new_member_aliases = {}
    new_free_aliases = {}
    
    for node in nodes_data:
        alias_name = node.get("Alias", "")
        zone_name = node.get("Create a Zone", "")
        is_active = node.get("Activate", False)
        
        if alias_name:
            alias_id = str(node.get("Row"))
            alias_info = {
                "name": alias_name,
                "type": node.get("DevType", ""),
                "ip": node.get("IPAddress", ""),
                "nqn": node.get("NQN", "")
            }
            
            if zone_name:
                # Handle zone creation/update if needed
                if zone_name not in existing_zones_by_name:
                    # Create new zone
                    all_keys = list(zone_data["active_zones"].keys()) + list(zone_data["inactive_zones"].keys())
                    new_id = str(max(map(int, all_keys)) + 1) if all_keys else "1"
                    zone_data["inactive_zones"][new_id] = {"name": zone_name, "aliases": {}}
                    existing_zones_by_name[zone_name] = new_id
                
                zone_id = existing_zones_by_name[zone_name]
                
                # Move zone between active/inactive based on activation state
                if is_active:
                    if zone_id in zone_data["inactive_zones"]:
                        zone_data["active_zones"][zone_id] = zone_data["inactive_zones"].pop(zone_id)
                else:
                    if zone_id in zone_data["active_zones"]:
                        zone_data["inactive_zones"][zone_id] = zone_data["active_zones"].pop(zone_id)

                # Add alias to member aliases and zone
                new_member_aliases[alias_id] = alias_info
                zone = zone_data["active_zones"].get(zone_id) or zone_data["inactive_zones"].get(zone_id)
                if zone:
                    if "aliases" not in zone:
                        zone["aliases"] = {}
                    zone["aliases"][alias_id] = alias_info
            else:
                # No zone assigned - add to free aliases
                new_free_aliases[alias_id] = alias_info
    
    # Update alias data
    alias_data["member_aliases"] = new_member_aliases
    alias_data["free_aliases"] = new_free_aliases
    
    # Clean up empty zones
    for zone_id in list(zone_data["active_zones"].keys()):
        if not zone_data["active_zones"][zone_id].get("aliases"):
            zone_data["inactive_zones"][zone_id] = zone_data["active_zones"].pop(zone_id)
    
    # Save updated data files
    save_alias_data(alias_data)
    save_zones(zone_data)
    st.session_state['aliases'] = alias_data
    st.session_state['zones'] = zone_data


def color_rows(df):
    """Creates a color mask based on DevType"""
    colors = pd.DataFrame('', index=df.index, columns=df.columns)    

    # Define color schemes
    color_map = {
        'Host': 'background-color: #A1E6C1; color: black',
        'Host-Port': 'background-color: #DEFBEB; color: black',
        'Controller': 'background-color: #9E9EF3; color: black',
        'Subsystem': 'background-color: #D8D8FA; color: black'
    }

    # Apply colors based on Type
    for idx in df.index:
        dev_type = df.loc[idx,'DevType']
        colors.iloc[idx, :] = color_map.get(dev_type, '')
    
    return colors

def style_nvme_table(df):
    """Apply styling to the NVMe configuration table"""
    display_cols = ['Row', 'IPAddress', 'NQN', 'Alias']
    for col in display_cols:
        if col not in df.columns:
            df[col] = '' if col != 'Row' else range(1, len(df) + 1)
    styled_df = df[display_cols].style
    
    # Apply the color styling
    styled_df = styled_df.apply(lambda _: color_rows(df)[display_cols], axis=None)
    
    # Set fixed column widths using px values
    styled_df = styled_df.set_table_styles([
        {'selector': f'td:nth-child(1)', 'props': [('width', '40px'), ('max-width', '40px'), ('min-width', '40px')]},  # Row
        {'selector': f'td:nth-child(2)', 'props': [('width', '208px'), ('max-width', '208px'), ('min-width', '208px')]},  # IPAddress (26 chars)
        {'selector': f'td:nth-child(3)', 'props': [('width', 'auto')]},  # NQN (flexible)
        {'selector': f'td:nth-child(4)', 'props': [('width', '256px'), ('max-width', '256px'), ('min-width', '256px')]},  # Alias (32 chars)
    ])
    
    styled_df = styled_df.set_properties(**{
    'font-size': '14px',
    'border': '1px solid #ddd'
}).set_table_styles([{
    'selector': 'tr:hover',
    'props': [('background-color', '#f5f5f5')]
}])
    return styled_df

def nodes_config():
    st.markdown(" **LEGEND** : " + create_legend(), unsafe_allow_html=True)

    registered_nodes = load_registered_nodes()
    df = pd.DataFrame(registered_nodes)
    df['Row'] = range(1, len(df) + 1)
    if 'Activate' not in df.columns:
        df['Activate'] = False
    df['Activate'] = df['Activate'].astype(bool)

    # Initialize session state if not already
    if 'current_df' not in st.session_state:
        st.session_state.current_df = df.copy()

    required_columns = ['Row', 'Alias', 'Create a Zone', 'Activate']
    for col in required_columns:
        if col not in st.session_state.current_df.columns:
            st.session_state.current_df[col] = ""

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("### Registered Hosts and Controllers")
        styled_df = style_nvme_table(st.session_state.current_df)
        st.dataframe(styled_df, hide_index=True, use_container_width=True)

    with col2:
        st.markdown("### Configure an alias, add to a created zone, activate")

        # Safe edit copy
        edit_df = st.session_state.current_df[required_columns].copy()

        # Load zones from activate_zone.py
        zones_data = fetch_zones_from_api()
        # Use .get with default empty dicts to avoid KeyError
        active_zones = zones_data.get('active_zones', {})
        inactive_zones = zones_data.get('inactive_zones', {})
        available_zones = list(active_zones.values()) + list(inactive_zones.values())

        edited_df = st.data_editor(
                edit_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Row": st.column_config.NumberColumn("Row#", help="Corresponding row", width="small", disabled=True),
                    "Alias": st.column_config.TextColumn("Alias", help="Name for the device", width="small", max_chars=32),
                    "Create a Zone": st.column_config.TextColumn("New Zone Name", help="Zone to create", width="small", required=False),
                    "Activate": st.column_config.CheckboxColumn( 'Activate', help="Add Zone to ZoneGroup", width='small', default=False)
                }
            )
    if handle_edit(edited_df):
        st.rerun()
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'current_df' not in st.session_state:
        st.session_state.current_df = pd.DataFrame(load_registered_nodes())
    
        # Delete Alias
    st.write("##### Delete Alias")
    alias_to_delete = st.selectbox(
            "Select Alias to Delete",
            options=[node["Alias"] for node in st.session_state.current_df.to_dict("records") if node["Alias"]],
            key="delete_alias"
        )
        
    if st.button("Delete Alias", type="primary"):
        df = st.session_state.current_df
        df.loc[df["Alias"] == alias_to_delete, ["Alias", "Create a Zone", "Activate"]] = ["", "", False]
        save_registered_nodes(df.to_dict("records"))
        update_aliases_and_zones_from_nodes(df.to_dict("records"))
        st.success(f"Alias '{alias_to_delete}' deleted")
        st.rerun()
        
# def generate_zone_config():
#     # Load all data
#     with open("data/zonegroup_data.json") as f:
#         zonegroup_data = json.load(f)
#     with open("data/zones_data.json") as f:
#         zones_data = json.load(f)

#     config = {"active": [], "inactive": []}
#     for group_id, group in zonegroup_data["zone_groups"].items():
#         group_status = "active" if group.get("active", False) else "inactive"
#         group_entry = {
#             "ZoneGrpId": int(group_id),
#             "ZoneGrpName": group["name"],
#             "zoneCount": len(group["zones"]),
#             "ZoneMembers": []
#         }
#         for zone_id in group["zones"]:
#             zone = zones_data.get("active_zones", {}).get(zone_id) 
#             if not zone:
#                 zone = zones_data.get("inactive_zones", {}).get(zone_id)
#             if zone:
#                 aliases = zone.get("aliases", {})
#                 alias_members = []
#                 for alias_id, alias in aliases.items():
#                     alias_members.append({
#                         "AliasId": int(alias_id),
#                         "AliasName": alias["name"],
#                         "Type": alias.get("type", ""),
#                         "IPAddress": alias.get("ip", ""),
#                         "NQN": alias.get("nqn", "")
#                     })
#                 group_entry["ZoneMembers"].append({
#                     "ZoneId": int(zone_id),
#                     "ZoneName": zone["name"],
#                     "aliasCount": len(alias_members),
#                     "AliasMembers": alias_members
#                 })
#         config[group_status].append(group_entry)
#     return config

def main():
    st.title(" Zone Configuration")

    # if st.button("Show Current Zone Config"):
    #     config = generate_zone_config()
    #     st.json(config)
    # st.markdown("----")
    nodes_config()
    create_legend()
    # referesh button
    # if st.button("Refresh data"):
    #     st.session_state.current_df = pd.DataFrame(load_registered_nodes())
    #     st.session_state['aliases'] = load_alias()
    #     st.session_state['zones'] = load_data()
    #     st.rerun()
    st.divider()
    st.subheader("Zone Creation & Activation")
    CreateActivateZone(callback_logging=add_log)

    st.divider()
    st.subheader("Alias to Zone Linking")
    Alias2ZoneLink(callback_logging=add_log)

    st.divider()
    st.subheader("Zone Groups")
    CreateZoneGroup(callback_logging=add_log)
    ZoneGroupManager(callback_logging=add_log)
    st.divider()

    with st.expander("Console Logs", expanded=False):
        for log in reversed(st.session_state.logs):
            st.text(log)


if __name__ == "__main__":
    main()


