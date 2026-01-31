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

# ---------------- STATE MANAGEMENT ----------------
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'home' # 'home', 'JB', or 'Juvy'

def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

def set_view(view_name):
    st.session_state.current_view = view_name

themes = {
    "light": {
        "bg": "#fafafa",
        "card": "#ffffff",
        "text": "#262626",
        "subtext": "#8e8e8e",
        "border": "#dbdbdb",
        "input": "#efefef",
        "story_ring": "linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%)"
    },
    "dark": {
        "bg": "#000000",
        "card": "#121212",
        "text": "#F5F5F5",
        "subtext": "#A8A8A8",
        "border": "#363636",
        "input": "#262626",
        "story_ring": "#363636"
    }
}
c = themes[st.session_state.theme]

# ---------------- CSS OVERHAUL ----------------
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Grand+Hotel&family=Roboto:wght@400;500;700&display=swap');

    /* Global Settings */
    .stApp {{
        background-color: {c['bg']};
        color: {c['text']};
    }}
    
    header, footer {{visibility: hidden;}}

    /* "Daily Eats" Logo Button Styling */
    div.stButton.logo-btn > button {{
        font-family: 'Grand Hotel', cursive !important;
        font-size: 38px !important;
        color: {c['text']} !important;
        background: transparent !important;
        border: none !important;
        padding: 0px !important;
        margin: 0px !important;
        box-shadow: none !important;
        cursor: pointer;
    }}
    div.stButton.logo-btn > button:hover {{
        color: #ed4956 !important;
    }}

    /* Standard Buttons */
    div.stButton > button {{
        background-color: transparent;
        color: {c['text']};
        border: 1px solid {c['border']};
    }}
    
    /* Post Card Container */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {c['card']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        margin-bottom: 15px;
        padding: 0px !important;
        overflow: hidden;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] > div > div {{
        gap: 0px;
    }}

    /* Inputs */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input {{
        background-color: {c['input']};
        color: {c['text']};
        border: 1px solid {c['border']};
    }}

    /* Stories */
    .story-ring {{
        width: 74px;
        height: 74px;
        border-radius: 50%;
        padding: 3px;
        background: {c['story_ring']};
        display: flex;
        justify-content: center;
        align-items: center;
        margin: auto;
        cursor: pointer;
        transition: transform 0.2s;
    }}
    .story-ring:hover {{
        transform: scale(1.05);
    }}
    .story-img {{
        width: 66px;
        height: 66px;
        border-radius: 50%;
        border: 3px solid {c['card']};
        background-color: #eee;
        display: block;
    }}
    
    /* Profile Stats */
    .profile-stat-num {{ font-size: 18px; font-weight: bold; display: block; }}
    .profile-stat-label {{ font-size: 12px; color: {c['subtext']}; }}
