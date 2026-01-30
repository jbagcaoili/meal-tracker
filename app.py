import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# ---------------- CONFIGURATION ----------------
st.set_page_config(page_title="Visual Meal Tracker", page_icon="📸")

# ---------------- FUNCTIONS ----------------
def image_to_base64(image_file):
    """Converts uploaded file to a small base64 string for the sheet."""
    img = Image.open(image_file)
    # Resize to thumbnail (300px) to prevent hitting Google Sheets cell limits
    img.thumbnail((300, 300)) 
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_str}"

# ---------------- CONNECT TO DATABASE ----------------
# This looks for your secrets in .streamlit/secrets.toml or Streamlit Cloud Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# Fetch data (Expected columns: Name, Date time, Image)
# We catch errors in case the sheet is empty or headers are wrong
try:
    data = conn.read(worksheet="Sheet1", usecols=list(range(3)), ttl=5)
    data = data.dropna(how="all")
except Exception:
    st.warning("Could not read data. Make sure your Sheet has headers: Name, Date time, Image")
    data = pd.DataFrame(columns=["Name", "Date time", "Image"])

# ---------------- SIDEBAR: LOG ENTRY ----------------
st.sidebar.header("📸 Log Food")

with st.sidebar.form(key="log_form"):
    # Header 1: Name (Who is eating?)
    name = st.selectbox("Name", ["Me", "Partner"]) 
    
    # Header 2: Date Time
    d_date = st.date_input("Date", datetime.now())
    d_time = st.time_input("Time", datetime.now())
    
    # Header 3: Image
    uploaded_file = st.file_uploader("Take a photo", type=['jpg', 'png', 'jpeg'])
    if not uploaded_file:
        # Fallback for mobile camera if file upload isn't used
        uploaded_file = st.camera_input("Or take a picture")

    submit = st.form_submit_button("Save Meal")

if submit and uploaded_file:
    # Process the image
    image_data = image_to_base64(uploaded_file)
    
    # Format Date Time
    dt_string = f"{d_date} {d_time}"

    # Create Payload
    new_entry = pd.DataFrame(
        [{"Name": name, "Date time": dt_string, "Image": image_data}]
    )

    # Append and Update
    updated_df = pd.concat([data, new_entry], ignore_index=True)
    conn.update(worksheet="Sheet1", data=updated_df)
    
    st.success("Photo saved!")
    st.rerun()

# ---------------- DASHBOARD ----------------
st.title("🍛 Food Gallery")

if not data.empty:
    # Display the Dataframe with the Image Column rendered
    st.dataframe(
        data,
        column_config={
            "Name": "Who",
            "Date time": "When",
            "Image": st.column_config.ImageColumn(
                "Food Snap", help="Double click to preview"
            ),
        },
        use_container_width=True,
        hide_index=True,
        height=600
    )
else:
    st.info("No meals logged yet. Use the sidebar to add one!")
