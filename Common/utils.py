import paramiko # type: ignore
from PIL import Image
import time
import streamlit as st
import streamlit.components.v1 as components

class SSHManager:
    """
    Singleton class for managing SSH connections.
    This class implements the Singleton pattern to ensure only one SSH connection
    manager exists throughout the application's lifecycle. It handles creating,
    maintaining, and testing SSH connections to remote servers.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """
        Returns the singleton instance of SSHManager.
        Creates a new instance if none exists.
        Returns: SSHManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize the SSH manager with no active connection."""
        self.client = None
    
    def connect(self, host, username, password):
        """
        Establishes or reuses an SSH connection to the specified host.
        Args:   host (str): The hostname or IP address to connect to
                username (str): SSH username
                password (str): SSH password
        Returns: paramiko.SSHClient or None: Active SSH client if successful, None if connection fails
        Note:   - Tests existing connection before reuse
                - Creates new connection if needed
                - Displays error messages via Streamlit if connection fails
        """
        try:
            if self.client:
                try:
                    # Test if connection is still alive
                    self.client.exec_command('echo 1', timeout=5)
                    return self.client
                except:
                    self.client = None
            
            # Create new connection
            client, error = ssh_connect(host, username, password)
            if error:
                st.error(f"SSH connection failed: {error}")
                return None
                
            self.client = client
            return self.client
            
        except Exception as e:
            st.error(f"Connection error: {str(e)}")
            return None

@st.cache_resource 
def get_ssh_manager():
    """
    Returns cached instance of SSHManager.
    Uses Streamlit's caching to maintain connection across reruns.
    Returns: SSHManager: Cached singleton instance
    """
    return SSHManager.get_instance()


def verify_cdc_cfg_running():
    """Verify CDC configuration and process status"""
    try:
        client = st.session_state.client
        if not client:
            st.error("No active SSH connection")
            return    
        file_path = "/hpe_nvme/cdc.conf"
        # Check config file
        with st.spinner("Checking cdc.conf file presence .."):
            #time.sleep(0.7)
            if check_file_exists(client, file_path):
                st.success(f"CDC Configuration File {file_path} found")
            else:
                st.error(f"File {file_path} does not exist")
                return
            
        # Check process
        with st.spinner("Verifying nsd, mdnsd, slapd ..."):
            #time.sleep(0.5)
            if check_process_running(client, "nsd"):
                st.session_state.cdc_status = "CDCRunning"
                st.session_state.page = 0
                st.success("CDC processes are running")
            else:
                st.error("CDC is not running. Start CDC")
                st.session_state.cdc_status = "Connected"
        #time.sleep(1.5)
        

    except Exception as e:
        st.error(f"Error verifying CDC configuration: {str(e)}")

def display_login_page():
    """Display login form and handle connection"""
    
    image = Image.open('./Data/hpe_logo_small.jpg')
    st.image(image)
    
    st.title("CDC Server/Switch Login")
    
    host = st.text_input("CDC Server IP Address")
    username = st.text_input("Username", placeholder="username")
    password = st.text_input("Password", type="password")
    
    if st.button("Connect"):
        ssh_manager = get_ssh_manager()
        client = ssh_manager.connect(host, username, password)
        if client:
            st.session_state.client = client
            st.session_state.server = host
            st.session_state.username = username
            st.session_state.password = password
            st.session_state.cdc_status = "Connected"
            st.success("Login to Server successful!")

def is_valid_ip(ip_str: str) -> tuple[bool, str]:
    """
    Validates IPv4 address format.
    Args: ip_str (str): IP address string to validate
    Returns: tuple[bool, str]: (is_valid, error_message)
    Checks: - Correct number of octets
            - Valid numeric ranges (0-255)
            - No leading zeros in octets
    """
    if "." in ip_str:
        octets = ip_str.split(".")
        
        if len(octets) != 4:
            return False, "IPv4 address must have exactly 4 octets"
            
        try:
            for octet in octets:
                num = int(octet)
                if num < 0 or num > 255:
                    return False, f"Invalid IPv4 octet: {octet} (must be between 0 and 255)"
                    
                if len(octet) > 1 and octet[0] == '0':
                    return False, f"Invalid IPv4 octet: {octet} (no leading zeros allowed)"
                    
        except ValueError:
            return False, f"Invalid IPv4 octet: {octet} (must be numeric)"
            
        return True, "Valid IPv4 address"

def is_valid_nqn(nqn: str) -> tuple[bool, str]:
    """
    Validates NVMe Qualified Name (NQN) format.
    Args:   nqn (str): NQN string to validate
    Returns:    tuple[bool, str]: (is_valid, error_message)
    Supports validation of: - Standard NVMe format
                            - UUID format
                            - FC WWNN format
                            - Reverse domain format
    Note: Some TODO items remain for additional validation rules
    """
    if not nqn:
        return False, "Empty string provided"
    
    if not nqn.startswith('nqn.'):
        return False, "NQN must start with 'nqn.'"
    
    parts = nqn.split('.')
    if len(parts) < 3:
        return False, "NQN must have at least 3 parts separated by dots"
    
    # Check if it's a standard NVMe format
    if parts[1] == '2014-08' and parts[2] == 'org' and parts[3] == 'nvmexpress':
        remaining = ':'.join(nqn.split(':')[1:])  # Get everything after first colon
        
        # UUID format
        if nqn.split(':')[0].endswith('uuid'):
            if not remaining:
                return False, "UUID value is missing"
            # Basic UUID format check (could be made more strict)
            if len(remaining.replace('-', '')) != 32:
                return False, "Invalid UUID format"
            #TODO validate UUID. it should be :uuid:x.* where x can be 0 to 9 or a to f or -
            return True, "Valid NVMe UUID format"
            
        # FC WWNN format
        elif nqn.split(':')[0].endswith('fc_wwnn'):
            if not remaining:
                return False, "WWNN value is missing"
            # Basic WWNN format check
            if len(remaining.replace(':', '')) != 16:
                return False, "Invalid WWNN format"
            # TODO after reverse domain "fc_wwnn" is a must with two colons surrounding. The remaining can contain hexadecimal or colon
            return True, "Valid NVMe FC WWNN format"
            
        # Standard subsystem format
        else:
            if ':' in nqn and not remaining:
                return False, "Subsystem identifier is missing"
            return True, "Valid NVMe subsystem format"
    
    # Check for reverse domain format (nqn.yyyy-mm.reverse.domain:user-string)
    else:
        # Validate year-month format in second part
        try:
            year_month = parts[1]
            if len(year_month) != 7:  # yyyy-mm format
                return False, "Invalid year-month format (should be yyyy-mm)"
            
            year, month = year_month.split('-')
            if not (len(year) == 4 and len(month) == 2):
                #TODO if year is '2014' and montn is less than 8, invalid.
                return False, "Invalid year-month format (should be yyyy-mm)"
                
            year_num = int(year)
            month_num = int(month)
            
            if not (2014 <= year_num <= 9999):  # Year should be 2014 or later
                #I think it should be less than or equal to current year and current month.
                return False, "Year must be 2014 or later"
                
            if not (1 <= month_num <= 12):
                return False, "Month must be between 1 and 12"
                
        except (ValueError, IndexError):
            return False, "Invalid year-month format"
            
        # Check for domain and user string
        if ':' in nqn:
            domain, user_string = nqn.split(':', 1)
            if not user_string:
                return False, "User string is missing"
        
        return True, "Valid reverse domain format"

def parse_inp_args():
    """
    Parses command line arguments for the application.
    Returns:    argparse.Namespace with:
            - auto_login (bool): Whether to use saved credentials
            - page (int): Landing page number (default: 0)
    """
    import argparse
    parser = argparse.ArgumentParser(description="Use default username? and land on page no.?")
    parser.add_argument("--auto-login", action="store_true", help="Use saved credentials")
    parser.add_argument("--page", type=int, default=0, help="Landing page number")
    return parser.parse_args()

# Helper Functions
def ssh_connect(host, username, password):
    """
    Creates a new SSH connection.
    Args:   host (str): Hostname or IP address
            username (str): SSH username
            password (str): SSH password
    Returns:tuple: (SSHClient or None, error_message or None)
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=host, username=username, password=password)
        return client, None
    except paramiko.AuthenticationException:
        return None, "Authentication failed, please check your credentials"
    except paramiko.SSHException as sshException:
        return None, f"Unable to establish SSH connection: {sshException}"
    except Exception as e:
        return None, str(e)

