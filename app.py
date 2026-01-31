import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# ---------------- CONFIGURATION ----------------
# "centered" is best for the mobile/Instagram look
st.set_page_config(page_title="Daily Eats", page_icon="🥑", layout="centered")

# ---------------- THEME ENGINE ----------------
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

# Color Palettes (Instagram-inspired)
themes = {
    "light": {
        "bg": "#fafafa",         # Very light grey (Instagram web bg)
        "card": "#ffffff",       # Pure white cards
        "text": "#262626",       # Almost black text
        "subtext": "#8e8e8e",    # Grey for dates/secondary
        "border": "#dbdbdb",     # Subtle border
        "input": "#efefef",      # Light grey inputs
        "accent": "linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%)" # Insta Gradient
    },
    "dark": {
        "bg": "#000000",         # Pure black
        "card": "#121212",       # Dark grey cards
        "text": "#F5F5F5",       # Almost white text
        "subtext": "#A8A8A8",    # Light grey subtext
        "border": "#363636",     # Dark border
        "input": "#262626",      # Dark inputs
        "accent": "linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%)"
    }
}
c = themes[st.session_state.theme]

# ---------------- CSS INJECTION ----------------
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Roboto', sans-serif;
    }}

    /* Global Background */
    .stApp {{
        background-color: {c['bg']};
        color: {c['text']};
    }}

    /* Hide Header */
    [data-testid="stHeader"] {{ visibility: hidden; }}

    /* Cards (Feed Posts) */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {c['card']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 0px !important;
        margin-bottom: 20px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }}

    /* Buttons (The "Fresh" Gradient) */
    div.stButton > button:first-child {{
        background: {c['accent']};
        color: white;
        border: none;
        border-radius: 8px;
        height: 45px;
        font-weight: 600;
        font-size: 14px;
    }}

    /* Inputs */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input {{
        background-color: {c['input']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 6px;
    }}
    /* Dropdown text fix for dark mode */
    div[data-baseweb="select"] > div {{
        background-color: {c['input']};
        color: {c['text']};
    }}

    /* Custom Classes for Text */
    .post-header {{ padding: 10px 15px; display: flex; align-items: center; }}
    .username {{ font-weight: 600; font-size: 14px; color: {c['text']}; margin-right: 5px; }}
    .timestamp {{ font-size: 12px; color: {c['subtext']}; }}
    .caption {{ padding: 10px 15px; font-size: 14px; color: {c['text']}; }}
    .stats-text {{ font-size: 16px; font-weight: 500; color: {c['text']}; }}
</style>
""", unsafe_allow_html=True)

# ---------------- BACKEND ----------------
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

def load_data():
    try:
        data = sh.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=["Name", "Date time", "Image", "Calories", "Likes"])

def image_to_base64(image_file):
    img = Image.open(image_file)
    img.thumbnail((400, 400)) # Resize for API safety
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=60) 
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

df = load_data()

# ---------------- UI LAYOUT ----------------

# 1. TOP NAV BAR
col_home, col_title, col_theme = st.columns([1, 4, 1])
with col_home:
    if st.button("🏠", help="Refresh Feed"):
        st.rerun()
with col_title:
    st.markdown(f"<h3 style='text-align: center; margin: 0; color: {c['text']}'>Daily Eats</h3>", unsafe_allow_html=True)
with col_theme:
    if st.button("🌗", help="Toggle Dark/Light Mode"):
        toggle_theme()
        st.rerun()

st.write("") # Spacer

# 2. TABS
tab_feed, tab_log, tab_stats = st.tabs(["feed", "plus", "chart"])

# --- TAB 1: INSTAGRAM FEED ---
with tab_feed:
    if not df.empty:
        # Reverse list to show newest first
        for i, row in df.iloc[::-1].iterrows():
            
            # --- CARD START ---
            with st.container(border=True):
                
                # A. HEADER (Avatar + Name + Time)
                c1, c2, c3 = st.columns([1, 5, 1])
                with c1:
                    # Avatar
                    av_bg = "E1306C" if row.get('Name') == 'Juvy' else "405DE6"
                    st.image(f"https://ui-avatars.com/api/?background={av_bg}&color=fff&rounded=true&bold=true&name={row.get('Name')}", width=32)
                with c2:
                    # Name & Date
                    st.markdown(f"""
                        <div style="line-height: 1.2; margin-top: 2px;">
                            <span class="username">{row.get('Name')}</span><br>
                            <span class="timestamp">{row.get('Date time')}</span>
                        </div>
                    """, unsafe_allow_html=True)
                with c3:
                    # Delete Button (Top Right)
                    if st.button("🗑️", key=f"del_{i}"):
                        sh.delete_row(i + 2)
                        st.rerun()

                # B. IMAGE (Full Width)
                img_str = row.get('Image', '')
                if str(img_str).startswith('data:'):
                    st.image(img_str, use_container_width=True)
                
                # C. ACTION BAR (Likes + Calories)
                c_like, c_cal = st.columns([1, 4])
                with c_like:
                    likes = row.get('Likes') or 0
                    if st.button(f"❤️ {likes}", key=f"like_{i}"):
                        sh.update_cell(i + 2, 5, int(likes) + 1)
                        st.rerun()
                with c_cal:
                    st.markdown(f"<div style='padding-top: 8px; color:{c['text']}'><b>{row.get('Calories')}</b> kcal</div>", unsafe_allow_html=True)

            # --- CARD END ---
            st.write("") # Spacer between posts
    else:
        st.info("No posts yet.")

# --- TAB 2: LOG NEW MEAL ---
with tab_log:
    st.write("")
    with st.container(border=True):
        st.markdown(f"<h4 style='color:{c['text']}'>New Post</h4>", unsafe_allow_html=True)
        with st.form("entry_form", clear_on_submit=True):
            
            c1, c2 = st.columns(2)
            name = c1.selectbox("Who?", ["JB", "Juvy"])
            cals = c2.number_input("Calories", 0, 2000, 400, step=50)
            
            c3, c4 = st.columns(2)
            d_date = c3.date_input("Date")
            d_time = c4.time_input("Time")
            
            st.markdown("---")
            photo = st.file_uploader("Photo", type=['jpg','png'])
            cam = st.camera_input("Camera")
            
            final_file = photo if photo else cam
            
            if st.form_submit_button("Share"):
                if final_file:
                    with st.spinner("Sharing..."):
                        try:
                            img_b64 = image_to_base64(final_file)
                            if len(img_b64) > 50000:
                                st.error("Image too big!")
                                st.stop()
                            
                            # Format: "Jan 30 • 11:30 PM"
                            ts = datetime.combine(d_date, d_time).strftime("%b %d • %I:%M %p")
                            sh.append_row([name, ts, cals, img_b64, 0])
                            st.success("Shared!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Please upload a photo!")

# --- TAB 3: STATISTICS ---
with tab_stats:
    st.write("")
    if not df.empty:
        df['Calories'] = pd.to_numeric(df['Calories'], errors='coerce').fillna(0)
        
        with st.container(border=True):
            st.markdown(f"<h4 style='color:{c['text']}'>Activity</h4>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            c1.metric("JB Total", f"{int(df[df['Name']=='JB']['Calories'].sum())}")
            c2.metric("Juvy Total", f"{int(df[df['Name']=='Juvy']['Calories'].sum())}")
            
            st.divider()
            st.bar_chart(df.groupby("Name")["Calories"].sum(), color="#d62976")
