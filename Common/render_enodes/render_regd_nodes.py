import streamlit as st
import json
import os

# Set wide layout
#st.set_page_config(layout="wide")

def read_file_content(filename):
    """Read content of a file from the static directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'static', filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        st.error(f"Error reading {filename}: {str(e)}")
        return None

def load_sample_data():
    """Load the sample data from JSON file."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, 'data', 'sample_data.json')
        
        with open(data_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # Debug log
            #print("Loaded data:", json.dumps(data, indent=2))
            return data
    except Exception as e:
        st.error(f"Error loading sample data: {str(e)}")
        return None

def render_hosts_subsystems():
    st.title("Storage System Visualization")
    
    try:
        # Load data
        data = load_sample_data()
        if not data:
            st.error("Failed to load visualization data")
            return

        # Load static files
        css_content = read_file_content('style.css')
        js_content = read_file_content('tree.js')
        
        if not css_content or not js_content:
            st.error("Failed to load required static files")
            return

        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>{css_content}</style>
        </head>
        <body>
            <div class="visualization-container">
                <div class="tree-container">
                    <div class="tree-title">Storage System Configuration</div>
                    <svg id="tree-svg"></svg>
                </div>
            </div>

            <script>
                const hostData = {json.dumps(data['hosts'])};
                const storageData = {json.dumps(data['storage'])};
            </script>
            <script>{js_content}</script>
        </body>
        </html>
        """
        
        # Render the visualization
        st.components.v1.html(html_content, height=800)
        
    except Exception as e:
        st.error(f"Error rendering visualization: {str(e)}")
        print("Detailed error:", str(e))  # Debug log

if __name__ == "__main__":
    render_hosts_subsystems()