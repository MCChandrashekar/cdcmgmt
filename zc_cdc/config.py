#zc_cdc/config.py
import streamlit as st
from .activate_zone import CreateActivateZone
from .aliases import refresh_data
from .zonegroup import CreateZoneGroup , ZoneGroupManager
from .data_utils import load_zones, save_zones, load_alias, save_alias, load_registered_nodes, save_registered_nodes
from datetime import datetime
import pandas as pd
import json
from .config_manager import remove_alias_from_all_zones , update_zone_config


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

# def load_registered_nodes():
#     try:
#         with open('../CDCMgmt/data/nodes.json', 'r') as f:
#             data = json.load(f)
#         return data['nodes']  # Assuming 'nodes' is the key for your list
#     except FileNotFoundError:
#         st.error("data/nodes.json not found!")
#         return []
#     except json.JSONDecodeError:
#         st.error("Error decoding registered_nodes.json. Check the file.")
#         return []

# def save_registered_nodes(nodes_data):
#     with open('../CDCMgmt/data/nodes.json', 'w') as f:
#         json.dump({'nodes': nodes_data}, f, indent=4)


def handle_edit(edited_df):
    """Handle changes in the editable table"""
    main_df = st.session_state.current_df.copy()
    main_df['Alias'] = edited_df['Alias']
 
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

        update_aliases_from_nodes(nodes_data)
        refresh_data() 
        st.rerun() 
    return False

def update_aliases_from_nodes(nodes_data):
    # Load current alias and zone data
    alias_data = load_alias()
    new_free_aliases = {}
    for node in nodes_data:
        if node.get("Alias"):
            alias_id = str(node.get("Row"))
            alias_data["free_aliases"][alias_id] = {
                    "name": node["Alias"],
                    "type": node.get("DevType", ""),
                    "ip": node.get("IPAddress", ""),
                    "nqn": node.get("NQN", "")
            }
    save_alias(alias_data)
    st.session_state['aliases'] = alias_data

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

    # Initialize session state if not already
    if 'current_df' not in st.session_state:
        st.session_state.current_df = df.copy()

    required_columns = ['Row', 'Alias','Delete']
    for col in required_columns:
        if col not in st.session_state.current_df.columns:
            st.session_state.current_df[col] = ""

    col1, col2 = st.columns([1.5, 0.5])
    with col1:
        st.markdown("### Registered Hosts and Controllers")
        styled_df = style_nvme_table(st.session_state.current_df)
        st.dataframe(styled_df, hide_index=True, use_container_width=True)

    with col2:
        st.markdown("### Configure Alias")
        edit_df = st.session_state.current_df[required_columns].copy()
        edit_df['Delete'] = False
        edited_df = st.data_editor(
                edit_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Row": st.column_config.NumberColumn("Row#", help="Corresponding row", width="small", disabled=True),
                    "Alias": st.column_config.TextColumn("Alias", help="Name for the device", width="small", max_chars=32),
                    "Delete": st.column_config.CheckboxColumn("Delete", width="small")
                },key = "alias_editor"
            )
         # Delete selected alias
        selected_alias = None
        if not edited_df[edited_df['Delete']].empty:
            selected_alias = edited_df[edited_df['Delete']].iloc[0]['Alias']

        # Delete button (only shows when an alias is selected)
        if selected_alias:
            if st.button("🗑️ Delete Alias", type="primary"):
                with st.status(f"Deleting {selected_alias}..."):
                        # 1. Remove alias from all zones
                        zone_data = load_zones()
                        for zone_dict in [zone_data["active_zones"], zone_data["inactive_zones"]]:
                            for zid, zobj in zone_dict.items():
                                aliases = zobj.get("aliases", {})
                                # Find alias ID by name
                                to_remove = [k for k, v in aliases.items() if v["name"] == selected_alias]
                                for k in to_remove:
                                    aliases.pop(k, None)
                        save_zones(zone_data)
                        # 2. Remove from alias data
                        alias_data = load_alias()
                        alias_data["member_aliases"] = {
                            k: v for k, v in alias_data["member_aliases"].items() 
                            if v["name"] != selected_alias
                        }
                        alias_data["free_aliases"] = {
                            k: v for k, v in alias_data["free_aliases"].items() 
                            if v["name"] != selected_alias}
                        save_alias(alias_data)

                        # 3. Remove from DataFrame
                        st.session_state.current_df.loc[
                            st.session_state.current_df['Alias'] == selected_alias, 'Alias'] = ""
                        save_registered_nodes(st.session_state.current_df.to_dict("records"))
                        remove_alias_from_all_zones(selected_alias)
                        update_zone_config()
                        update_aliases_from_nodes(st.session_state.current_df.to_dict("records"))
                        
                        st.success(f"Alias '{selected_alias}' deleted!")
                        st.rerun()

        if not edited_df[['Row', 'Alias']].equals(edit_df[['Row', 'Alias']]):
            with st.status("Saving changes..."):
                st.session_state.current_df['Alias'] = edited_df['Alias']
                update_zone_config()
                save_registered_nodes(st.session_state.current_df.to_dict("records"))
                update_aliases_from_nodes(st.session_state.current_df.to_dict("records"))
                st.rerun()

    
def main():
    if "logs" not in st.session_state:
        st.session_state["logs"] = []

    st.title(" Zone Configuration")
    tabs = st.tabs([" 1.Alias", "2.Zone","3.Zone Group"])
    with tabs[0]:
        st.header("🖊Alias Management")
        nodes_config()
        create_legend()

    with tabs[1]:
        st.header("🗃Zone Configuration")
        CreateActivateZone(callback_logging=add_log)

    with tabs[2]:
        st.header("🗂️ Zone Group Management")
        CreateZoneGroup(callback_logging=add_log)
        ZoneGroupManager(callback_logging=add_log)
    
    with st.expander("Console Logs", expanded=False):
        for log in reversed(st.session_state.logs):
            st.text(log)

if __name__ == "__main__":
    main()





    # st.markdown("### Delete Alias")
    # if not st.session_state.current_df['Alias'].any():
    #     st.info("No aliases to delete")
    # else:
    #     alias_to_delete = st.selectbox("Select Alias to Delete", 
    #                                     options=st.session_state.current_df['Alias'].unique().tolist(),
    #                                     help="Select an alias to delete from the system")
    #     member_alias_dict = {v["name"]: k for k, v in alias_data["member_aliases"].items()}
    #     alias_data = load_alias()
    #     if st.button("Delete Alias", type="primary"):
    #         alias_id = member_alias_dict.get(alias_to_delete)
    #         if not alias_id:
    #             st.error(f"Alias '{alias_to_delete}' not found.")
    #             return
    #         with st.status("Deleting alias..."):
    #             # 1. Remove alias from all zones
    #             zone_data = load_data()
    #             for zone_dict in [zone_data["active_zones"], zone_data["inactive_zones"]]:
    #                 for zid, zobj in zone_dict.items():
    #                     zobj.get("aliases", {}).pop(alias_id, None)
    #             save_zones(zone_data)

    #             # 2. Remove from alias data
    #             alias_data = load_alias()
    #             alias_data["member_aliases"].pop(alias_id, None)
    #             alias_data["free_aliases"].pop(alias_id, None)
    #             save_alias_data(alias_data)

    #             # 3. Remove from DataFrame
    #             df = st.session_state.current_df
    #             df.loc[df["Alias"] == alias_to_delete, "Alias"] = ""
    #             save_registered_nodes(df.to_dict("records"))
    #             update_aliases_from_nodes(df.to_dict("records"))

    #             st.success(f"Alias '{alias_to_delete}' deleted from system.")
    #             st.rerun()