def check_file_exists(client, file_path):
    """
    Checks if a file exists on the remote system.
    Args:   client (paramiko.SSHClient): Active SSH client
            file_path (str): Path to check
    Returns:    bool: True if file exists, False otherwise
    """
    stdin, stdout, stderr = client.exec_command(f"test -f {file_path} && echo 'exists' || echo 'not found'")
    result = stdout.read().decode().strip()
    return result == "exists"

def get_file_content(client, file_path):
    """
    Retrieves content of a file from remote system via SFTP.
    Args:   client (paramiko.SSHClient): Active SSH client
            file_path (str): Path to file
    Returns:    str: Content of the file
    """
    sftp = client.open_sftp()
    with sftp.open(file_path, "r") as file:
        content = file.read().decode()
    sftp.close()
    return content

def check_process_running(client, process_name):
    """
    Checks if a process is running on the remote system.
    Args:   client (paramiko.SSHClient): Active SSH client
            process_name (str): Name of process to check
    Returns:    bool: True if process is running, False otherwise
    """
    stdin, stdout, stderr = client.exec_command(f"pgrep -x {process_name}")
    result = stdout.read().decode().strip()
    return bool(result)

def page_header_title(subtitle_text):
    """
    Renders the page header with HPE logo and dynamic subtitle.
    Args:   subtitle_text (str): Text to display as subtitle
    Note:   - Uses custom HTML/CSS for styling
            - Loads HPE logo from local file
    """
    image = Image.open('./Data/hpe_logo_small.jpg')
    st.image(image)
    components.html(
        f"""
        <html>
            <head>
                <style>
                    .title  {{ color:rgb(0, 175, 175); text-align: center; font-size: 36px; }}
                    .subtitle {{ color:rgb(0, 175, 175); text-align: center; font-size: 30px; text-decoration: underline; }}
               </style>
            </head>
        <body>
            <h1 class="title">Centralized Discovery Controller</h1>
            <p class="subtitle">{subtitle_text}</p>
        </body>
        </html>
        """,
        height=200,
    )
    