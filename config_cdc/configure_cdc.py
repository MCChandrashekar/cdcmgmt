#config_cdc/configure_cdc.py
import streamlit as st
import json
import os
import ipaddress
from datetime import datetime
import logging
import pandas as pd

cdc_server = "http://localhost:5001"

# Setup logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_dir, "cdc_running.log"),
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Load end_nodes.json
@st.cache_data
def load_end_nodes():
    with open("data/end_nodes.json", "r") as f:
        return json.load(f)

# Load zone configuration
@st.cache_data
def load_zone_config():
    try:
        with open("data/zone_config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("Zone config file not found")
        return {"active": [], "inactive": [], "last_updated": ""}
    except json.JSONDecodeError:
        logging.error("Invalid zone config JSON")
        return {"active": [], "inactive": [], "last_updated": ""}

# Check if IP is valid and belongs to a subnet
def is_in_subnet(ip, subnet):
    try:
        return ipaddress.ip_address(ip) in subnet
    except ValueError:
        logging.warning(f"Invalid IP skipped: {ip}")
        return False

# Extract hosts and subsystems within a subnet
def extract_hosts_and_subsystems(end_nodes, subnet):
    hosts, subsystems = [], []
    for host in end_nodes["hosts"]["children"]:
        for portal in host.get("children", []):
            ip = portal["details"].get("ip")
            if ip and is_in_subnet(ip, subnet):
                hosts.append({"name": host["name"], "nqn": host["nqn"], "ip": ip})
                for conn in portal.get("connections", []):
                    if conn.startswith("nqn.") or is_in_subnet(conn, subnet):
                        subsystems.append({"host": host["name"], "subsystem_nqn": conn})
    return hosts, subsystems

# Save a backup
def save_backup(data, backup_path):
    with open(backup_path, "w") as f:
        json.dump(data, f, indent=4)
    logging.info(f"Backup saved at: {backup_path}")

# Streamlit UI
def main():
    st.title("🔧 CDC Configuration Interface")
    st.subheader("🧩 Interface Management")

    if "interfaces" not in st.session_state:
        st.session_state.interfaces = []

    if "interface_stats" not in st.session_state:
        st.session_state.interface_stats = []

    end_nodes = load_end_nodes()
    interface_input = st.text_input("Enter Interface IP/Subnet (e.g., 192.168.1.10/24)")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("➕ Add Interface"):
            try:
                if interface_input:
                    subnet = ipaddress.IPv4Network(interface_input, strict=False)
                    if interface_input not in st.session_state.interfaces:
                        st.session_state.interfaces.append(interface_input)
                        hosts, subsystems = extract_hosts_and_subsystems(end_nodes, subnet)
                        st.session_state.interface_stats.append({
                            "interface": interface_input,
                            "host_count": len(hosts),
                            "subsystem_count": len(subsystems)
                        })
                        logging.info(f"Interface added: {interface_input}")
                        st.success(f"Interface added: {interface_input}")
                        st.info(f"Eligible Hosts: {len(hosts)} | Eligible Subsystems: {len(subsystems)}")
                    else:
                        st.warning("Interface already exists.")
                else:
                    st.warning("Please enter a valid interface IP with subnet.")
            except ValueError:
                st.error("Invalid interface format. Please use IP/Subnet (e.g., 192.168.1.10/24).")

    with col2:
        if st.session_state.interfaces:
            selected_interface = st.selectbox("Select Interface to Delete", st.session_state.interfaces)
            if st.button("🗑️ Delete Selected Interface"):
                st.session_state.interfaces.remove(selected_interface)
                st.session_state.interface_stats = [
                    stat for stat in st.session_state.interface_stats
                    if stat["interface"] != selected_interface
                ]
                logging.info(f"Interface deleted: {selected_interface}")
                st.success(f"Interface removed: {selected_interface}")
        else:
            st.info("No interfaces to delete.")

    if st.session_state.interfaces:
        st.write("### 📡 Active Interfaces")
        st.table(st.session_state.interfaces)

        st.subheader("📊 Interface Stats")
        df = pd.DataFrame(st.session_state.interface_stats)
        df.columns = ["Interface", "Host", "Subsystem"]
        st.table(df)

        st.subheader("📋 Hosts and Subsystems Detected")
        all_hosts, all_subsystems = [], []
        all_ips = set()

        for interface in st.session_state.interfaces:
            try:
                subnet = ipaddress.IPv4Network(interface, strict=False)
                hosts, subsystems = extract_hosts_and_subsystems(end_nodes, subnet)

                for host in hosts:
                    if host['ip'] not in all_ips:
                        all_hosts.append(host)
                        all_ips.add(host['ip'])

                for subsystem in subsystems:
                    if subsystem['subsystem_nqn'] not in all_ips:
                        all_subsystems.append(subsystem)
                        all_ips.add(subsystem['subsystem_nqn'])

            except Exception as e:
                st.error(f"Error processing interface {interface}: {e}")
                logging.error(f"Error processing interface {interface}: {e}")

        st.success(f"✔ Found {len(all_hosts)} Hosts and {len(all_subsystems)} Subsystems")

        if all_hosts:
            st.write("#### 🖥️ Hosts")
            st.table(all_hosts)

        if all_subsystems:
            st.write("#### 💽 Subsystems")
            st.table(all_subsystems)

    # Backup Section
    st.subheader("💾 Backup Configuration")
    auto_backup = st.checkbox("Enable Auto Backup")

    if auto_backup:
        backup_data = {
            "zone_configuration": load_zone_config(),
            "active_interfaces": st.session_state.interfaces,
            "log_severity": logging.getLevelName(logging.getLogger().level),
            "timestamp": str(datetime.now())
        }
        filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        full_path = os.path.join("backups", filename)
        os.makedirs("backups", exist_ok=True)
        save_backup(backup_data, full_path)
        st.success(f"Auto backup saved as `{filename}` in `backups/`")
    else:
        col1, col2 = st.columns([1, 2])
        with col1:
            manual_filename = st.text_input("Backup File Name (with .json)")
        with col2:
            manual_path = st.text_input("Full Path to Save (e.g., C:/Users/YourName/Documents)")

        if st.button("💾 Save Manual Backup"):
            if not manual_filename.endswith(".json"):
                st.error("Filename must end with `.json`")
            elif not os.path.isdir(manual_path):
                st.error("Directory path does not exist")
            else:
                full_manual_path = os.path.join(manual_path, manual_filename)
                manual_data = {
                    "zone_configuration": load_zone_config(),
                    "active_interfaces": st.session_state.interfaces,
                    "log_severity": logging.getLevelName(logging.getLogger().level),
                    "timestamp": str(datetime.now())
                }
                save_backup(manual_data, full_manual_path)
                st.success(f"Manual backup saved to: {full_manual_path}")

if __name__ == "__main__":
    main()
