import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# ---------------- CONFIGURATION ----------------
st.set_page_config(page_title="Daily Eats", page_icon="🥑", layout="centered")

# ---------------- SESSION STATE (The Brains) ----------------
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

def toggle_theme():
    if st.session_state.theme == 'dark':
        st.session_state.theme = 'light'
    else:
        st.session_state.theme = 'dark'

# ---------------- DYNAMIC CSS ENGINE ----------------
# We define color palettes for both modes here
themes = {
    "light": {
        "bg": "#F1F5F9",
        "card_bg": "#FFFFFF",
        "text": "#1E293B",
        "sub_text": "#64748B",
        "input_bg": "#F8FAFC",
        "border": "#E2E8F0",
        "shadow": "rgba(148, 163, 184, 0.15)",
        "accent": "linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)" # Indigo/Purple
    },
    "dark": {
        "bg": "#0F172A",
        "card_bg": "#1E293B",
        "text": "#F8FAFC",
        "sub_text": "#94A3B8",
        "input_bg": "#334155",
        "border": "#475569",
        "shadow": "rgba(0, 0, 0, 0.3)",
        "accent": "linear-gradient(135deg, #38BDF8 0%, #818CF8 100%)" # Sky/Indigo
    }
}

current_theme = themes[st.session_state.theme]

# Inject CSS based on current selection
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* Global Reset */
    .stApp {{
        background-color: {current_theme['bg']};
        color: {current_theme['text']};
        font-family: 'Inter', sans-serif;
    }}
    
    /* Hide Default Header/Footer */
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .block-container {{ padding-top: 3rem; max-width: 550px; }}

    /* MODERN CARD STYLING */
    .stContainer {{
        background-color: {current_theme['card_bg']};
        border-radius: 24px;
        padding: 24px;
        border: 1px solid {current_theme['border']};
        box-shadow: 0 10px 25px -5px {current_theme['shadow']};
    }}

    /* INPUT FIELDS (The "Sleek" Look) */
    .stTextInput input, .stSelectbox div, .stNumberInput input, .stDateInput input, .stTimeInput input {{
        background-color: {current_theme['input_bg']} !important;
        color: {current_theme['text']} !important;
        border: 1px solid {current_theme['border']} !important;
        border-radius: 12px !important;
        height: 48px;
        font-size: 15px;
    }}
    
    /* Focus State for Inputs */
    .stTextInput input:focus, .stNumberInput input:focus {{
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }}

    /* PRIMARY BUTTON */
    .stButton>button {{
        background: {current_theme['accent']};
        color: white;
        border: none;
        border-radius: 16px;
        height: 56px;
        font-weight: 700;
        font-size: 16px;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 12px {current_theme['shadow']};
        transition: all 0.2s ease;
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px {current_theme['shadow']};
    }}

    /* TYPOGRAPHY */
    h1, h2, h3 {{ font-weight: 800; letter-spacing: -0.5px; color: {current_theme['text']}; }}
    p, label {{ color: {current_theme['sub_text']}; font-size: 14px; font-weight: 500; }}
    
    /* TABS */
    button[data-baseweb="tab"] {{
        background-color: transparent !important;
        color: {current_theme['sub_text']};
        font-weight: 600;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {current_theme['text']};
        background-color: {current_theme['card_bg']} !important;
        border-radius: 10px;
        box-shadow: 0 2px 10px {current_theme['shadow']};
    }}
</style>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def image_to_base64(image_file):
    img = Image.open(image_file)
    img.thumbnail((500, 500))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85) # Better quality
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

