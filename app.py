import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# ---------------- CONFIGURATION ----------------
st.set_page_config(page_title="Daily Eats", page_icon="📸", layout="centered")

# ---------------- STATE MANAGEMENT ----------------
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'
if 'view' not in st.session_state:
    st.session_state.view = 'home' # Options: 'home', 'profile'
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = None

def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

def go_home():
    st.session_state.view = 'home'
    st.session_state.selected_user = None

def go_profile(user):
    st.session_state.view = 'profile'
    st.session_state.selected_user = user

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
    
    /* Hide Default Header & Footer */
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* Instagram Logo Style - UPDATED SIZE */
    .insta-logo {{
        font-family: 'Grand Hotel', cursive;
        font-size: 38px; /* INCREASED FROM 28px */
        color: {c['text']};
        margin: 0;
        padding: 0;
        text-decoration: none;
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
    
    /* Remove padding inside the card to make image flush */
    div[data-testid="stVerticalBlockBorderWrapper"] > div > div {{
        gap: 0px;
    }}

    /* Buttons (Ghost Style) */
    div.stButton > button {{
        background-color: transparent;
        color: {c['text']};
        border: none;
        padding: 0px 10px;
        font-size: 16px;
    }}
    div.stButton > button:hover {{
        background-color: transparent;
        color: #ed4956;
        border: none;
    }}
    div.stButton > button:focus {{
        background-color: transparent;
        color: #ed4956;
        border: none;
        box-shadow: none;
    }}

    /* Custom Input Styling */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input {{
        background-color: {c['input']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 3px;
    }}

    /* Stories Bar (Circles) */
    .story-ring {{
        width: 72px;
        height: 72px;
        border-radius: 50%;
        padding: 2px;
        background: {c['story_ring']};
        display: flex;
        justify-content: center;
        align-items: center;
        margin: auto;
        cursor: pointer;
    }}
    .story-img {{
        width: 66px;
        height: 66px;
        border-radius: 50%;
        border: 2px solid {c['card']};
        background-color: #eee;
        display: block;
    }}

    /* Tabs Styling (Minimal) */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {c['bg']};
        border-bottom: 1px solid {c['border']};
        gap: 20px;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: {c['subtext']};
    }}
    .stTabs [aria-selected="true"] {{
        background-color: transparent;
        color: {c['text']};
        font-weight: bold;
        border-bottom: 2px solid {c['text']};
    }}

    /* Metric/Stats Styling */
    div[data-testid="stMetricValue"] {{
        font-size: 24px;
        color: {c['text']};
    }}
    div[data-testid="stMetricLabel"] {{
        font-size: 14px;
        color: {c['subtext']};
    }}
</style>
""", unsafe_allow_html=True)

# ---------------- BACKEND HELPERS ----------------
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

# --- UPDATED COMPRESSION LOGIC ---
def image_to_base64(image_file):
    img = Image.open(image_file)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img.thumbnail((400, 400)) 
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=50) 
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

df = load_data()
if not df.empty:
     df['Calories'] = pd.to_numeric(df['Calories'], errors='coerce').fillna(0)

# ---------------- UI LAYOUT ----------------

# 1. APP HEADER
col_title, col_spacer, col_theme = st.columns([3, 1, 1])
with col_title:
    # Logic to handle title clicking (optional reset)
    if st.session_state.view == 'profile':
        if st.button("⬅ Back", key="back_btn"):
            go_home()
            st.rerun()
    else:
        st.markdown('<p class="insta-logo">Daily Eats</p>', unsafe_allow_html=True)

with col_theme:
    if st.button("🌗", help="Toggle Theme"):
        toggle_theme()
        st.rerun()

# 2. STORIES ROW (UPDATED: Interactive & Filtered)
if not df.empty and st.session_state.view == 'home':
    st.write("")
    # Layout centered slightly
    c1, c_jb, c_juvy, c2 = st.columns([1, 1, 1, 1])
    
    users = ["JB", "Juvy"] 
    avatars = ["405DE6", "E1306C"]
    
    with c_jb:
        st.markdown(f"""
            <div class="story-ring">
                <img class="story-img" src="https://ui-avatars.com/api/?background={avatars[0]}&color=fff&name={users[0]}&bold=true">
            </div>
        """, unsafe_allow_html=True)
        if st.button("JB", key="story_jb", use_container_width=True):
            go_profile("JB")
            st.rerun()

    with c_juvy:
        st.markdown(f"""
            <div class="story-ring">
                <img class="story-img" src="https://ui-avatars.com/api/?background={avatars[1]}&color=fff&name={users[1]}&bold=true">
            </div>
        """, unsafe_allow_html=True)
        if st.button("Juvy", key="story_juvy", use_container_width=True):
            go_profile("Juvy")
            st.rerun()
            
    st.markdown(f"<div style='border-bottom: 1px solid {c['border']}; margin-top: 10px; margin-bottom: 10px;'></div>", unsafe_allow_html=True)


# ---------------- MAIN CONTENT AREA ----------------

if st.session_state.view == 'home':
    # 3. HOME TABS
    tab_feed, tab_log, tab_stats = st.tabs(["🏠 Feed", "➕ New", "📊 Stats"])

    # --- FEED TAB ---
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
                            <span style="font-size:12px; color:{c['subtext']}">{row.get('Date time').split('•')[0] if '•' in str(row.get('Date time')) else row.get('Date time')}</span>
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
                    
                    # Action Bar
                    ac1, ac2, ac3, ac4 = st.columns([1, 1, 1, 6])
                    with ac1:
                        likes = row.get('Likes') or 0
                        btn_label = "❤️" if int(likes) > 0 else "🤍"
                        if st.button(btn_label, key=f"like_{i}"):
                            sh.update_cell(i + 2, 5, int(likes) + 1)
                            st.rerun()
                    with ac2:
                        st.markdown(f"<div style='font-size:20px; padding-top:5px; cursor:pointer;'>💬</div>", unsafe_allow_html=True)
                    with ac3:
                        st.markdown(f"<div style='font-size:20px; padding-top:5px; cursor:pointer;'>🚀</div>", unsafe_allow_html=True)
                    
                    # Caption
                    st.markdown(f"""
                    <div style="padding: 0px 12px 15px 12px;">
                        <div style="font-weight: 600; font-size: 14px; margin-bottom: 4px;">{likes} likes</div>
                        <span style="font-weight: 600; font-size: 14px;">{row.get('Name')}</span>
                        <span style="font-size: 14px;">Ate <b>{row.get('Calories')} kcal</b> today! 🥑</span>
                        <div style="color: {c['subtext']}; font-size: 12px; margin-top: 5px; text-transform: uppercase;">{row.get('Date time')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.write("") 
        else:
            st.info("No posts yet. Be the first!")

    # --- UPLOAD TAB ---
    with tab_log:
        st.write("")
        with st.container(border=True):
            st.markdown(f"<div style='padding:15px; font-weight:600; color:{c['text']}'>New Post</div>", unsafe_allow_html=True)
            
            # --- INPUTS OUTSIDE FORM ---
            st.markdown(f"<div style='padding-left:15px; font-size:14px; color:{c['text']}'>Choose Source</div>", unsafe_allow_html=True)
            input_type = st.radio("Input Source", ["Upload", "Camera"], horizontal=True, label_visibility="collapsed")
            
            final_file = None
            if input_type == "Upload":
                final_file = st.file_uploader("Choose file", type=['jpg','png'], label_visibility="collapsed")
            else:
                final_file = st.camera_input("Take photo", label_visibility="collapsed")

            st.divider()

            # --- DATA FORM ---
            with st.form("entry_form", clear_on_submit=True):
                f1, f2 = st.columns([1, 2])
                with f1:
                    st.image("https://ui-avatars.com/api/?background=ddd&name=?", width=60)
                with f2:
                    name = st.selectbox("Select User", ["JB", "Juvy"], label_visibility="collapsed")
                    st.caption("Posting as " + name)
                
                cals = st.number_input("Calories (kcal)", 0, 2000, 400, step=50)
                
                c3, c4 = st.columns(2)
                d_date = c3.date_input("Date")
                d_time = c4.time_input("Time")
                
                st.write("")
                submit = st.form_submit_button("Share Post", use_container_width=True)

                if submit:
                    if final_file:
                        with st.spinner("Posting..."):
                            try:
                                img_b64 = image_to_base64(final_file)
                                if len(img_b64) > 50000:
                                    st.error(f"Image too large. Try another.")
                                else:
                                    ts = datetime.combine(d_date, d_time).strftime("%b %d • %I:%M %p")
                                    sh.append_row([name, ts, img_b64, cals, 0])
                                    st.success("Shared!")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    else:
                        st.warning("Please add an image!")

    # --- STATS TAB ---
    with tab_stats:
        st.write("")
        if not df.empty:
            col_jb, col_vs, col_juvy = st.columns([2,1,2])
            
            with col_jb:
                st.markdown(f"<div style='text-align:center'><h1 style='color:{c['text']}; margin:0'>{int(df[df['Name']=='JB']['Calories'].sum())}</h1><p style='color:{c['subtext']}'>JB Calories</p></div>", unsafe_allow_html=True)
            
            with col_juvy:
                st.markdown(f"<div style='text-align:center'><h1 style='color:{c['text']}; margin:0'>{int(df[df['Name']=='Juvy']['Calories'].sum())}</h1><p style='color:{c['subtext']}'>Juvy Calories</p></div>", unsafe_allow_html=True)

            st.divider()
            st.caption("Activity Log")
            st.bar_chart(df.groupby("Name")["Calories"].sum(), color="#d62976")

# ---------------- PROFILE VIEW ----------------
elif st.session_state.view == 'profile':
    user = st.session_state.selected_user
    
    # Filter Data for User
    user_df = df[df['Name'] == user] if not df.empty else pd.DataFrame()
    total_cals = int(user_df['Calories'].sum()) if not user_df.empty else 0
    total_posts = len(user_df)

    # Profile Header
    c_p1, c_p2 = st.columns([1, 2])
    with c_p1:
        st.image(f"https://ui-avatars.com/api/?background=random&color=fff&name={user}&size=150", width=100)
    with c_p2:
        st.markdown(f"<h2 style='margin:0; padding:0;'>{user}</h2>", unsafe_allow_html=True)
        st.caption("Daily Eats Creator")
        
    # Stats Row
    s1, s2, s3 = st.columns(3)
    s1.metric("Posts", total_posts)
    s2.metric("Total Cals", total_cals)
    s3.metric("Avg Cals", int(total_cals/total_posts) if total_posts > 0 else 0)

    st.divider()
    
    # User Grid/Feed
    st.subheader(f"📸 {user}'s History")
    
    if not user_df.empty:
        # Simple grid view (2 columns)
        grid_cols = st.columns(2)
        for idx, (i, row) in enumerate(user_df.iloc[::-1].iterrows()):
            with grid_cols[idx % 2]:
                with st.container(border=True):
                    img_str = row.get('Image', '')
                    if str(img_str).startswith('data:'):
                        st.image(img_str, use_container_width=True)
                    st.caption(f"{row.get('Calories')} kcal • {row.get('Date time')}")
    else:
        st.info(f"{user} hasn't eaten anything yet! 🍽️")
