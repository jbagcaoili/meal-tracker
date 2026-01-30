import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# ---------------- CONFIGURATION ----------------
st.set_page_config(page_title="Meal Tracker", page_icon="🥗", layout="centered")

# ---------------- CUSTOM STYLING (The "Pretty" Part) ----------------
# This CSS mimics the mobile app look (Orange/Teal, Cards, Shadows)
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* Hide standard header */
    header {visibility: hidden;}
    
    /* Custom Card Style */
    .meal-card {
        background-color: white;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border-left: 5px solid #FF6B6B; /* Coral accent */
    }
    
    /* Top Header Style */
    .main-header {
        background-color: #FF6B6B;
        padding: 30px;
        border-radius: 0 0 30px 30px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        margin-top: -60px; /* Pull it to the very top */
    }
    
    /* Text Styles */
    .sub-text { color: #888; font-size: 14px; }
    .bold-text { font-weight: bold; font-size: 18px; color: #333; }
    
    /* Button Override */
    .stButton>button {
        background-color: #FF6B6B;
        color: white;
        border-radius: 50px;
        height: 50px;
        width: 100%;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #FF4B4B;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- FUNCTIONS ----------------
def image_to_base64(image_file):
    img = Image.open(image_file)
    img.thumbnail((400, 400)) # Slightly larger thumbnail for the "Feed" look
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_str}"

# ---------------- DATABASE ----------------
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    data = conn.read(worksheet="Sheet1", usecols=list(range(3)), ttl=5)
    data = data.dropna(how="all")
except:
    data = pd.DataFrame(columns=["Name", "Date time", "Image"])

# ---------------- UI LAYOUT ----------------

# 1. The "App Header" (Orange Box)
st.markdown(f"""
<div class="main-header">
    <h1>🔥 Daily Tracker</h1>
    <p>Keeping up with JB & Juvy</p>
</div>
""", unsafe_allow_html=True)

# 2. Main Action Area (Tabs for "Feed" and "Add")
tab1, tab2 = st.tabs(["🍛 Food Feed", "📸 Log Meal"])

# --- TAB 1: THE FEED (Looks like the "Food Diary" in your screenshot) ---
with tab1:
    if not data.empty:
        # Sort by date (newest first)
        try:
            # Quick fix to ensure sorting works if date formats vary
            data = data.iloc[::-1] 
        except:
            pass
            
        for index, row in data.iterrows():
            # We use HTML injection to make it look exactly like a mobile card
            st.markdown(f"""
            <div class="meal-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div class="bold-text">{row['Name']}</div>
                    <div class="sub-text">{row['Date time']}</div>
                </div>
                <img src="{row['Image']}" style="width: 100%; border-radius: 15px;">
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No meals yet! Click 'Log Meal' to start.")

# --- TAB 2: LOGGING (Clean Input Form) ---
with tab2:
    st.markdown("### New Entry")
    with st.form(key="log_form", clear_on_submit=True):
        name = st.selectbox("Who is eating?", ["JB", "Juvy"]) 
        
        # Simple Date/Time layout
        c1, c2 = st.columns(2)
        with c1:
            d_date = st.date_input("Date", datetime.now())
        with c2:
            d_time = st.time_input("Time", datetime.now())
        
        uploaded_file = st.file_uploader("Upload Photo", type=['jpg', 'png', 'jpeg'])
        camera_file = st.camera_input("Or Take Photo")
        
        # Logic to pick whichever file was used
        final_file = uploaded_file if uploaded_file else camera_file
        
        submit = st.form_submit_button("✅ Save to Diary")

    if submit and final_file:
        image_data = image_to_base64(final_file)
        # Format Date nicely (e.g., "Jan 31, 12:30 PM")
        dt_obj = datetime.combine(d_date, d_time)
        dt_string = dt_obj.strftime("%b %d, %I:%M %p")

        new_entry = pd.DataFrame(
            [{"Name": name, "Date time": dt_string, "Image": image_data}]
        )

        updated_df = pd.concat([data, new_entry], ignore_index=True)
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("Added!")
        st.rerun()
