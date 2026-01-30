import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Daily Eats", page_icon="🥑", layout="centered")

# ---------------- CSS ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

header, footer {
    visibility: hidden;
}

.stApp {
    background: radial-gradient(circle at top, #0f172a 0%, #020617 60%);
    color: #e5e7eb;
}

.block-container {
    max-width: 420px;
    padding-top: 1.2rem;
}

/* TITLE */
h1 {
    text-align: center;
    font-weight: 800;
    color: #f9fafb;
}
.subtitle {
    text-align: center;
    color: #9ca3af;
    margin-bottom: 1.5rem;
}

/* TABS */
button[data-baseweb="tab"] {
    font-size: 15px;
    font-weight: 600;
    color: #94a3b8;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #38bdf8;
    border-bottom: 3px solid #38bdf8;
}

/* CARDS */
.meal-card {
    background: rgba(30, 41, 59, 0.65);
    backdrop-filter: blur(14px);
    border-radius: 22px;
    padding: 14px;
    margin-bottom: 20px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.6);
    animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
    from {opacity:0; transform:translateY(6px);}
    to {opacity:1;}
}

.meal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.meal-name {
    font-weight: 700;
    font-size: 16px;
    color: #f9fafb;
}

.meal-time {
    font-size: 11px;
    background: linear-gradient(135deg, #38bdf8, #6366f1);
    padding: 4px 10px;
    border-radius: 999px;
    color: white;
}

.meal-card img {
    width: 100%;
    border-radius: 16px;
    margin-top: 10px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.7);
}

/* INPUTS */
.stSelectbox div[data-baseweb="select"],
.stDateInput input,
.stTimeInput input,
.stNumberInput input,
.stFileUploader {
    background: rgba(15, 23, 42, 0.8) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(148,163,184,0.15) !important;
    color: #f9fafb !important;
}

/* BUTTON */
.stButton>button {
    background: linear-gradient(135deg, #38bdf8, #6366f1);
    color: white;
    border-radius: 999px;
    height: 54px;
    width: 100%;
    font-size: 17px;
    font-weight: 700;
    border: none;
    box-shadow: 0 6px 30px rgba(56,189,248,0.5);
    transition: all 0.25s ease;
}

.stButton>button:hover {
    transform: translateY(-1px) scale(1.02);
    box-shadow: 0 10px 45px rgba(56,189,248,0.7);
}

/* CAMERA */
section[data-testid="stCameraInput"] {
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 8px 30px rgba(0,0,0,0.7);
}

/* ALERT */
div[data-testid="stAlert"] {
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- FUNCTIONS ----------------
def image_to_base64(image_file):
    img = Image.open(image_file)
    img.thumbnail((400, 400))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

# ---------------- DATABASE ----------------
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    data = conn.read(worksheet="Sheet1", ttl=5)
    data = data.dropna(how="all")
except:
    data = pd.DataFrame(columns=["Name", "Date time", "Calories", "Image", "Likes"])

# ---------------- HEADER ----------------
st.title("🥑 Daily Eats")
st.markdown('<div class="subtitle">Tracking for JB & Juvy</div>', unsafe_allow_html=True)

tab_feed, tab_add, tab_stats = st.tabs(["Feed", "Add", "Stats"])

# ---------------- FEED ----------------
with tab_feed:
    if not data.empty:
        data = data.iloc[::-1]
        for i, row in data.iterrows():
            col_card, col_del = st.columns([6,1])

            with col_card:
                st.markdown(f"""
                <div class="meal-card">
                    <div class="meal-header">
                        <div class="meal-name">🍽 {row['Name']}</div>
                        <div class="meal-time">{row['Date time']}</div>
                    </div>
                    <div style="color:#9ca3af;font-size:13px;margin-top:4px;">🔥 {row['Calories']} kcal</div>
                    <img src="{row['Image']}">
                    <div style="margin-top:8px;color:#f87171;">❤️ {int(row.get("Likes",0))}</div>
                </div>
                """, unsafe_allow_html=True)

            with col_del:
                if st.button("🗑", key=f"del{i}"):
                    data = data.drop(i)
                    conn.update(worksheet="Sheet1", data=data)
                    st.rerun()

            if st.button("❤️ Like", key=f"like{i}"):
                data.loc[i,"Likes"] = int(row.get("Likes",0)) + 1
                conn.update(worksheet="Sheet1", data=data)
                st.rerun()
    else:
        st.info("No meals yet. Add your first one!")

# ---------------- ADD ----------------
with tab_add:
    with st.form("add_form", clear_on_submit=True):
        name = st.selectbox("Who?", ["JB","Juvy"])

        c1, c2 = st.columns(2)
        with c1:
            d = st.date_input("Date", datetime.now())
        with c2:
            t = st.time_input("Time", datetime.now())

        calories = st.number_input("Calories", min_value=0)

        upload = st.file_uploader("Upload", type=["jpg","png","jpeg"])
        cam = st.camera_input("Camera")
        photo = upload if upload else cam

        submit = st.form_submit_button("✨ Save Meal")

    if submit and photo:
        img = image_to_base64(photo)
        dt = datetime.combine(d,t).strftime("%b %d • %I:%M %p")

        new = pd.DataFrame([{
            "Name": name,
            "Date time": dt,
            "Calories": calories,
            "Image": img,
            "Likes": 0
        }])

        data = pd.concat([data,new],ignore_index=True)
        conn.update(worksheet="Sheet1", data=data)
        st.success("Saved!")
        st.rerun()

# ---------------- STATS ----------------
with tab_stats:
    if not data.empty:
        data["Calories"] = pd.to_numeric(data["Calories"], errors="coerce")
        weekly = data.groupby("Name")["Calories"].sum()

        st.subheader("🔥 Weekly Calories")
        st.bar_chart(weekly)
    else:
        st.info("No data yet.")
