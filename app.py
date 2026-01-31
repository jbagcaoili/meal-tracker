import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# ---------------- CONFIGURATION ----------------
st.set_page_config(page_title="Daily Eats", page_icon="🥑", layout="mobile")

# ---------------- THEME & CSS ----------------
# We force a "Food App" look with soft pinks, rounded corners, and shadows
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    /* APP BACKGROUND - Soft Warm White */
    .stApp {
        background-color: #FFF8F6; /* Very pale pinkish white */
    }

    /* HIDE HEADER */
    [data-testid="stHeader"] { visibility: hidden; }

    /* CARD STYLING */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border-radius: 20px; /* Big rounded corners */
        border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); /* Soft floaty shadow */
        padding: 15px;
    }

    /* BUTTONS - Pill Shaped & Red/Orange */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #FF4B4B, #FF6B6B);
        color: white;
        border: none;
        border-radius: 50px; /* Pill shape */
        height: 50px;
        font-weight: 600;
        box-shadow: 0 4px 10px rgba(255, 75, 75, 0.3);
    }

    /* INPUTS - Rounded */
    .stTextInput input, .stNumberInput input, .stDateInput input {
        border-radius: 15px;
        border: 1px solid #eee;
        background-color: #fcfcfc;
    }

    /* TABS - Clean & Minimal */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 20px;
        padding: 5px 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: none;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #FF4B4B;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE CONNECTION ----------------
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

# Helper: Shrink Image to Icon Size
def image_to_base64(image_file):
    img = Image.open(image_file)
    img.thumbnail((300, 300)) # Perfect size for grid cards
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=70) 
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

df = load_data()

# ---------------- UI LAYOUT ----------------

# App Title (Custom HTML for style)
st.markdown("<h1 style='text-align: center; color: #333; margin-bottom: -10px;'>🥑 Daily Eats</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888; font-size: 14px;'>Track your meals together</p>", unsafe_allow_html=True)
st.write("")

# Navigation Tabs
tab_feed, tab_log, tab_stats = st.tabs(["🔥 Feed", "➕ Add", "📊 Stats"])

# --- TAB 1: GRID FEED (Like the Reference Image) ---
with tab_feed:
    if not df.empty:
        # Create 2 Columns for the "Grid" look
        col1, col2 = st.columns(2)
        
        # Iterate through rows reversely
        for index, row in df.iloc[::-1].reset_index().iterrows():
            
            # Decide which column to put the card in (Zig-Zag)
            target_col = col1 if index % 2 == 0 else col2
            
            with target_col:
                with st.container(border=True):
                    # 1. Image (Top)
                    img_str = row.get('Image', '')
                    if str(img_str).startswith('data:'):
                        st.image(img_str, use_container_width=True)
                    
                    # 2. Food Details
                    st.markdown(f"**{row.get('Name')}**")
                    st.caption(f"🔥 {row.get('Calories')} kcal")
                    
                    # 3. Tiny Action Bar
                    c_date, c_like = st.columns([2, 1])
                    c_date.caption(f"{str(row.get('Date time')).split(' ')[0]}") # Just the date
                    
                    # Like Button logic (Simplified for grid)
                    real_idx = row['index'] + 2 # Adjust for header
                    likes = row.get('Likes') or 0
                    if c_like.button(f"❤️{likes}", key=f"like_{index}"):
                        sh.update_cell(real_idx, 5, int(likes) + 1)
                        st.rerun()

    else:
        st.info("No meals yet.")

# --- TAB 2: LOGGING (Clean Card) ---
with tab_log:
    with st.container(border=True):
        st.subheader("Snap a Meal")
        with st.form("entry_form", clear_on_submit=True):
            name = st.selectbox("Who is eating?", ["JB", "Juvy"])
            cals = st.number_input("Calories", 0, 2000, 400, step=50)
            
            c1, c2 = st.columns(2)
            d_date = c1.date_input("Date")
            d_time = c2.time_input("Time")
            
            photo = st.file_uploader("Upload", type=['jpg','png'])
            cam = st.camera_input("Camera")
            final_file = photo if photo else cam
            
            if st.form_submit_button("Post Meal"):
                if final_file:
                    with st.spinner("Uploading..."):
                        try:
                            img_b64 = image_to_base64(final_file)
                            if len(img_b64) > 50000:
                                st.error("Image too big!")
                                st.stop()

                            ts = datetime.combine(d_date, d_time).strftime("%b %d %H:%M")
                            sh.append_row([name, ts, cals, img_b64, 0])
                            st.success("Posted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Photo required!")

# --- TAB 3: PROFILE STATS ---
with tab_stats:
    if not df.empty:
        df['Calories'] = pd.to_numeric(df['Calories'], errors='coerce').fillna(0)
        
        # Profile Header Style
        st.markdown("### 🏆 Weekly Goals")
        
        with st.container(border=True):
            # Circular Progress effect using metrics
            c1, c2 = st.columns(2)
            c1.metric("JB", f"{int(df[df['Name']=='JB']['Calories'].sum())} kcal")
            c2.metric("Juvy", f"{int(df[df['Name']=='Juvy']['Calories'].sum())} kcal")
            
            st.divider()
            st.caption("Recent Activity")
            st.bar_chart(df.groupby("Name")["Calories"].sum(), color="#FF4B4B")
