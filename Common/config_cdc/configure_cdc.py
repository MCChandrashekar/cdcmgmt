import streamlit as st
import json
import os

def  configure_cdc_settings():
    # Dummy data for demonstration
    if "interfaces" not in st.session_state:
        st.session_state.interfaces = ["192.168.1.1", "192.168.1.2"]
    if "selected_section" not in st.session_state:
        st.session_state.selected_section = None
    if "cdc_config" not in st.session_state:
        st.session_state.cdc_config = {"param1": "value1", "param2": "value2"}

    ha_enabled = True
    ha_status = {"state": "Active", "interfaces": {"192.168.1.1": "UP", "192.168.1.2": "DOWN"}}
    log_levels = ["fatal", "error", "warning", "info", "debug"]
    features = [f"Feature {i}" for i in range(1, 16)]

    # Callback to set the selected section
    def set_section(section):
        st.session_state.selected_section = section

    # Layout: Left column for navigation, right column for content
    left_col, right_col = st.columns([1, 3], border=True)

    with left_col:
        st.markdown(
            """
            <style>
            div.stButton > button {
                width: 100%;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        st.subheader("Sections")
        if st.button("Interfaces", on_click=set_section, args=("Interfaces",)):
            pass
        if st.button("Backup", on_click=set_section, args=("Backup",)):
            pass
        if st.button("Logging", on_click=set_section, args=("Logging",)):
            pass
        if st.button("Config", on_click=set_section, args=("Config",)):
            pass
        if st.button("Set HA", on_click=set_section, args=("HA Settings",)):
            pass

    with right_col:
        st.header("Current Configuration")
        section = st.session_state.selected_section

        if section == "Interfaces":
            st.subheader("CDC Interfaces/Subnets/VLANs")
            st.markdown("**Currently Configured Interfaces**")
            for ip in st.session_state.interfaces:
                st.write(ip)
            
            st.subheader("Modify Interfaces")
            remove_ip = st.selectbox("Select interface to detach", st.session_state.interfaces, key="remove_interface")
            if st.button("Detach Interface"):
                if remove_ip in st.session_state.interfaces:
                    st.session_state.interfaces.remove(remove_ip)
                    st.success(f"Detached {remove_ip}")
            
            new_ip = st.text_input("Add new Interface (IP Address)", key="new_interface")
            if st.button("Add Interface"):
                if new_ip:
                    st.session_state.interfaces.append(new_ip)
                    st.success(f"Added {new_ip}")

        elif section == "Backup/Restore":
            st.subheader("CDC Configuration Backup/Restore")
            auto_backup = st.checkbox("Enable Auto Backup", key="auto_backup")
            if not auto_backup:
                backup_path = st.text_input("Backup File Path", key="backup_path")
                if st.button("Set Backup Path"):
                    st.success(f"Backup path set to {backup_path}")

            auto_restore = st.checkbox("Enable Auto Restore", key="auto_restore")
            if not auto_restore:
                restore_path = st.text_input("Restore File Path", key="restore_path")
                if st.button("Restore Configuration"):
                    st.success(f"Restoring configuration from {restore_path}")

        elif section == "Logging":
            st.subheader("Logging Configuration")
            log_path = st.text_input("Log File Path", key="log_path")
            if st.button("Set Log Path"):
                st.success(f"Log path set to {log_path}")

            log_level = st.selectbox("Select Log Level", log_levels, key="log_level")
            if st.button("Set Log Level"):
                st.success(f"Log level set to {log_level}")

            debug_feature = st.selectbox("Enable Debug Logs for Feature", features, key="debug_feature")
            if st.button("Enable Debug Logs"):
                st.success(f"Debug logs enabled for {debug_feature}")

        elif section == "Reboot Config":
            st.subheader("Configuration for Next Switch Reboot")
            st.markdown("**Current CDC Configuration**")
            st.json(st.session_state.cdc_config)
            
            param = st.text_input("Enter Parameter to Modify", key="modify_param")
            new_value = st.text_input("Enter New Value", key="new_value")
            if st.button("Modify Parameter"):
                if param in st.session_state.cdc_config:
                    st.session_state.cdc_config[param] = new_value
                    st.success(f"Updated {param} to {new_value}")
                else:
                    st.error("Invalid parameter")

        elif section == "HA Info":
            if ha_enabled:
                st.markdown("**High Availability (HA) Information**")
                st.markdown("**HA State**")
                st.write(f"Local CDC State: {ha_status['state']}")
                st.markdown("**Interface HA Status**")
                for ip, status in ha_status["interfaces"].items():
                    st.write(f"{ip}: {status}")
            else:
                st.info("HA is not enabled.")
        else:
            st.info("Please select a section from the left.")


if __name__ == "__main__":
    configure_cdc_settings()