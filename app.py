import streamlit as st

st.set_page_config(page_title="Secrets Detective", page_icon="🕵️")

st.title("🕵️ Secrets Detective")
st.write("Diagnosing why the app cannot see your password...")

# 1. Check if secrets exist at all
if not st.secrets:
    st.error("❌ CRITICAL: st.secrets is completely empty!")
    st.stop()

# 2. Check for the main [connections] header
if "connections" not in st.secrets:
    st.error("❌ Missing [connections] section.")
    st.info(f"Found these top-level sections instead: {list(st.secrets.keys())}")
    st.stop()

# 3. Check for the [gsheets] subsection
if "gsheets" not in st.secrets["connections"]:
    st.error("❌ Missing [connections.gsheets] subsection.")
    st.info(f"Found inside [connections]: {list(st.secrets['connections'].keys())}")
    st.stop()

# 4. Check for the service account info
creds = st.secrets["connections"]["gsheets"]
st.success("✅ Found [connections.gsheets]!")

if "service_account_info" not in creds:
    st.error("❌ Missing 'service_account_info' block inside gsheets.")
    st.write("Keys found:", creds.keys())
    st.stop()

# 5. Check the Private Key specifically
info = creds["service_account_info"]
if "private_key" not in info:
    st.error("❌ Service Account info exists, but 'private_key' is missing!")
else:
    key_sample = info["private_key"][:15] + "..."
    st.success(f"✅ Private Key found! Starts with: {key_sample}")

st.balloons()
st.success("🎉 DIAGNOSIS: The secrets are readable! You can restore your App code.")
