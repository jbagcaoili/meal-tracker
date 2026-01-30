import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
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

# Define colors for CSS injection
theme_cfg = {
    "light": {"bg": "#ffffff", "text": "#333333", "card": "#f8f9fa", "accent": "#FF4B4B"},
    "dark": {"bg": "#0e1117", "text": "#ffffff", "card": "#262730", "accent": "#FF4B4B"}
}
current = theme_cfg[st.session_state.theme]

# ---------------- CLEAN CSS (No Glitches) ----------------
st.markdown(f"""
<style>
    /* 1. Dynamic Background */
    .stApp {{
        background-color: {current['bg']};
        color: {current['text']};
    }}
    
    /* 2. Hide Clutter */
    header, footer {{visibility: hidden;}}
    .block-container {{padding-top: 2rem; max-width: 550px;}}

    /* 3. Sleek Primary Button */
    div.stButton > button:first-child {{
        background: linear-gradient(90deg, #FF4B4B 0%, #FF6B6B 100%);
        color: white;
        border: none;
        border-radius: 12px;
        height: 50px;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.2);
        transition: transform 0.1s ease;
    }}
    div.stButton > button:active {{
        transform: scale(0.98);
    }}

    /* 4. Secondary Action Buttons (Like/Delete) */
    div[data-testid="column"] button {{
        background-color: transparent;
        border: 1px solid #ddd;
        border-radius: 8px;
    }}
</style>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def image_to_base64(image_file):
    img = Image.open(image_file)
    img.thumbnail((600, 600)) 
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

# ---------------- DATABASE ----------------
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Sheet1", ttl=0)
    df = df.dropna(how="all")
    # Auto-repair missing columns
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
    # Theme Toggle
    icon = "🌙" if st.session_state.theme == 'light' else "☀️"
    if st.button(icon, key="theme_toggle"):
        toggle_theme()
        st.rerun()

# ---------------- TABS ----------------
tab_feed, tab_log, tab_stats = st.tabs(["Feed", "Log Meal", "Stats"])

# --- TAB 1: FEED ---
with tab_feed:
    if not df.empty:
        df_display = df.iloc[::-1].reset_index(drop=True)
        for i, row in df_display.iterrows():
            # CLEAN CARD (Using Native Streamlit Container)
            with st.container(border=True):
                # Header
                c_head1, c_head2 = st.columns([1, 5])
                with c_head1:
                    st.write("🧑‍🍳" if row['Name'] == "JB" else "👩‍🍳")
                with c_head2:
                    st.markdown(f"**{row['Name']}**")
                    st.caption(f"{row['Date time']}")
                
                # Image
                if str(row['Image']).startswith("data:"):
                    st.image(row['Image'], use_container_width=True)
                
                # Footer Actions
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.markdown(f"🔥 **{row['Calories']}** kcal")
                with c2:
                    # Like Logic
                    real_idx = df[df['Date time'] == row['Date time']].index[0]
                    likes = int(row.get("Likes", 0))
                    if st.button(f"❤️ {likes}", key=f"like_{real_idx}"):
                        df.at[real_idx, "Likes"] = likes + 1
                        conn.update(worksheet="Sheet1", data=df)
                        st.rerun()
                with c3:
                    # Delete Logic
                    if st.button("🗑️", key=f"del_{real_idx}"):
                        df = df.drop(real_idx)
                        conn.update(worksheet="Sheet1", data=df)
                        st.rerun()
    else:
        st.info("No meals yet. Start tracking!")

# --- TAB 2: LOGGING ---
with tab_log:
    st.write("")
    with st.container(border=True):
        st.subheader("New Entry")
        with st.form("entry_form", clear_on_submit=True):
            
            # Row 1
            col1, col2 = st.columns(2)
            with col1:
                name = st.selectbox("Who?", ["JB", "Juvy"])
            with col2:
                calories = st.number_input("Calories", min_value=0, step=50, value=400)
            
            # Row 2
            col3, col4 = st.columns(2)
            with col3:
                d_date = st.date_input("Date")
            with col4:
                d_time = st.time_input("Time")
            
            st.divider()
            
            # Photo
            upload = st.file_uploader("Upload Photo", type=['jpg', 'png'])
            cam = st.camera_input("Take Photo")
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

# --- TAB 3: STATS ---
with tab_stats:
    st.write("")
    if not df.empty:
        df["Calories"] = pd.to_numeric(df["Calories"], errors='coerce').fillna(0)
        
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            c1.metric("Total", f"{int(df['Calories'].sum())}")
            c2.metric("JB", f"{int(df[df['Name']=='JB']['Calories'].sum())}")
            c3.metric("Juvy", f"{int(df[df['Name']=='Juvy']['Calories'].sum())}")
        
        st.subheader("Weekly Trend")
        st.bar_chart(df.groupby("Name")["Calories"].sum(), color="#FF4B4B")
    else:
        st.info("Log some meals to see stats!")
