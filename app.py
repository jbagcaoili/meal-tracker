import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Daily Eats", page_icon="🥑", layout="centered")

# ---------------- CSS ----------------
st.markdown("""
<style>
    .stApp { background-color: white; color: #333; }
    div.stButton > button:first-child {
        background: #FF4B4B; color: white; border-radius: 12px; height: 50px; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def image_to_base64(image_file):
    img = Image.open(image_file)
    img.thumbnail((500, 500))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

# ---------------- DATABASE CONNECTION (BRUTE FORCE) ----------------
# We manually pull the secrets to ensure they are found
try:
    if "connections" in st.secrets and "gsheets" in st.secrets.connections:
        # Standard way
        conn = st.connection("gsheets", type=GSheetsConnection)
    else:
        # Fallback: Create connection without arguments and hope for global secrets
        conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Connection setup failed: {e}")
    st.stop()

# ---------------- LOAD DATA ----------------
try:
    # Use the specific URL from secrets if available, or just rely on connection
    df = conn.read(worksheet="Sheet1", ttl=0)
    df = df.dropna(how="all")
    # Auto-repair columns
    for col in ["Name", "Date time", "Image", "Calories", "Likes"]:
        if col not in df.columns:
            df[col] = 0 if col in ["Calories", "Likes"] else ""
except Exception as e:
    st.error(f"Database Error: {e}")
    st.info("Check: 1. Sheet is 'Restricted' (shared with bot). 2. Headers exist: Name, Date time, Image, Calories, Likes")
    df = pd.DataFrame(columns=["Name", "Date time", "Image", "Calories", "Likes"])

# ---------------- UI ----------------
st.title("🥑 Daily Eats")

tab1, tab2 = st.tabs(["Feed", "Log"])

with tab1:
    if not df.empty:
        for i, row in df.iloc[::-1].iterrows():
            with st.container(border=True):
                st.markdown(f"**{row['Name']}** • {row['Date time']}")
                st.image(row['Image'])
                st.caption(f"{row['Calories']} kcal")
    else:
        st.info("No meals yet.")

with tab2:
    with st.form("entry"):
        name = st.selectbox("Who?", ["JB", "Juvy"])
        cal = st.number_input("Calories", 300)
        d = st.date_input("Date")
        t = st.time_input("Time")
        photo = st.file_uploader("Photo")
        
        if st.form_submit_button("Save"):
            if photo:
                img = image_to_base64(photo)
                ts = datetime.combine(d, t).strftime("%Y/%m/%d %H:%M")
                new_row = pd.DataFrame([{"Name": name, "Date time": ts, "Image": img, "Calories": cal, "Likes": 0}])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                
                # THE WRITE OPERATION
                conn.update(worksheet="Sheet1", data=updated_df)
                st.success("Saved!")
                st.rerun()
