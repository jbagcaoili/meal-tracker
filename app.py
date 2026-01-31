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
    "light": {
        "bg": "#fafafa", # Instagram-like light grey background
        "card": "#ffffff",
        "text": "#262626",
        "subtext": "#8e8e8e",
        "btn_bg": "linear-gradient(135deg, #FF4B4B 0%, #FF6B6B 100%)"
    },
    "dark": {
        "bg": "#000000",
        "card": "#121212",
        "text": "#F5F5F5",
        "subtext": "#A8A8A8",
        "btn_bg": "linear-gradient(135deg, #FF4B4B 0%, #FF6B6B 100%)"
    }
}
current = theme[st.session_state.theme]

# ---------------- INSTAGRAM-STYLE CSS ----------------
st.markdown(f"""
<style>
    /* Global App Styling */
    .stApp {{
        background-color: {current['bg']};
        color: {current['text']};
    }}
    
    /* Hide Default Header */
    [data-testid="stHeader"] {{ visibility: hidden; }}
    
    /* POST CARD STYLING */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {current['card']};
        border: 1px solid {current['bg']}; /* Subtle border */
        border-radius: 12px;
        padding: 0px !important; /* Remove padding to make image full width */
        margin-bottom: 20px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }}
    
    /* Primary Action Button (Save) */
    div.stButton > button:first-child {{
        background: {current['btn_bg']}; 
        color: white; 
        border: none; 
        border-radius: 8px; 
        height: 45px; 
        font-weight: 600;
    }}
    
    /* Icon Buttons (Like/Delete) - Transparent & Clean */
    button[kind="secondary"] {{
        background: transparent !important;
        border: none !important;
        color: {current['text']} !important;
        font-size: 1.2rem;
    }}
    button[kind="secondary"]:hover {{
        color: #FF4B4B !important;
    }}

    /* Typography */
    .username {{ font-weight: 700; font-size: 15px; color: {current['text']}; }}
    .timestamp {{ font-size: 12px; color: {current['subtext']}; }}
    .calories {{ font-weight: 600; font-size: 14px; color: {current['text']}; }}
</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
def get_worksheet():
    try:
        secrets = st.secrets["connections"]["gsheets"]["service_account_info"]
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(secrets, scopes=scope)
        client = gspread.authorize(creds)
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        return client.open_by_url(sheet_url).sheet1
    except Exception as e:
        st.error(f"Connection Error: {e}")
        st.stop()

sh = get_worksheet()

# Helper: Load Data safely
def load_data():
    try:
        data = sh.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=["Name", "Date time", "Image", "Calories", "Likes"])

# Helper: Process Image
def image_to_base64(image_file):
    img = Image.open(image_file)
    img.thumbnail((400, 400)) # Good balance of quality/size
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=60) 
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

# Load initial data
df = load_data()

# ---------------- UI LAYOUT ----------------
# Top Bar
c1, c2 = st.columns([5,1])
c1.markdown(f"### 🥑 Daily Eats")
if c2.button("🌗", help="Toggle Theme"):
    toggle_theme()
    st.rerun()

# Tabs
tab_feed, tab_log, tab_stats = st.tabs(["🏠 Feed", "➕ Log", "📊 Stats"])

# --- TAB 1: SOCIAL FEED ---
with tab_feed:
    if not df.empty:
        # Reverse to show newest first
        # We use .iterrows() on the original reversed DF so 'i' is the REAL index
        for i, row in df.iloc[::-1].iterrows():
            
            # THE POST CARD
            with st.container(border=True):
                
                # 1. HEADER (Avatar + Name)
                c_av, c_info, c_menu = st.columns([1, 5, 1])
                with c_av:
                    # Simple Avatar based on name
                    av = "https://ui-avatars.com/api/?background=FF4B4B&color=fff&rounded=true&name=" + row.get('Name', 'U')
                    st.image(av, width=40)
                with c_info:
                    st.markdown(f"""
                    <div style="line-height: 1.2;">
                        <span class="username">{row.get('Name')}</span><br>
                        <span class="timestamp">{row.get('Date time')}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with c_menu:
                    # Delete Button (Uses real index 'i' + 2 for header correction)
                    if st.button("🗑️", key=f"del_{i}"):
                        sh.delete_row(i + 2) # +2 because Google Sheets is 1-indexed + Header
                        st.rerun()

                # 2. HERO IMAGE (Full Width)
                img_str = row.get('Image', '')
                if str(img_str).startswith('data:'):
