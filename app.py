import streamlit as st
import google.auth
from google.oauth2 import service_account
import requests

st.title("🔍 Connection Doctor")

# 1. Load Secrets
try:
    info = st.secrets["connections"]["gsheets"]["service_account_info"]
    st.write(f"Testing Key for: `{info['client_email']}`")
except:
    st.error("❌ Secrets are missing or formatted wrong.")
    st.stop()

# 2. Test Google Login (Get a Token)
try:
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    token = google.auth.transport.requests.Request()
    creds.refresh(token)
    st.success("✅ Login Successful! We have a valid token.")
except Exception as e:
    st.error(f"❌ Login Failed: {e}")
    st.stop()

# 3. Test Access to Sheet
sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
sheet_id = sheet_url.split("/d/")[1].split("/")[0]

url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"
headers = {"Authorization": f"Bearer {creds.token}"}
resp = requests.get(url, headers=headers)

if resp.status_code == 200:
    st.success(f"✅ Connected to Sheet: {resp.json().get('properties', {}).get('title')}")
    st.balloons()
else:
    st.error(f"❌ Google Blocked Us (Error {resp.status_code})")
    st.json(resp.json()) # This prints the EXACT reason
