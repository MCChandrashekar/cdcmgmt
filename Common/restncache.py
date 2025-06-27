import streamlit as st
import requests
import backoff # type: ignore
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from functools import wraps
import time

class CDCAPIClient:
    def __init__(self, base_url):
        self.session = self._create_session()
        self.base_url = f"https://{base_url}:8080/cdc/api/v1"
    
    def _create_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy, 
            pool_connections=10, 
            pool_maxsize=10
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3)
    def get(self, endpoint):
        url = f"{self.base_url}/{endpoint}"
        response = self.session.get(url, verify=False)
        response.raise_for_status()
        return response.json()

def get_cache_key(func_name, *args, **kwargs):
    """Generate a unique cache key based on function name and arguments"""
    return f"{func_name}_{str(args)}_{str(kwargs)}"

def clear_all_caches():
    """Clear all cached data"""
    # Clear Streamlit's cache
    st.cache_data.clear()
    
    # Reset cache-related session state variables
    for key in list(st.session_state.keys()):
        if key.startswith('cache_'):
            del st.session_state[key]
    
    # Update last reset timestamp
    st.session_state.last_cache_reset = time.time()
    st.session_state.force_refresh = False

def cache_with_reset(ttl_seconds=60):
    """ Custom cache decorator that supports manual reset and TTL
    Parameters:
    ttl_seconds (int): Time to live for cached data in seconds
    """
    def decorator(func):
        @st.cache_data(ttl=ttl_seconds)
        def cached_func(*args, **kwargs):
            return func(*args, **kwargs)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = get_cache_key(func.__name__, *args, **kwargs)
            
            # Check if we need to force refresh
            force_refresh = st.session_state.get('force_refresh', False)
            
            # Check if cache has expired
            last_update = st.session_state.get(f'cache_time_{cache_key}', 0)
            cache_expired = (time.time() - last_update) > ttl_seconds
            
            if force_refresh or cache_expired:
                cached_func.clear()
                st.session_state[f'cache_time_{cache_key}'] = time.time()
            
            return cached_func(*args, **kwargs)
        return wrapper
    return decorator

@cache_with_reset(ttl_seconds=60)  # Cache for 1 minute
def fetch_nvmenode_data(cdc_server_ip):
    """ Fetch NVMe node data with caching
    Parameters: cdc_server_ip (str): IP address of the CDC server
    Returns: dict: JSON response containing node data
    """
    client = CDCAPIClient(cdc_server_ip)
    return client.get("nvmenode")

@cache_with_reset(ttl_seconds=300)  # Cache for 5 minutes
def send_get_command(cdc_server_ip, command):
    """ Send a GET command to CDC server with caching
    Parameters: cdc_server_ip (str): IP address of the CDC server
    command (str): Command to send
    Returns: dict: JSON response from the server
    """
    client = CDCAPIClient(cdc_server_ip)
    return client.get(command)

def add_cache_management_ui():
    """Add cache management UI elements to the sidebar"""
    with st.sidebar:
        st.markdown("### Cache Management")
        
        # Display last cache reset time
        if 'last_cache_reset' in st.session_state:
            last_reset = time.strftime(
                '%Y-%m-%d %H:%M:%S', 
                time.localtime(st.session_state.last_cache_reset)
            )
            st.text(f"Last Reset: {last_reset}")
        
        # Add manual refresh button
        if st.button("🔄 Refresh All Data", key="refresh_cache"):
            clear_all_caches()
            st.success("Cache cleared successfully!")
            st.rerun()
        
        # Add auto-refresh interval selector
        refresh_intervals = {
            "Disabled": 0,
            "30 seconds": 30,
            "1 minute": 60,
            "5 minutes": 300
        }
        selected_interval = st.selectbox(
            "Auto Refresh Interval",
            options=list(refresh_intervals.keys()),
            key="refresh_interval"
        )
        
        # Store the selected interval in seconds
        st.session_state.auto_refresh_interval = refresh_intervals[selected_interval]

def manage_auto_refresh():
    """Handle automatic cache refresh based on selected interval"""
    if not hasattr(st.session_state, 'last_auto_refresh'):
        st.session_state.last_auto_refresh = time.time()
    
    interval = st.session_state.get('auto_refresh_interval', 0)
    if interval > 0:
        time_since_refresh = time.time() - st.session_state.last_auto_refresh
        if time_since_refresh >= interval:
            clear_all_caches()
            st.session_state.last_auto_refresh = time.time()
            st.rerun()

# Example usage
def restapi_init():
    
    # Add cache management UI
    add_cache_management_ui()
    
    # Handle auto-refresh
    manage_auto_refresh()
    
    # Your existing dashboard code here
    if st.session_state.get('cdc_server_ip'):
        try:
            # This will use cached data unless cache was cleared
            node_data = fetch_nvmenode_data(st.session_state.cdc_server_ip)
            st.write("Node Data:", node_data)
            
            # Other API calls...
            
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")

if __name__ == "__main__":
    st.title("CDC Dashboard")
    restapi_init()