import streamlit as st
import requests
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning # type: ignore

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def fetch_nvmenode_data(cdc_server_ip, command):
    url = f"https://"+cdc_server_ip+":8080/cdc/api/v1/{command}"
    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            data = response.json()
            cdc_config = data["commandout"]["data"]["Info"]
            for key, val in cdc_config.items():
                st.write(f"{key}                                 :  {val}")
            return data
        else:
            return {"error": f"Failed to fetch data, status code: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
 
def send_get_command(cdc_server_ip, command):
    url = f"https://{cdc_server_ip}:8080/cdc/api/v1/{command}"
    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            json_data = response.json()
            return json_data
        else:
            return {"error": f"Failed to fetch data, status code: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def create_zgrp(cdc_server_ip, zgrp_name):
    url = f"https://{cdc_server_ip}:8080/cdc/api/v1/zgrp/{{zgrp_name}}"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "zgrpName": zgrp_name
    }
    try:
        response = requests.post(
            url, 
            headers=headers, 
            data=json.dumps(payload),
            verify=False
        )
        if response.status_code == 200 or response.status_code == 201:
            return {"success": f"Zone Group '{zgrp_name}' created successfully", "response": response.json()}
        else:
            return {"error": f"Failed to create zgrp, status code: {response.status_code}", "response": response.text}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def create_zone(cdc_server_ip, zone_name):
    url = f"https://{cdc_server_ip}:8080/cdc/api/v1/zone/{{zonename}}"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "zoneName": zone_name
    }
    try:
        response = requests.post(
            url, 
            headers=headers, 
            data=json.dumps(payload),
            verify=False
        )
        if response.status_code == 200 or response.status_code == 201:
            return {"success": f"Zone '{zone_name}' created successfully", "response": response.json()}
        else:
            return {"error": f"Failed to create zone, status code: {response.status_code}", "response": response.text}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def create_alias(cdc_server_ip, alias_name):
    url = f"https://{cdc_server_ip}:8080/cdc/api/v1/alias/{{aliasname}}"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "aliasName": alias_name
    }
    try:
        response = requests.post(
            url, 
            headers=headers, 
            data=json.dumps(payload),
            verify=False
        )
        if response.status_code == 200 or response.status_code == 201:
            return {"success": f"Alias '{alias_name}' created successfully", "response": response.json()}
        else:
            return {"error": f"Failed to create alias, status code: {response.status_code}", "response": response.text}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def delete_zgrp(cdc_server_ip, zgrp_name):
    url = f"https://{cdc_server_ip}:8080/cdc/api/v1/zgrp/{{zgrpname}}"
    headers = {
        "accept": "application/json"
    }
    params = {
        "zgrp_name": zgrp_name
    }
    try:
        response = requests.delete(
            url, 
            headers=headers,
            params=params,
            verify=False
        )
        if response.status_code == 200 or response.status_code == 204:
            return {"success": f"Zong Group '{zgrp_name}' deleted successfully", "response": response.json() if response.text else "No content"}
        else:
            return {"error": f"Failed to delete zgrp, status code: {response.status_code}", "response": response.text}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def delete_zone(cdc_server_ip, zone_name):
    url = f"https://{cdc_server_ip}:8080/cdc/api/v1/zone/{{zonename}}"
    headers = {
        "accept": "application/json"
    }
    params = {
        "zone_name": zone_name
    }
    try:
        response = requests.delete(
            url, 
            headers=headers,
            params=params,
            verify=False
        )
        if response.status_code == 200 or response.status_code == 204:
            return {"success": f"Zone '{zone_name}' deleted successfully", "response": response.json() if response.text else "No content"}
        else:
            return {"error": f"Failed to delete zone, status code: {response.status_code}", "response": response.text}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def delete_alias(cdc_server_ip, alias_name):
    url = f"https://{cdc_server_ip}:8080/cdc/api/v1/alias/{{aliasname}}"
    headers = {
        "accept": "application/json"
    }
    params = {
        "alias_name": alias_name
    }
    try:
        response = requests.delete(
            url, 
            headers=headers,
            params=params,
            verify=False
        )
        if response.status_code == 200 or response.status_code == 204:
            return {"success": f"Alias '{alias_name}' deleted successfully", "response": response.json() if response.text else "No content"}
        else:
            return {"error": f"Failed to delete alias, status code: {response.status_code}", "response": response.text}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


if __name__ == "__main__":
    st.title("Testing operation over objects")
    
    # Server IP input (reusing the same IP for all operations)
    cdc_server_ip = st.text_input("CDC Server IP", value="10.22.14.249")
    
    # NVMe Nodes section
    st.header("NVMe Nodes")
    if st.button('Get NVMe Nodes'):
        out = send_get_command(cdc_server_ip, 'nvmenodes')
        st.write(out)
    
    # Using columns for better layout of zone operations
    st.header("Zone Operations")
    col1, col2 = st.columns(2)
    
    # Creation section
    with col1:
        st.subheader("Create Zone Group")
        create_zgrp_name = st.text_input("Zone Group Name for Creation", placeholder="Enter Zone Group name to create")
        if st.button('Create Zone Group'):
            if create_zgrp_name:
                result = create_zgrp(cdc_server_ip, create_zgrp_name)
                st.write(result)
            else:
                st.error("Please enter a Zone Group name")

        st.divider()
        st.subheader("Create Zone")
        create_zone_name = st.text_input("Zone Name for Creation", placeholder="Enter zone name to create")
        if st.button('Create Zone'):
            if create_zone_name:
                result = create_zone(cdc_server_ip, create_zone_name)
                st.write(result)
            else:
                st.error("Please enter a zone name")

        st.divider()
        st.subheader("Create Alias")
        create_alias_name = st.text_input("Alias Name for Creation", placeholder="Enter alias name to create")
        if st.button('Create Alias'):
            if create_alias_name:
                result = create_alias(cdc_server_ip, create_alias_name)
                st.write(result)
            else:
                st.error("Please enter a alias name")
     
    # Deletion section
    with col2:
        st.subheader("Delete Zone Group")
        delete_zgrp_name = st.text_input("Zone Group Name for Deletion", placeholder="Enter Zone Group name to delete")
        if st.button('Delete Zone Group'):
            if delete_zgrp_name:
                result = delete_zgrp(cdc_server_ip, delete_zgrp_name)
                st.write(result)
            else:
                st.error("Please enter a Zone Group name")        

        st.divider()
        st.subheader("Delete Zone")
        delete_zone_name = st.text_input("Zone Name for Deletion", placeholder="Enter zone name to delete")
        if st.button('Delete Zone'):
            if delete_zone_name:
                result = delete_zone(cdc_server_ip, delete_zone_name)
                st.write(result)
            else:
                st.error("Please enter a zone name")
                
        st.divider()
        st.subheader("Delete AliaS")
        delete_alias_name = st.text_input("Alias Name for Deletion", placeholder="Enter alias name to delete")
        if st.button('Delete Alias'):
            if delete_alias_name:
                result = delete_alias(cdc_server_ip, delete_alias_name)
                st.write(result)
            else:
                st.error("Please enter a alia name")
