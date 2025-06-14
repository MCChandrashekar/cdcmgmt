import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from functools import wraps
import time

# CDC API Client with retry
class CDCAPIClient:
    def __init__(self, base_url):
        self.session = self._create_session()
        self.base_url = f"http://localhost:8080/cdc/api/v1"

    def _create_session(self):
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def get(self, endpoint):
        url = f"{self.base_url}/{endpoint}"
        response = self.session.get(url, verify=False)
        response.raise_for_status()
        return response.json()

# Cache utilities
def clear_cache():
    st.cache_data.clear()
    st.session_state.last_cache_reset = time.time()
    st.session_state.force_refresh = True

def cache_with_reset(ttl_seconds=60):
    def decorator(func):
        @st.cache_data(ttl=ttl_seconds)
        def cached_func(*args, **kwargs):
            return func(*args, **kwargs)

        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}_{args}_{kwargs}"
            now = time.time()
            last_time = st.session_state.get(f'cache_time_{key}', 0)

            if st.session_state.get('force_refresh', False) or (now - last_time > ttl_seconds):
                cached_func.clear()
                st.session_state[f'cache_time_{key}'] = now

            return cached_func(*args, **kwargs)
        return wrapper
    return decorator

@cache_with_reset(ttl_seconds=60)
def fetch_nvmenode_data(cdc_ip):
    client = CDCAPIClient(cdc_ip)
    return client.get("nvmenode")

# Sidebar controls
def sidebar_controls():
    with st.sidebar:
        st.markdown("### Cache Options")
        if st.button("🔄 Refresh Cache"):
            clear_cache()
            st.rerun()
        st.text(f"Last Reset: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.session_state.get('last_cache_reset', time.time())))}")

# Main App
def main():
    st.title("CDC Dashboard")
    sidebar_controls()

    st.text_input("Enter CDC IP", key="cdc_server_ip")

    if st.session_state.get("cdc_server_ip"):
        try:
            data = fetch_nvmenode_data(st.session_state["cdc_server_ip"])
            st.write("Fetched NVMe Node Data:")
            st.json(data)
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")

if __name__ == "__main__":
    if 'force_refresh' not in st.session_state:
        st.session_state.force_refresh = False
    main()
