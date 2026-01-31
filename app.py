import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# ---------------- CONFIGURATION ----------------
st.set_page_config(page_title="Daily Eats", page_icon="🥑", layout="centered")

# ---------------- THEME ENGINE ----------------
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

theme = {
    "light": {"bg": "#ffffff", "text": "#333333", "card": "#f8f9fa", "btn": "linear-gradient(90deg, #FF4B4B, #FF6B6B)"},
    "dark": {"bg": "#0e1117", "text": "#ffffff", "card": "#262730", "btn": "linear-gradient(90deg, #FF4B4B, #FF6B6B)"}
}
current = theme[st.session_state.theme]

# Inject CSS for the "Production" Look
st.markdown(f"""
<style>
    .stApp {{ background-color: {current['bg']}; color: {current['text']}; }}
    div.stButton > button:first-child {{
        background: {current['btn']}; color: white; border: none; border-radius: 12px; height: 50px; width: 100%; font-weight: 600;
    }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)

# ---------------- ROBUST DATABASE CONNECTION ----------------
# This uses the exact method that passed your "Doctor" test
def get_worksheet():
    try:
        # Load secrets
        secrets = st.secrets["connections"]["gsheets"]["service_account_info"]
        
        # Authenticate
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(secrets, scopes=scope)
        client = gspread.authorize(creds)
        
        # Open Sheet
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        return client.open_by_url(sheet_url).sheet1
    except Exception as e:
        st.error(f"Connection Error: {e}")
        st.stop()

# ---------------- HELPERS ----------------
def image_to_base64(image_file):
    img = Image.open(image_file)
    img.thumbnail((600, 600))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

# Load Data
sh = get_worksheet()
try:
    data = sh.get_all_records()
    df = pd.DataFrame(data)
except:
    df = pd.DataFrame(columns=["Name", "Date time", "Image", "Calories", "Likes"])

# ---------------- UI LAYOUT ----------------
# Header
c1, c2 = st.columns([5,1])
c1.title("🥑 Daily Eats")
if c2.button("🌗"): toggle_theme(); st.rerun()

# Tabs
tab_feed, tab_log, tab_stats = st.tabs(["Feed", "Log Meal", "Stats"])

# --- TAB 1: FEED ---
with tab_feed:
    if not df.empty:
        # Show newest first
        for i, row in df.iloc[::-1].iterrows():
            with st.container(border=True):
                c_head, c_date = st.columns([1, 4])
                c_head.write("🧑‍🍳" if row.get('Name') == 'JB' else "👩‍🍳")
                c_date.caption(f"**{row.get('Name')}** • {row.get('Date time')}")
                
                # Image
                img_str = row.get('Image', '')
                if str(img_str).startswith('data:'):
                    st.image(img_str, use_container_width=True)
                
                # Footer
                st.markdown(f"**{row.get('Calories')}** kcal")
    else:
        st.info("No meals yet. Log your first one!")

# --- TAB 2: LOGGING ---
with tab_log:
    st.write("")
    with st.container(border=True):
        st.subheader("New Entry")
        with st.form("entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            name = col1.selectbox("Who?", ["JB", "Juvy"])
            cals = col2.number_input("Calories", 0, 2000, 400, step=50)
            
            col3, col4 = st.columns(2)
            d_date = col3.date_input("Date")
            d_time = col4.time_input("Time")
            
            photo = st.file_uploader("Upload", type=['jpg','png'])
            cam = st.camera_input("Camera")
            final_file = photo if photo else cam
            
            if st.form_submit_button("Save Meal"):
                if final_file:
                    with st.spinner("Saving to Google Sheets..."):
                        img_b64 = image_to_base64(final_file)
                        timestamp = datetime.combine(d_date, d_time).strftime("%Y-%m-%d %H:%M")
                        
                        # DIRECT WRITE TO SHEET (The "Manual" Fix)
                        sh.append_row([name, timestamp, cals, img_b64, 0])
                        
                        st.success("Saved!")
                        st.rerun()
                else:
                    st.warning("Please add a photo!")

# --- TAB 3: STATS ---
with tab_stats:
    if not df.empty:
        # Convert cals to number carefully
        df['Calories'] = pd.to_numeric(df['Calories'], errors='coerce').fillna(0)
        
        total = df['Calories'].sum()
        jb = df[df['Name']=='JB']['Calories'].sum()
        juvy = df[df['Name']=='Juvy']['Calories'].sum()
        
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            c1.metric("Total", int(total))
            c2.metric("JB", int(jb))
            c3.metric("Juvy", int(juvy))
        
        st.bar_chart(df.groupby("Name")["Calories"].sum(), color="#FF4B4B")
