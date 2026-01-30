import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# ---------------- CONFIGURATION ----------------
st.set_page_config(page_title="Daily Eats", page_icon="🥑", layout="centered")

# ---------------- SESSION STATE & THEME ----------------
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

# ---------------- MINIMALIST CSS ----------------
# We only style the BACKGROUND and BUTTONS. We leave inputs alone to prevent glitches.
theme_config = {
    "light": {"bg": "#ffffff", "text": "#333333", "accent": "#FF4B4B"},
    "dark": {"bg": "#0e1117", "text": "#ffffff", "accent": "#FF4B4B"}
}
current = theme_config[st.session_state.theme]

st.markdown(f"""
<style>
    /* 1. App Background */
    .stApp {{
        background-color: {current['bg']};
        color: {current['text']};
    }}
    
    /* 2. Hide Header/Footer */
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* 3. Center the layout content */
    .block-container {{
        max-width: 550px;
        padding-top: 2rem;
    }}

    /* 4. Styled "Primary" Buttons (Gradient) */
    div.stButton > button:first-child {{
        background: linear-gradient(to right, #ff4b4b, #ff6b6b);
        color: white;
        border: none;
        border-radius: 12px;
        height: 50px;
        font-weight: bold;
        width: 100%;
    }}
    div.stButton > button:hover {{
        opacity: 0.9;
    }}
    
    /* 5. Metrics styling */
    div[data-testid="stMetricValue"] {{
        font-size: 26px;
        color: {current['accent']};
    }}
</style>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def image_to_base64(image_file):
    img = Image.open(image_file)
    img.thumbnail((600, 600)) 
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

# ---------------- DATABASE ----------------
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Sheet1", ttl=0)
    df = df.dropna(how="all")
    # Auto-fix missing columns
    for col in ["Name", "Date time", "Image", "Calories", "Likes"]:
        if col not in df.columns:
            df[col] = 0 if col in ["Calories", "Likes"] else ""
except:
    df = pd.DataFrame(columns=["Name", "Date time", "Image", "Calories", "Likes"])

# ---------------- HEADER ----------------
c1, c2 = st.columns([5, 1])
with c1:
    st.title("🥑 Daily Eats")
    st.caption("Tracking for JB & Juvy")
with c2:
    # Clean Toggle Button
    icon = "🌙" if st.session_state.theme == 'light' else "☀️"
    if st.button(icon):
        toggle_theme()
        st.rerun()

# ---------------- TABS ----------------
tab_feed, tab_log, tab_stats = st.tabs(["feed", "log", "stats"])

# --- TAB 1: INSTAGRAM STYLE FEED ---
with tab_feed:
    if not df.empty:
        # Show newest first
        df_display = df.iloc[::-1].reset_index(drop=True)
        
        for i, row in df_display.iterrows():
            # USE NATIVE CONTAINER (Clean Border, No CSS Hacks)
            with st.container(border=True):
                # Header
                c_head1, c_head2 = st.columns([1, 5])
                with c_head1:
                    st.write("🧑‍🍳" if row['Name'] == "JB" else "👩‍🍳")
                with c_head2:
                    st.write(f"**{row['Name']}**")
                
                # Image (Hero)
                if row['Image'].startswith("data:"):
                    st.image(row['Image'], use_container_width=True)
                
                # Footer Info
                st.caption(f"{row['Date time']} • {row['Calories']} kcal")
                
                # Actions (Likes & Delete)
                c_like, c_del, c_space = st.columns([1, 1, 3])
                
                with c_like:
                    # Find real index
                    real_idx = df[df['Date time'] == row['Date time']].index[0]
                    likes = int(row.get("Likes", 0))
                    if st.button(f"❤️ {likes}", key=f"like_{real_idx}"):
                        df.at[real_idx, "Likes"] = likes + 1
                        conn.update(worksheet="Sheet1", data=df)
                        st.rerun()
                
                with c_del:
                    if st.button("🗑️", key=f"del_{real_idx}"):
                        df = df.drop(real_idx)
                        conn.update(worksheet="Sheet1", data=df)
                        st.rerun()
    else:
        st.info("No meals yet.")

# --- TAB 2: CLEAN LOGGING FORM ---
with tab_log:
    st.write("") # Spacer
    with st.container(border=True):
        st.subheader("New Entry")
        with st.form("entry_form", clear_on_submit=True):
            
            # Use Standard Streamlit columns for layout
            col1, col2 = st.columns(2)
            with col1:
                name = st.selectbox("Who?", ["JB", "Juvy"])
            with col2:
                calories = st.number_input("Kcal", min_value=0, step=50, value=400)
            
            col3, col4 = st.columns(2)
            with col3:
                d_date = st.date_input("Date")
            with col4:
                d_time = st.time_input("Time")
            
            st.divider()
            
            # File Uploader
            upload = st.file_uploader("Upload Photo", type=['jpg', 'png'])
            cam = st.camera_input("Or Take Photo")
            final_file = upload if upload else cam
            
            submitted = st.form_submit_button("Save Meal")
    
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
        st.success("Saved!")
        st.rerun()

# --- TAB 3: STATS DASHBOARD ---
with tab_stats:
    st.write("")
    if not df.empty:
        df["Calories"] = pd.to_numeric(df["Calories"], errors='coerce').fillna(0)
        
        # Summary Metrics
        with st.container(border=True):
            c1, c2 = st.columns(2)
            c1.metric("Total Calories", int(df["Calories"].sum()))
            c2.metric("Meals Tracked", len(df))
        
        # Chart
        st.subheader("Weekly Breakdown")
        st.bar_chart(df.groupby("Name")["Calories"].sum(), color="#FF4B4B")
    else:
        st.info("Log some meals to see stats!")
