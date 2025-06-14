# login_client.py
import streamlit as st
import requests

st.set_page_config(page_title="CDC Manager", layout="centered")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "login_attempts" not in st.session_state:
    st.session_state.login_attempts = 0

def login_ui():
    col1, col2, col3 = st.columns([1, 2, 1])  # Center column layout

    with col2:
        st.markdown("<h1 style='text-align: center;'>🔐 CDC Login</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Please enter your credentials to continue.</p>", unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        if st.session_state.login_attempts >= 3:
            st.error("Too many failed attempts. Please restart the app.")
            return

        if st.button("Login"):
            response = requests.post("http://localhost:5002/login", json={
                "username": username,
                "password": password
            })

            if response.status_code == 200 and response.json().get("success"):
                st.session_state.authenticated = True
                st.session_state.login_attempts = 0
                st.success("✅ Login successful!")
                st.experimental_rerun()
            else:
                st.session_state.login_attempts += 1
                st.error(f"❌ Invalid username or password. Attempt {st.session_state.login_attempts}/3")



def cdc_ui():
    st.title("🧠 CDC Management Dashboard")

    zgrp = st.text_input("Enter Zone Group name to create")
    if st.button("Create Zone Group"):
        res = requests.post(f"http://localhost:5001/cdc/api/v1/zgrp/{zgrp}")
        if res.status_code == 201:
            st.success(res.json()["message"])
        else:
            st.error(res.json()["error"])

    if st.button("Logout"):
        st.session_state.authenticated = False
        st.experimental_rerun()

# Entry point
if not st.session_state.authenticated:
    login_ui()
else:
    cdc_ui()
