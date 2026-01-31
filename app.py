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
    st.session_state.current_view = 'home'

def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

# Callback function to handle navigation reliably
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

    .stApp {{
        background-color: {c['bg']};
        color: {c['text']};
    }}
    
    header, footer {{visibility: hidden;}}

    /* BUTTON STYLES */
    div.stButton > button {{
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: {c['text']};
        padding: 0px;
    }}
    div.stButton > button:hover {{
        color: #ed4956;
    }}
    
    /* Header Logo Button */
    div[data-testid="column"] div.stButton.logo-btn > button {{
        font-family: 'Grand Hotel', cursive;
        font-size: 38px;
        margin-top: -10px;
    }}

    /* Form Submit Button (Make it look real) */
    div[data-testid="stForm"] div.stButton > button {{
        background: {c['story_ring']} !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 10px !important;
        font-weight: 600 !important;
    }}

    /* Story Circles */
    .story-ring {{
        width: 80px;
        height: 80px;
        border-radius: 50%;
        padding: 3px;
        background: {c['story_ring']};
        display: flex;
        justify-content: center;
        align-items: center;
        margin: auto;
        margin-bottom: 5px;
    }}
    .story-img {{
        width: 72px;
        height: 72px;
        border-radius: 50%;
        border: 3px solid {c['card']};
        background-color: #eee;
        display: block;
    }}
    
    /* Post Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {c['card']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        margin-bottom: 15px;
        overflow: hidden;
    }}
    
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input {{
        background-color: {c['input']};
        color: {c['text']};
        border: 1px solid {c['border']};
    }}
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

# 1. HEADER
c_logo, c_space, c_theme = st.columns([3, 4, 1])
with c_logo:
    st.markdown('<div class="logo-btn">', unsafe_allow_html=True)
    # Using callback for Home button too
    st.button("Daily Eats", key="home_btn", on_click=set_view, args=('home',))
    st.markdown('</div>', unsafe_allow_html=True)

with c_theme:
    if st.button("🌗"):
        toggle_theme()
        st.rerun()

st.write("") 

# 2. STORY NAVIGATION (Centered)
# Using empty columns to center the 2 profiles
spacer_l, col_jb, col_juvy, spacer_r = st.columns([1, 1, 1, 1])

def render_story_btn(col, user_name, color_hex):
    with col:
        with st.container():
            # The Visual Avatar
            st.markdown(f"""
                <div class="story-ring" style="background: linear-gradient(45deg, #{color_hex}, #f09433);">
                    <img class="story-img" src="https://ui-avatars.com/api/?background={color_hex}&color=fff&name={user_name}&bold=true&size=128">
                </div>
            """, unsafe_allow_html=True)
            
            # The Clickable Button (Invisible but active)
            # We use on_click here for reliable navigation
            st.button(user_name, key=f"nav_{user_name}", use_container_width=True, on_click=set_view, args=(user_name,))

render_story_btn(col_jb, "JB", "405DE6")
render_story_btn(col_juvy, "Juvy", "E1306C")

st.markdown(f"<div style='border-bottom: 1px solid {c['border']}; margin-top: 15px; margin-bottom: 15px;'></div>", unsafe_allow_html=True)

# ---------------- MAIN CONTENT ROUTER ----------------

if st.session_state.current_view == 'home':
    # --- HOME FEED VIEW ---
    tab_feed, tab_log, tab_stats = st.tabs(["🏠 Feed", "➕ New", "📊 Stats"])

    with tab_feed:
        if not df.empty:
            for i, row in df.iloc[::-1].iterrows():
                with st.container(border=True):
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

                    st.write("") 
                    img_str = row.get('Image', '')
                    if str(img_str).startswith('data:'):
                        st.image(img_str, use_container_width=True)
                    
                    st.markdown(f"""
                    <div style="padding: 0px 12px 15px 12px;">
                        <span style="font-weight: 600; font-size: 14px;">{row.get('Name')}</span>
                        <span style="font-size: 14px;">Ate <b>{row.get('Calories')} kcal</b> 🥑</span>
                    </div>
                    """, unsafe_allow_html=True)
                st.write("") 
        else:
            st.info("No posts yet.")

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
                            sh.append_row([name, ts, img_b64, cals, 0])
                            st.success("Shared!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Image required!")

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

else:
    # --- INDIVIDUAL PROFILE VIEW ---
    profile_user = st.session_state.current_view
    
    # Filter Data
    user_df = df[df['Name'] == profile_user] if not df.empty else pd.DataFrame()
    
    st.markdown(f"### {profile_user}'s Profile")
    
    ph1, ph2, ph3 = st.columns([1, 1, 1])
    with ph1:
        st.image(f"https://ui-avatars.com/api/?background=random&color=fff&name={profile_user}&size=128&rounded=true")
    with ph2:
        total_cals = int(user_df['Calories'].sum()) if not user_df.empty else 0
        st.markdown(f"<span class='profile-stat-num'>{total_cals}</span><span class='profile-stat-label'>Total Cals</span>", unsafe_allow_html=True)
    with ph3:
        post_count = len(user_df)
        st.markdown(f"<span class='profile-stat-num'>{post_count}</span><span class='profile-stat-label'>Posts</span>", unsafe_allow_html=True)

    st.divider()

    st.caption("Performance")
    if not user_df.empty:
        user_df['SimpleDate'] = user_df['Date time'].astype(str).apply(lambda x: x.split('•')[0] if '•' in x else x)
        chart_data = user_df.groupby('SimpleDate')['Calories'].sum()
        st.line_chart(chart_data)
    else:
        st.info("No data available.")

    st.write("")
    
    st.caption("Posts")
    if not user_df.empty:
        grid_cols = st.columns(3)
        for i, row in user_df.iloc[::-1].reset_index().iterrows():
            col = grid_cols[i % 3]
            with col:
                img_str = row.get('Image', '')
                if str(img_str).startswith('data:'):
                    st.image(img_str, use_container_width=True)
                st.caption(f"{row.get('Calories')} kcal")