# ---------------- DATABASE ----------------
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Sheet1", ttl=0)
    df = df.dropna(how="all")
    # Auto-fix missing columns to prevent crashes
    required_cols = ["Name", "Date time", "Image", "Calories", "Likes"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0 if col in ["Calories", "Likes"] else ""
except:
    df = pd.DataFrame(columns=["Name", "Date time", "Image", "Calories", "Likes"])

# ---------------- UI HEADER ----------------
# Theme Toggle Button (Top Right)
c1, c2 = st.columns([4, 1])
with c1:
    st.title("Daily Eats")
    st.caption("Tracking for JB & Juvy")
with c2:
    # The Toggle Switch
    btn_icon = "🌞" if st.session_state.theme == 'dark' else "🌙"
    st.button(btn_icon, on_click=toggle_theme, help="Toggle Theme")

# ---------------- MAIN TABS ----------------
tab_feed, tab_log, tab_stats = st.tabs(["🏠 Feed", "📝 Log", "📊 Stats"])

# --- TAB 1: FEED ---
with tab_feed:
    if not df.empty:
        df_display = df.iloc[::-1].reset_index(drop=True)
        
        for i, row in df_display.iterrows():
            with st.container():
                # Avatar & Info
                c_av, c_info = st.columns([1, 5])
                with c_av:
                    st.markdown(f"<div style='font-size:32px; text-align:center;'>{'🧑‍💻' if row['Name']=='JB' else '👩‍🔬'}</div>", unsafe_allow_html=True)
                with c_info:
                    st.markdown(f"**{row['Name']}**")
                    st.caption(f"{row['Date time']}")
                
                # Image
                st.image(row['Image'], use_container_width=True)
                
                # Action Bar
                c_cal, c_like, c_del = st.columns([2, 1, 1])
                with c_cal:
                     st.markdown(f"**{row['Calories']}** <span style='color:{current_theme['sub_text']};'>kcal</span>", unsafe_allow_html=True)
                with c_like:
                    # Logic to find the real index in the database
                    real_idx = df[df['Date time'] == row['Date time']].index[0]
                    if st.button(f"❤️ {int(row.get('Likes',0))}", key=f"like_{real_idx}"):
                        df.at[real_idx, "Likes"] = int(row.get("Likes",0)) + 1
                        conn.update(worksheet="Sheet1", data=df)
                        st.rerun()
                with c_del:
                    if st.button("🗑️", key=f"del_{real_idx}"):
                        df = df.drop(real_idx)
                        conn.update(worksheet="Sheet1", data=df)
                        st.rerun()
                
                st.write("") # Spacer
    else:
        st.info("Your feed is empty. Start logging!")

# --- TAB 2: LOGGING (Redesigned) ---
with tab_log:
    st.markdown("### New Entry")
    
    # We use a container to create the "Card" effect
    with st.container():
        with st.form("entry_form", clear_on_submit=True):
            
            # Row 1: Who & Calories
            c_name, c_cal = st.columns(2)
            with c_name:
                name = st.selectbox("Who is eating?", ["JB", "Juvy"])
            with c_cal:
                calories = st.number_input("Calories", min_value=0, step=50, value=400)
            
            # Row 2: Date & Time
            c_date, c_time = st.columns(2)
            with c_date:
                d_date = st.date_input("Date")
            with c_time:
                d_time = st.time_input("Time")
            
            # Row 3: Image
            st.markdown("---")
            st.markdown("**📸 Snap a photo**")
            
            # Custom styled file uploader hint
            uploaded_file = st.file_uploader("Upload", type=['jpg', 'png'], label_visibility="collapsed")
            camera_file = st.camera_input("Camera", label_visibility="collapsed")
            
            final_file = uploaded_file if uploaded_file else camera_file
            
            st.write("") # Spacer
            submitted = st.form_submit_button("Save to Diary")

    if submitted and final_file:
        img_data = image_to_base64(final_file)
        timestamp = datetime.combine(d_date, d_time).strftime("%b %d, %I:%M %p")
        
        new_row = pd.DataFrame([{
            "Name": name,
            "Date time": timestamp,
            "Calories": calories,
            "Image": img_data,
            "Likes": 0
        }])
        
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("Added successfully!")
        st.rerun()

# --- TAB 3: STATISTICS ---
with tab_stats:
    st.markdown("### Dashboard")
    with st.container():
        if not df.empty:
             df["Calories"] = pd.to_numeric(df["Calories"], errors='coerce').fillna(0)
             
             total = df["Calories"].sum()
             jb_cals = df[df["Name"]=="JB"]["Calories"].sum()
             juvy_cals = df[df["Name"]=="Juvy"]["Calories"].sum()
             
             c1, c2, c3 = st.columns(3)
             c1.metric("Total Tracked", f"{int(total)}")
             c2.metric("JB's Cals", f"{int(jb_cals)}")
             c3.metric("Juvy's Cals", f"{int(juvy_cals)}")
             
             st.markdown("---")
             st.caption("Weekly Breakdown")
             st.bar_chart(df.groupby("Name")["Calories"].sum(), color="#6366F1")
        else:
            st.info("No data available yet.")