</style>
""", unsafe_allow_html=True)

# ---------------- BACKEND ----------------
# (Keep your existing connection logic here)
def get_worksheet():
    try:
        secrets = st.secrets["connections"]["gsheets"]["service_account_info"]
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(secrets, scopes=scope)
        client = gspread.authorize(creds)
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        return client.open_by_url(sheet_url).sheet1
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
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
    if img.mode != 'RGB': img = img.convert('RGB')
    img.thumbnail((400, 400)) 
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=50) 
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

df = load_data()
if not df.empty:
    df['Calories'] = pd.to_numeric(df['Calories'], errors='coerce').fillna(0)

# ---------------- UI LAYOUT ----------------

# 1. HEADER (Clickable Logo + Theme)
c_logo, c_space, c_theme = st.columns([3, 4, 1])
with c_logo:
    # Use a specific class to style this button as text
    st.markdown('<div class="logo-btn">', unsafe_allow_html=True)
    if st.button("Daily Eats", key="home_btn", help="Go to Feed"):
        set_view('home')
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with c_theme:
    if st.button("🌗"):
        toggle_theme()
        st.rerun()

st.write("") 

# 2. STORY NAV BAR (JB and Juvy Only)
# We render this on EVERY page so you can always switch profiles
s_col1, s_col2, s_col3, s_col4 = st.columns(4)
users = ["JB", "Juvy"]
avatars = ["405DE6", "E1306C"]

# Helper to render a clickable story "button"
def render_story_btn(col, user_name, color_hex):
    with col:
        # We use a container to stack the Image and the Button tightly
        with st.container():
            # Display Avatar (Visual only)
            st.markdown(f"""
                <div class="story-ring" style="background: linear-gradient(45deg, #{color_hex}, #f09433);">
                    <img class="story-img" src="https://ui-avatars.com/api/?background={color_hex}&color=fff&name={user_name}&bold=true&size=128">
                </div>
            """, unsafe_allow_html=True)
            
            # Invisible-ish button below to handle the click
            # We use the full name as the label so it's clear
            if st.button(user_name, key=f"nav_{user_name}", use_container_width=True):
                set_view(user_name)
                st.rerun()

render_story_btn(s_col1, "JB", "405DE6")
render_story_btn(s_col2, "Juvy", "E1306C")

st.markdown(f"<div style='border-bottom: 1px solid {c['border']}; margin-top: 15px; margin-bottom: 15px;'></div>", unsafe_allow_html=True)

# ---------------- MAIN CONTENT ROUTER ----------------

# VIEW A: THE HOME FEED (Default)
if st.session_state.current_view == 'home':
    
    tab_feed, tab_log, tab_stats = st.tabs(["🏠 Feed", "➕ New", "📊 Stats"])

    # --- HOME FEED ---
    with tab_feed:
        if not df.empty:
            for i, row in df.iloc[::-1].iterrows():
                with st.container(border=True):
                    # Header
                    c1, c2, c3 = st.columns([1, 6, 1])
                    with c1:
                        st.markdown(f"""<div style="padding-top:10px; padding-left:10px;">
                            <img src="https://ui-avatars.com/api/?background=random&color=fff&rounded=true&bold=true&name={row.get('Name')}" width="32" style="border-radius:50%;">
                            </div>""", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"""<div style="padding-top:10px; line-height:1.1;">
                            <span style="font-weight:600; font-size:14px; color:{c['text']}">{row.get('Name')}</span><br>
                            <span style="font-size:12px; color:{c['subtext']}">{str(row.get('Date time')).split('•')[0]}</span>
                            </div>""", unsafe_allow_html=True)
                    with c3:
                        if st.button("⋮", key=f"opt_{i}"):
                             sh.delete_row(i + 2)
                             st.rerun()

                    # Image
                    st.write("") 
                    img_str = row.get('Image', '')
                    if str(img_str).startswith('data:'):
                        st.image(img_str, use_container_width=True)
                    
                    # Caption
                    st.markdown(f"""
                    <div style="padding: 0px 12px 15px 12px;">
                        <span style="font-weight: 600; font-size: 14px;">{row.get('Name')}</span>
                        <span style="font-size: 14px;">Ate <b>{row.get('Calories')} kcal</b> 🥑</span>
                    </div>
                    """, unsafe_allow_html=True)
                st.write("") 
        else:
            st.info("No posts yet.")

    # --- UPLOAD FORM ---
    with tab_log:
        st.write("")
        with st.container(border=True):
            st.markdown(f"<div style='padding:15px; font-weight:600; color:{c['text']}'>New Post</div>", unsafe_allow_html=True)
            
            st.markdown(f"<div style='padding-left:15px; font-size:14px; color:{c['text']}'>Choose Source</div>", unsafe_allow_html=True)
            input_type = st.radio("Input Source", ["Upload", "Camera"], horizontal=True, label_visibility="collapsed")
            
            final_file = None
            if input_type == "Upload":
                final_file = st.file_uploader("Choose file", type=['jpg','png'], label_visibility="collapsed")
            else:
                final_file = st.camera_input("Take photo", label_visibility="collapsed")

            st.divider()

            with st.form("entry_form", clear_on_submit=True):
                f1, f2 = st.columns([1, 2])
                with f1:
                    st.image("https://ui-avatars.com/api/?background=ddd&name=?", width=60)
                with f2:
                    name = st.selectbox("Select User", ["JB", "Juvy"], label_visibility="collapsed")
                
                cals = st.number_input("Calories (kcal)", 0, 2000, 400, step=50)
                
                c3, c4 = st.columns(2)
                d_date = c3.date_input("Date")
                d_time = c4.time_input("Time")
                
                st.write("")
                if st.form_submit_button("Share Post", use_container_width=True):
                    if final_file:
                        try:
                            img_b64 = image_to_base64(final_file)
                            ts = datetime.combine(d_date, d_time).strftime("%b %d • %I:%M %p")
                            # Ensure Correct Column Order: Name, Date, Image, Calories, Likes
                            sh.append_row([name, ts, img_b64, cals, 0])
                            st.success("Shared!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Image required!")

    # --- GLOBAL STATS ---
    with tab_stats:
        st.write("")
        if not df.empty:
            col_jb, col_juvy = st.columns(2)
            with col_jb:
                total_jb = int(df[df['Name']=='JB']['Calories'].sum())
                st.metric("JB Total", f"{total_jb} kcal")
            with col_juvy:
                total_juvy = int(df[df['Name']=='Juvy']['Calories'].sum())
                st.metric("Juvy Total", f"{total_juvy} kcal")
            st.bar_chart(df.groupby("Name")["Calories"].sum(), color="#d62976")

# VIEW B & C: INDIVIDUAL PROFILES
else:
    # Get the user from the state ('JB' or 'Juvy')
    profile_user = st.session_state.current_view
    
    # Filter Data for this user
    user_df = df[df['Name'] == profile_user] if not df.empty else pd.DataFrame()
    
    # --- PROFILE HEADER ---
    st.markdown(f"### {profile_user}'s Profile")
    
    ph1, ph2, ph3 = st.columns([1, 1, 1])
    with ph1:
        # Large Avatar
        st.image(f"https://ui-avatars.com/api/?background=random&color=fff&name={profile_user}&size=128&rounded=true")
    with ph2:
        total_cals = int(user_df['Calories'].sum()) if not user_df.empty else 0
        st.markdown(f"<span class='profile-stat-num'>{total_cals}</span><span class='profile-stat-label'>Total Cals</span>", unsafe_allow_html=True)
    with ph3:
        post_count = len(user_df)
        st.markdown(f"<span class='profile-stat-num'>{post_count}</span><span class='profile-stat-label'>Posts</span>", unsafe_allow_html=True)

    st.divider()

    # --- PROFILE DASHBOARD ---
    
    # 1. User's Personal Chart
    st.caption("Performance")
    if not user_df.empty:
        # Group by Date to show trend
        # We need to extract just the date part for grouping
        user_df['SimpleDate'] = user_df['Date time'].astype(str).apply(lambda x: x.split('•')[0] if '•' in x else x)
        chart_data = user_df.groupby('SimpleDate')['Calories'].sum()
        st.line_chart(chart_data)
    else:
        st.info("No data available.")

    st.write("")
    
    # 2. User's Post Grid
    st.caption("Posts")
    if not user_df.empty:
        # Display posts in a 3-column grid (Instagram style)
        grid_cols = st.columns(3)
        for i, row in user_df.iloc[::-1].reset_index().iterrows():
            col = grid_cols[i % 3]
            with col:
                img_str = row.get('Image', '')
                if str(img_str).startswith('data:'):
                    st.image(img_str, use_column_width=True)
                st.caption(f"{row.get('Calories')} kcal")
