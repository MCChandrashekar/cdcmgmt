import streamlit as st  

# Sample data
active_zones = {
    "1": {"name": "zone1"},
    "2": {"name": "zone2"},
    "5": {"name": "zone5"},
}
inactive_zones = {
    "3": {"name": "zone3"},
    "4": {"name": "zone4"},
    "9": {"name": "zone9"},
    "8": {"name": "zone8"},
}

def CreateActivateZone(callback_logging):
    st.write("#### Activate, Deactivate Zone")
    
    # Create new zone
    zone_name = st.text_input("Enter zone name")
    if st.button("Create Zone"):
        if zone_name:
            new_id = str(max(map(int, active_zones.keys() | inactive_zones.keys())) + 1)
            inactive_zones[new_id] = {"name": zone_name}
            st.success(f"Zone '{zone_name}' created successfully!")
        else:
            st.error("Please provide a valid zone name.")

    col1, col2 = st.columns(2, vertical_alignment='top')
    
    # Left Column - Active Zones
    with col1:
        st.write("##### Deactivate Zones")
        q1, q2 = st.columns(2, vertical_alignment='bottom')
        with q1:
            active_zone_dict = {v["name"]: k for k, v in active_zones.items()}
            zones_to_deactivate = st.multiselect(
                "Select zones to deactivate",
                options=list(active_zones.values()),
                format_func=lambda x: x["name"]
            )
        
        with q2:
            if st.button("Deactivate", key="deactivate"):
                if zones_to_deactivate:
                    for zone in zones_to_deactivate:
                        zone_id = active_zone_dict[zone["name"]]
                        inactive_zones[zone_id] = active_zones.pop(zone_id)
                        #st.write(f"Zone {zone['name']} has been deactivated")
                        callback_logging(f"Zone {zone['name']} has been deactivated")
                    st.toast(f"Zone {zone['name']} has been deactivated")
                else:
                    st.toast("No zones selected for deactivation", icon="⚠️")
                    
        st.write("##### Active Zones")
        st.table([{"ID": k, "Name": v["name"]} for k, v in active_zones.items()])

    # Right Column - Inactive Zones
    with col2:
        st.write("##### Activate Zones")
        q3, q4 = st.columns(2, vertical_alignment='bottom')
        with q3:
            inactive_zone_dict = {v["name"]: k for k, v in inactive_zones.items()}
            zones_to_activate = st.multiselect(
                "Select zones to activate",
                options=list(inactive_zones.values()),
                format_func=lambda x: x["name"]
            )
            
        with q4:
            if st.button("Activate", key="activate"):
                if zones_to_activate:
                    for zone in zones_to_activate:
                        zone_id = inactive_zone_dict[zone["name"]]
                        active_zones[zone_id] = inactive_zones.pop(zone_id)
                        #st.write(f"Zone {zone['name']} has been activated")
                        callback_logging(f"Zone {zone['name']} has been activated")
                    st.toast(f"Zone {zone['name']} has been activated")
                else:
                    st.toast("No zones selected for activation", icon="⚠️")
                    
        st.write("##### Inactive Zones")
        st.table([{"ID": k, "Name": v["name"]} for k, v in inactive_zones.items()])