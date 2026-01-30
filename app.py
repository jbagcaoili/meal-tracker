import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# ---------------- CONFIGURATION ----------------
st.set_page_config(page_title="Daily Eats", page_icon="🥑", layout="centered")

# ---------------- PRO CSS STYLING ----------------
st.markdown("""
<style>
    /* 1. Global Reset & Dark Mode Base */
    .stApp {
        background-color: #0F172A; /* Midnight Blue */
        color: #F8FAFC;
    }
    
    /* 2. Remove default Header/Footer clutter */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 500px; /* Mobile width simulator */
    }

    /* 3. Custom Card Container */
    .stContainer {
        background-color: #1E293B;
        border-radius: 20px;
        padding: 20px;
        border: 1px solid #334155;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }

    /* 4. Styled Metrics (Stats) */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #38BDF8; /* Sky Blue */
    }
    div[data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #94A3B8;
    }

    /* 5. Inputs & Buttons */
    .stTextInput input, .stSelectbox div, .stNumberInput input {
        border-radius: 12px;
        background-color: #1E293B !important;
        color: white !important;
        border: 1px solid #475569 !important;
    }
    
    /* Primary Action Button (Gradient) */
    .stButton>button {
        background: linear-gradient(135deg, #0EA5E9 0%, #6366F1 100%);
        color: white;
        border: none;
        border-radius: 50px;
        font-weight: bold;
        height: 50px;
        transition: transform 0.1s;
    }
    .stButton>button:active {
        transform: scale(0.98);
    }
    
    /* Secondary Action Button (Delete/Like) - Make them subtle */
    div[data-testid="column"] .stButton>button {
        background: transparent;
        border: 1px solid #475569;
        height: 40px;
        font-size: 14px;
    }
    div[data-testid="column"] .stButton>button:hover {
        border-color: #94A3B8;
        background: #334155;
    }

    /* 6. Typography */
    h1 { font-family: 'Inter', sans-serif; font-weight: 800; letter-spacing: -1px; }
    p, label { font-family: 'Inter', sans-serif; color: #CBD5E1; }
</style>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def image_to_base64(image_file):
    img = Image.open(image_file)
    img.thumbnail((500, 500)) # High quality thumbnail
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

# ---------------- DATA ----------------
conn = st.connection("gsheets", type=GSheetsConnection)

# Initialize Data
try:
    df = conn.read(worksheet="Sheet1", ttl=0) # ttl=0 ensures instant updates
    df = df.dropna(how="all")
    # Ensure columns exist (backwards compatibility)
    for col in ["Likes", "Calories"]:
        if col not in df.columns:
            df[col] = 0
except:
    df = pd.DataFrame(columns=["Name", "Date time", "Image", "Calories", "Likes"])

# ---------------- UI: HEADER ----------------
c1, c2 = st.columns([1, 4])
with c1:
    st.image("https://cdn-icons-png.flaticon.com/512/3480/3480823.png", width=60)
with c2:
    st.title("Daily Eats")
    st.caption("Tracking for JB & Juvy")

# ---------------- UI: TABS ----------------
tab_feed, tab_log, tab_stats = st.tabs(["🏠 Feed", "➕ Log Meal", "📊 Stats"])

# --- TAB 1: THE FEED ---
with tab_feed:
    if not df.empty:
        # Show newest first
        df_display = df.iloc[::-1].reset_index(drop=True)
        
        for i, row in df_display.iterrows():
            # CARD CONTAINER
            with st.container():
                # 1. Header Row (Avatar + Name + Time)
                c_head1, c_head2 = st.columns([1, 5])
                with c_head1:
                    # Simple avatar based on name
                    avatar = "👨‍💻" if row['Name'] == "JB" else "👩‍🔬"
                    st.markdown(f"<div style='font-size:30px;'>{avatar}</div>", unsafe_allow_html=True)
                with c_head2:
                    st.markdown(f"**{row['Name']}**")
                    st.caption(f"{row['Date time']}")
                
                # 2. Hero Image
                st.image(row['Image'], use_container_width=True)
                
                # 3. Action Bar (Calories | Likes | Delete)
                c_act1, c_act2, c_act3 = st.columns([2, 1, 1])
                
                with c_act1:
                    st.markdown(f"🔥 **{row['Calories']}** <span style='color:#94A3B8; font-size:12px'>kcal</span>", unsafe_allow_html=True)
                
                with c_act2:
                    # Find original index to update the correct row in DB
                    original_idx = df[df['Date time'] == row['Date time']].index[0]
                    current_likes = int(row.get("Likes", 0))
                    
                    if st.button(f"❤️ {current_likes}", key=f"like_{original_idx}"):
                        df.at[original_idx, "Likes"] = current_likes + 1
                        conn.update(worksheet="Sheet1", data=df)
                        st.rerun()

                with c_act3:
                    if st.button("🗑️", key=f"del_{original_idx}"):
                        df = df.drop(original_idx)
                        conn.update(worksheet="Sheet1", data=df)
                        st.rerun()
                
                st.markdown("---") # Divider between cards
    else:
        st.info("No meals logged yet. Go to the 'Log Meal' tab!")

# --- TAB 2: LOG MEAL ---
with tab_log:
    st.markdown("### 📸 Snap a Meal")
    with st.form("entry_form", clear_on_submit=True):
        
        col_who, col_cal = st.columns(2)
        with col_who:
            name = st.selectbox("Who is eating?", ["JB", "Juvy"])
        with col_cal:
            calories = st.number_input("Calories", min_value=0, step=10, value=300)

        # Smart Date/Time
        col_d, col_t = st.columns(2)
        with col_d:
            d_date = st.date_input("Date")
        with col_t:
            d_time = st.time_input("Time")

        # Photo Input
        uploaded_file = st.file_uploader("Upload Image", type=['jpg', 'png'])
        camera_file = st.camera_input("Take Photo")
        final_file = uploaded_file if uploaded_file else camera_file

        submitted = st.form_submit_button("✨ Save to Feed")
    
    if submitted and final_file:
        # Processing
        img_data = image_to_base64(final_file)
        timestamp = datetime.combine(d_date, d_time).strftime("%b %d, %I:%M %p")
        
        new_row = pd.DataFrame([{
            "Name": name,
            "Date time": timestamp,
            "Calories": calories,
            "Image": img_data,
            "Likes": 0
        }])
        
        # Save
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("Meal logged!")
        st.rerun()

# --- TAB 3: STATISTICS ---
with tab_stats:
    st.markdown("### 📊 Dashboard")
    
    if not df.empty:
        # Convert calories to numeric just in case
        df["Calories"] = pd.to_numeric(df["Calories"], errors='coerce').fillna(0)
        
        # 1. Summary Cards
        col_stat1, col_stat2 = st.columns(2)
        
        total_cals = df["Calories"].sum()
        top_eater = df.groupby("Name")["Calories"].sum().idxmax()
        
        with col_stat1:
            st.metric("Total Tracked", f"{int(total_cals)} kcal")
        with col_stat2:
            st.metric("Top Eater", f"{top_eater}")

        # 2. Charts
        st.markdown("#### Weekly Breakdown")
        chart_data = df.groupby("Name")["Calories"].sum()
        st.bar_chart(chart_data, color="#38BDF8")
        
        st.markdown("#### Recent Activity")
        st.dataframe(
            df[["Name", "Date time", "Calories", "Likes"]].tail(5),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Log some meals to see stats!")
