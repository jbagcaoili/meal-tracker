import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Daily Eats", page_icon="🥗", layout="centered")

# ---------------- STATE ----------------
if "dark" not in st.session_state:
    st.session_state.dark = False

# ---------------- CSS ----------------
theme_bg = "#0f172a" if st.session_state.dark else "#f8fafc"
card_bg = "#1e293b" if st.session_state.dark else "#ffffff"
text_color = "#f1f5f9" if st.session_state.dark else "#1e293b"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
html, body, [class*="css"] {{
    font-family: 'Poppins', sans-serif;
    color: {text_color};
}}
.stApp {{
    background: {theme_bg};
}}
header, footer {{visibility: hidden;}}

.block-container {{
    max-width: 480px;
}}

.meal-card {{
    background: {card_bg};
    border-radius: 20px;
    padding: 14px;
    margin-bottom: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    animation: fadeIn 0.4s ease-in;
}}

@keyframes fadeIn {{
    from {{opacity:0; transform:translateY(5px);}}
    to {{opacity:1;}}
}}

.meal-header {{
    display:flex;
    justify-content:space-between;
    align-items:center;
}}

.meal-time {{
    font-size:12px;
    background:#fb7185;
    color:white;
    padding:4px 10px;
    border-radius:10px;
}}

.stButton>button {{
    border-radius:25px;
    height:52px;
    font-weight:600;
}}
</style>
""", unsafe_allow_html=True)

# ---------------- FUNCTIONS ----------------
def image_to_base64(image_file):
    img = Image.open(image_file)
    img.thumbnail((400, 400))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

# ---------------- DB ----------------
conn = st.connection("gsheets", type=GSheetsConnection)
try:
    data = conn.read(worksheet="Sheet1", ttl=5)
    data = data.dropna(how="all")
except:
    data = pd.DataFrame(columns=["Name", "Date time", "Calories", "Image", "Likes"])

# ---------------- HEADER ----------------
st.title("🥑 Daily Eats")
st.caption("Tracking for JB & Juvy")

col1, col2 = st.columns([3,1])
with col2:
    if st.button("🌙" if not st.session_state.dark else "☀️"):
        st.session_state.dark = not st.session_state.dark
        st.rerun()

tab_feed, tab_add, tab_stats = st.tabs(["Feed", "Add", "Stats"])

# ---------------- FEED ----------------
with tab_feed:
    if not data.empty:
        data = data.iloc[::-1]
        for i, row in data.iterrows():
            like_col, del_col = st.columns([5,1])
            with like_col:
                st.markdown(f"""
                <div class="meal-card">
                    <div class="meal-header">
                        <b>🍽 {row['Name']}</b>
                        <div class="meal-time">{row['Date time']}</div>
                    </div>
                    <p>🔥 {row['Calories']} kcal</p>
                    <img src="{row['Image']}" style="width:100%;border-radius:15px;">
                    <p>❤️ {int(row.get("Likes",0))}</p>
                </div>
                """, unsafe_allow_html=True)

            with del_col:
                if st.button("🗑", key=f"del{i}"):
                    data = data.drop(i)
                    conn.update(worksheet="Sheet1", data=data)
                    st.rerun()

            if st.button("❤️ Like", key=f"like{i}"):
                data.loc[i,"Likes"] = int(row.get("Likes",0)) + 1
                conn.update(worksheet="Sheet1", data=data)
                st.rerun()
    else:
        st.info("No meals yet.")

# ---------------- ADD ----------------
with tab_add:
    with st.form("add_form", clear_on_submit=True):
        name = st.selectbox("Who?", ["JB","Juvy"])
        c1,c2 = st.columns(2)
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
