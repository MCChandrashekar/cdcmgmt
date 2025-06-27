# restncache.py
import streamlit as st
import json
import time
from pathlib import Path

# Default zone config file
DATA_FILE = Path(__file__).resolve().parent / "data" / "zone_config.json"

@st.cache_data(show_spinner=False)
def load_zone_config(last_updated: float):
    """Loads zone configuration from JSON file using Streamlit caching."""
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def get_zone_data():
    """Helper to return config with dependency on file timestamp"""
    last_updated = DATA_FILE.stat().st_mtime
    return load_zone_config(last_updated)

# Optional: Generic support for other JSON files in /data
@st.cache_data(show_spinner=False)
def _load_generic_json(path_str: str, last_modified: float):
    with open(path_str, "r") as f:
        return json.load(f)

def read_json_from_data(filename: str):
    """Loads and caches any JSON file from the data/ directory"""
    file_path = Path(__file__).resolve().parent / "data" / filename
    if not file_path.exists():
        raise FileNotFoundError(f"{filename} not found in /data")
    return _load_generic_json(str(file_path), file_path.stat().st_mtime)

def zone_config_viewer():
    """Optional UI for viewing zone config interactively"""
    st.title("📄 Zone Configuration Viewer")

    refresh_mode = st.radio(
        "Select refresh mode:",
        ("Manual (button)", "Automatic (interval)")
    )

    if refresh_mode == "Manual (button)":
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.success("✅ Cache cleared. Data reloaded.")
        data = get_zone_data()
        st.json(data)

    else:
        interval = st.selectbox(
            "Select refresh interval:",
            [30, 60, 120, 300, 600, 1200, 3600],
            format_func=lambda x: f"{x//60 if x>=60 else x} {'minute(s)' if x>=60 else 'second(s)'}"
        )
        last_refresh = st.session_state.get("last_refresh", 0)
        now = time.time()
        if now - last_refresh > interval:
            st.cache_data.clear()
            st.session_state["last_refresh"] = now
        data = get_zone_data()
        st.json(data)
        st.info(f"Auto-refresh every {interval//60 if interval>=60 else interval} {'minute(s)' if interval>=60 else 'second(s)'}")
        st.rerun()
