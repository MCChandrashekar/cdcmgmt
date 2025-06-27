import streamlit as st
import pandas as pd
from datetime import datetime
from config_zones.activate_zones import CreateActivateZone
from config_zones.zone_members import Alias2ZoneLink

# Set page configuration to wide layout
# st.set_page_config(layout="wide")

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


if 'current_df' not in st.session_state:
    data = {
        'Row': list(range(1, 17)),
        'DevType': [
            'Host', 'Host', 'Host', 'Host',
            'Host-Port', 'Host-Port', 'Host-Port', 'Host-Port', 'Host-Port', 'Host-Port', 
            'Controller', 'Controller',
            'Subsystem', 'Subsystem', 'Subsystem', 'Subsystem' 
        ],
        'IPAddress': [
            '', '', '', '',
            '192.168.1.10', '192.168.1.11', '192.168.1.30', '192.168.1.40', '192.168.1.50', '192.168.1.60',
            '192.168.1.100', '192.168.1.110',
            '192.168.1.100', '192.168.1.100', '192.168.1.100', '192.168.1.110'
        ],
        'NQN': [
            'nqn.2014-08.org.nvmexpress:uuid:host1',
            'nqn.2014-08.org.nvmexpress:uuid:host2',
            'nqn.2014-08.org.nvmexpress:uuid:host3',
            'nqn.2014-08.org.nvmexpress:uuid:host4',
            'nqn.2014-08.org.nvmexpress:uuid:host1-p1',
            'nqn.2014-08.org.nvmexpress:uuid:host1-p2',
            'nqn.2014-08.org.nvmexpress:uuid:host2-p3',
            'nqn.2014-08.org.nvmexpress:uuid:host2-p4',
            'nqn.2014-08.org.nvmexpress:uuid:host3-p5',
            'nqn.2014-08.org.nvmexpress:uuid:host4-p6',
            '', '', 
            'nqn.2014-08.org.nvmexpress:uuid:c0subsys1',
            'nqn.2014-08.org.nvmexpress:uuid:c0subsys2',
            'nqn.2014-08.org.nvmexpress:uuid:c0subsys3',
            'nqn.2014-08.org.nvmexpress:uuid:c1subsys'
        ],
        'Alias': [''] * 16,
        'Create a Zone': [''] * 16,
        'Activate': [''] * 16,
    }
    st.session_state.current_df = pd.DataFrame(data)

############################################
# Initialize state for zone groups

def create_zonegroup():
    st.subheader("Zone Group Configuration")
    if 'zone_group' not in st.session_state:
        new_group = st.text_input("Enter Zone Group Name", key="new_zonegroup")
        if st.button("Create Zone Group"):
            if new_group:
                st.session_state.zone_group = new_group
                st.success(f"Zone Group '{new_group}' created successfully!")
    else:
        st.success(f"Configured Zone Group: '{st.session_state.zone_group}' ")

############################################

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

    # Apply colors based on DevType
    for idx in df.index:
        dev_type = df.loc[idx, 'DevType']
        colors.iloc[idx, :] = color_map.get(dev_type, '')
    
    return colors

def style_nvme_table(df):
    """Apply styling to the NVMe configuration table"""
    display_cols = ['Row', 'IPAddress', 'NQN', 'Alias']
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
    
    # Add cell styling
    styled_df = styled_df.set_properties(**{
        'text-align': 'left',
        'padding': '6px 8px',
        'white-space': 'nowrap',
        'overflow': 'hidden',
        'text-overflow': 'ellipsis'
    })
    return styled_df

def add_log_to_console(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {message}")


def handle_edit(edited_df):
    """Handle changes in the editable table"""
    main_df = st.session_state.current_df.copy()
    main_df['Alias'] = edited_df['Alias']
    main_df['Create a Zone'] = edited_df['Create a Zone']
    main_df['Activate'] = edited_df['Activate']
    
    if not main_df.equals(st.session_state.current_df):
        st.session_state.current_df = main_df
        return True
    return False

def cfg_zgrp_zone_aliases():
    # Display the title
    st.write("## Zone Configuration")

    st.html("""
        <style>
            .streamlit-expanderHeader {
                width: 400px !important;
            }
            .streamlit-expanderContent {
                width: 400px !important;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
        </style>
    """)
    
       
    st.html("""
        <style>
            .stHorizontalBlock {
                align-items: flex-start !important;
            }
            div[data-testid="column"] {
                width: calc(50% - 1rem);
                margin: 0 0.5rem;
            }
        </style>
    """)

    col1, col2 = st.columns([1, 1], vertical_alignment='bottom')
    with col1:
        with st.expander("**Note:**", expanded=True):
            st.write(''' 
                In the tables below, left table lists all the registered nodes\n  
                Nodes are hosts, host-ports, controllers, subsystems\n  
                The right table allows create/edit of alias names on the corresponding row in left table\n  
                Recommended Zone Configuration order:\n  
                    1. Create a Zone Group if not already created\n  
                    2. Provide an alias in 'Alias' column of right table(or edit if it was already provided)\n  
                    3. Use 'New Zone Name' column to create a Zone, Same row alias is automatically added to zone\n
                    4. Activate the new zone by clicking check box in 'Activate' column. This adds to zone group\n  
                    4. Use Create/Edit Zones buttons to add the node to more than one zone\n  
                    5. Check console at the bottom of this page\n  
            '''
            )
        create_zonegroup()
        st.divider()
        st.html("**LEGEND**: "+create_legend())
        st.markdown("### Registered Hosts and Controllers")
        styled_df = style_nvme_table(st.session_state.current_df)
        st.dataframe(styled_df, hide_index=True, use_container_width=True)

    with col2:
        st.markdown("### Configure an alias, add to a created zone, activate")
        edit_df = st.session_state.current_df[['Row', 'Alias', 'Create a Zone', 'Activate']].copy()

        available_zones = ["zone1", "zone2", "zone3", "zone4"]  # Replace with your actual zones

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

    # Initialize logs in session state if not exists
    if 'logs' not in st.session_state:
        st.session_state.logs = []

    # Your main app code
    #st.title("My Streamlit App")

    # Display logs in expander
           
    if handle_edit(edited_df):
        st.rerun()

def configure_aliases_zones():
    cfg_zgrp_zone_aliases()
    st.divider()

    CreateActivateZone(add_log_to_console)
    st.divider()

    Alias2ZoneLink(add_log_to_console)
    st.divider()

    with st.expander("Console Logs", expanded=False):
        # Display logs in reverse order (newest first)
        for log in reversed(st.session_state.logs):
            st.text(log)
 
    # Add some sample logs
    #if st.button("Perform Action"):
    #    add_log_to_console("Action performed")


if __name__=="__main__":
    configure_aliases_zones()