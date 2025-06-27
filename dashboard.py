#dashboard.py
import streamlit as st
import json
import os
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh


# Auto-refresh dashboard every 5 seconds
st_autorefresh(interval=5000, key="dashboard_autorefresh")

# Define file paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ZONE_FILE = os.path.join(BASE_DIR, 'data', 'zone_config.json')
ENTITY_FILE = os.path.join(BASE_DIR, 'data', 'regd_nodes2.json')
STORAGE_FILE = os.path.join(BASE_DIR, 'data', 'end_nodes.json')
ZONEGROUP_FILE = os.path.join(BASE_DIR, 'data', 'zonegroup_data.json')

# Unified JSON file loader
def load_json_file(filepath):
    try:
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return json.load(f)
        return {}
    except json.JSONDecodeError:
        st.error(f"🚨 Error decoding {filepath}. Using empty data.")
        return {}

# Compute dashboard metrics
def compute_snapshot():
    zone_data = load_json_file(ZONE_FILE)
    regd_data = load_json_file(ENTITY_FILE)
    storage_data = load_json_file(STORAGE_FILE)
    zonegroup_data = load_json_file(ZONEGROUP_FILE)

    active_zones = []
    for group in zone_data.get("active", []):
        active_zones.extend(group.get("ZoneMembers", []))
    inactive_zones = []
    for group in zone_data.get("inactive", []):
        inactive_zones.extend(group.get("ZoneMembers", []))
    total_zones = len(active_zones) + len(inactive_zones)
    active_zone_count = len(active_zones)
    inactive_zone_count = len(inactive_zones)

    empty_zones = sum(1 for z in active_zones + inactive_zones if z.get("aliasCount", 0) == 0)
    one_member_zones = sum(1 for z in active_zones + inactive_zones if z.get("aliasCount", 0) == 1)
    two_member_zones = sum(1 for z in active_zones + inactive_zones if z.get("aliasCount", 0) == 2)
    more_member_zones = sum(1 for z in active_zones + inactive_zones if z.get("aliasCount", 0) > 2)

    total_aliases = sum(z.get("aliasCount", 0) for z in active_zones + inactive_zones)
    host_aliases = 0
    storage_aliases = 0
    for zone in active_zones + inactive_zones:
        for alias in zone.get("AliasMembers", []):
            if alias.get("Type") == "Host":
                host_aliases += 1
            elif alias.get("Type") == "Storage":
                storage_aliases += 1

    entities = regd_data.get("data", {}).get("entities", [])
    total_entities = len(entities)
    total_portals = sum(e.get("portal_count", 0) for e in entities)
    host_entities = [e for e in entities if e.get("entity_type") == "NVMe Host"]
    one_port_hosts = sum(1 for e in host_entities if e.get("portal_count", 0) == 1)
    two_port_hosts = sum(1 for e in host_entities if e.get("portal_count", 0) == 2)
    three_port_hosts = sum(1 for e in host_entities if e.get("portal_count", 0) == 3)
    more_port_hosts = sum(1 for e in host_entities if e.get("portal_count", 0) > 3)

    portal_ips = []
    for e in entities:
        for p in e.get("portals", []):
            portal_ips.append(p.get("portal_ip"))
    unique_ips = len(set(portal_ips))

    host_count = sum(1 for e in entities if e.get("entity_type") == "NVMe Host")
    controller_count = sum(1 for e in entities if e.get("entity_type") == "NVMe Controller")

    subsystems = 0
    controllers = 0
    arrays = 0
    storage = storage_data.get("storage", {}).get("children", [])
    for array in storage:
        arrays += 1
        for controller in array.get("children", []):
            controllers += 1
            for subsystem in controller.get("children", []):
                subsystems += 1

    zonegroup_count = len(zonegroup_data.get("zone_groups", {}))

    return {
        "Entity": total_entities,
        "Portal": total_portals,
        "UniquePortalIPs": unique_ips,
        "HostCount": host_count,
        "ControllerCount": controller_count,
        "Subsystem": subsystems,
        "Controllers": controllers,
        "Arrays": arrays,
        "Zone": total_zones,
        "ActiveZones": active_zone_count,
        "InactiveZones": inactive_zone_count,
        "ZoneGroup": zonegroup_count,
        "Alias": total_aliases,
        "HostAliases": host_aliases,
        "StorageAliases": storage_aliases,
        "ZoneDistribution": {
            "empty": empty_zones,
            "one_member": one_member_zones,
            "two_members": two_member_zones,
            "more_members": more_member_zones
        },
        "HostPortDistribution": {
            "one_port": one_port_hosts,
            "two_ports": two_port_hosts,
            "three_ports": three_port_hosts,
            "more_ports": more_port_hosts
        }
    }

# Main dashboard display
def cdc_page0_dashboard_text():
    st.title("CDC Dashboard 🌟")
    st.markdown("---")
    
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()


    snapshot = compute_snapshot()

    st.subheader("📌 Snapshot Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Zones", snapshot["Zone"])
        st.metric("Active Zones", snapshot["ActiveZones"])
        st.metric("Inactive Zones", snapshot["InactiveZones"])
        st.metric("Zone Groups", snapshot["ZoneGroup"])
    with col2:
        st.metric("Total Entities", snapshot["Entity"])
        st.metric("Total Portals", snapshot["Portal"])
        st.metric("Unique Portal IPs", snapshot["UniquePortalIPs"])
    with col3:
        st.metric("Total Aliases", snapshot["Alias"])
        st.metric("Host Aliases", snapshot["HostAliases"])
        st.metric("Storage Aliases", snapshot["StorageAliases"])

    st.markdown("---")
    st.subheader("📈 Visual Breakdown")

    col4, col5, col6 = st.columns(3)
    with col4:
        fig1 = go.Figure(data=[
            go.Bar(
                name="Zone Distribution",
                x=["Empty", "1 Member", "2 Members", ">2 Members"],
                y=[
                    snapshot["ZoneDistribution"]["empty"],
                    snapshot["ZoneDistribution"]["one_member"],
                    snapshot["ZoneDistribution"]["two_members"],
                    snapshot["ZoneDistribution"]["more_members"]
                ],
                marker_color=["#FFA07A", "#98FB98", "#87CEEB", "#DDA0DD"]
            )
        ])
        fig1.update_layout(title="Zone Distribution", height=300)
        st.plotly_chart(fig1, use_container_width=True)

    with col5:
        fig2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=snapshot["Zone"],
            title={"text": "Configured Zones"},
            gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#1f77b4"}}
        ))
        fig2.update_layout(height=250)
        st.plotly_chart(fig2, use_container_width=True)

    with col6:
        fig3 = go.Figure(data=[
            go.Pie(
                labels=["1 Port", "2 Ports", "3 Ports", ">3 Ports"],
                values=[
                    snapshot["HostPortDistribution"]["one_port"],
                    snapshot["HostPortDistribution"]["two_ports"],
                    snapshot["HostPortDistribution"]["three_ports"],
                    snapshot["HostPortDistribution"]["more_ports"]
                ]
            )
        ])
        fig3.update_layout(title="Host Port Distribution", height=300)
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Entity Type Breakdown")
    fig4 = go.Figure(data=[
        go.Bar(
            name="Entity Types",
            x=["Hosts", "Controllers"],
            y=[snapshot["HostCount"], snapshot["ControllerCount"]],
            marker_color=["#FF9999", "#66B2FF"]
        )
    ])
    fig4.update_layout(title="Entity Types", height=300)
    st.plotly_chart(fig4, use_container_width=True)

