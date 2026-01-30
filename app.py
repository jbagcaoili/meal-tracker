import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# ---------------- CONFIGURATION ----------------
st.set_page_config(page_title="Meal Tracker", page_icon="🥗", layout="centered")

# ---------------- CUSTOM CSS (The "Pretty" Engine) ----------------
# This forces Streamlit to look like a mobile app
st.markdown("""
<style>
    /* 1. Main Background - Soft Gradient */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }

    /* 2. Hide default ugly header */
    header {visibility: hidden;}
    
    /* 3. Card Container for the Form */
    .block-container {
        padding-top: 2rem;
        max-width: 600px;
    }

    /* 4. Input Fields (Rounded & Soft) */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stDateInput input, .stTimeInput input {
        border-radius: 15px !important;
        border: 1px solid #ddd;
        padding: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }

    /* 5. The "Save" Button - Gradient & Rounded */
    .stButton>button {
        background: linear-gradient(45deg, #FF6B6B, #FF8E53);
        color: white;
        border: none;
        border-radius: 25px;
        height: 55px;
        width: 100%;
        font-size: 18px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.6);
    }

    /* 6. Food Feed Cards */
    .meal-card {
        background: white;
        border-radius: 20px;
        padding: 15px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .meal-card:active {
        transform: scale(0.98);
    }
    
    /* 7. Typography */
    h1 {
        color: #333;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        text-align: center;
        margin-bottom: 5px;
    }
    p {
        color: #666;
        text-align: center;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- FUNCTIONS ----------------
def image_to_base64(image_file):
    img = Image.open(image_file)
    img.thumbnail((400, 400)) 
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

st.title("🥑 Daily Eats")
st.markdown("<p>Tracking for JB & Juvy</p>", unsafe_allow_html=True)

# Navigation Tabs (Styled to look simpler)
tab_feed, tab_log = st.tabs(["Feed", "Add New"])

# --- TAB 1: THE FEED ---
with tab_feed:
    if not data.empty:
        # Reverse order to show newest first
        try:
            data = data.iloc[::-1]
        except:
            pass
            
        for index, row in data.iterrows():
            st.markdown(f"""
            <div class="meal-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div style="font-weight: bold; font-size: 18px; color: #444;">{row['Name']}</div>
                    <div style="font-size: 12px; color: #aaa; background: #f0f2f6; padding: 5px 10px; border-radius: 10px;">{row['Date time']}</div>
                </div>
                <img src="{row['Image']}" style="width: 100%; border-radius: 15px; object-fit: cover; max-height: 300px;">
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No meals yet. Go to 'Add New' to start!")

# --- TAB 2: LOGGING ---
with tab_log:
    with st.container():
        # We use a container to group inputs visually
        with st.form(key="log_form", clear_on_submit=True):
            
            # 1. Who?
            name = st.selectbox("Who is eating?", ["JB", "Juvy"]) 
            
            # 2. When? (Side by Side)
            c1, c2 = st.columns(2)
            with c1:
                # Standard date picker
                d_date = st.date_input("Date", datetime.now())
            with c2:
                # step=60 allows minute selection. 
                # On mobile, this triggers the scroll wheel.
                d_time = st.time_input("Time", datetime.now(), step=60)
            
            # 3. Photo
            uploaded_file = st.file_uploader("Upload", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
            camera_file = st.camera_input("Take Photo", label_visibility="collapsed")
            
            final_file = uploaded_file if uploaded_file else camera_file
            
            # Spacer
            st.write("")
            
            # 4. Big Beautiful Button
            submit = st.form_submit_button("✨ Save Meal")

        if submit and final_file:
            image_data = image_to_base64(final_file)
            dt_obj = datetime.combine(d_date, d_time)
            # Format: Jan 30 • 10:45 PM
            dt_string = dt_obj.strftime("%b %d • %I:%M %p")

            new_entry = pd.DataFrame(
                [{"Name": name, "Date time": dt_string, "Image": image_data}]
            )

            updated_df = pd.concat([data, new_entry], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.success("Saved!")
            st.rerun()
