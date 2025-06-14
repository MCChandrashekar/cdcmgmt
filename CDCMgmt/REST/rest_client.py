# RESTclient/client_ui.py
import streamlit as st
import requests

st.title("CDC Client UI")

cdc_server = "http://localhost:5001"

# NVMe Node Info
st.header("NVMe Nodes")
if st.button("Fetch NVMe Nodes"):
    res = requests.get(f"{cdc_server}/cdc/api/v1/nvmenodes")
    st.json(res.json())

# Create zone group/zone/alias
st.header("Create")
zgrp_create = st.text_input("Zone Group to create")
if st.button("Create Zone Group"):
    res = requests.post(f"{cdc_server}/cdc/api/v1/zgrp/{zgrp_create}")
    st.write(res.json())

zone_create = st.text_input("Zone to create")
if st.button("Create Zone"):
    res = requests.post(f"{cdc_server}/cdc/api/v1/zone/{zone_create}")
    st.write(res.json())

alias_create = st.text_input("Alias to create")
if st.button("Create Alias"):
    res = requests.post(f"{cdc_server}/cdc/api/v1/alias/{alias_create}")
    st.write(res.json())

# Delete zone group/zone/alias
st.header("Delete")
zgrp_delete = st.text_input("Zone Group to delete")
if st.button("Delete Zone Group"):
    res = requests.delete(f"{cdc_server}/cdc/api/v1/zgrp/{zgrp_delete}")
    st.write(res.json())

zone_delete = st.text_input("Zone to delete")
if st.button("Delete Zone"):
    res = requests.delete(f"{cdc_server}/cdc/api/v1/zone/{zone_delete}")
    st.write(res.json())

alias_delete = st.text_input("Alias to delete")
if st.button("Delete Alias"):
    res = requests.delete(f"{cdc_server}/cdc/api/v1/alias/{alias_delete}")
    st.write(res.json())
