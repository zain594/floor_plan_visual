import streamlit as st
import pandas as pd
import plotly.express as px

# Load your CSV
df = pd.read_csv("floor_plan_comparison.csv")

# Sidebar filters
st.sidebar.header("Filter Options")
selected_project = st.sidebar.multiselect("Select Project", options=df["Project"].unique(), default=df["Project"].unique())
selected_floor = st.sidebar.multiselect("Select Floor", options=df["Floor"].unique(), default=df["Floor"].unique())

# Filter data
filtered_df = df[df["Project"].isin(selected_project) & df["Floor"].isin(selected_floor)]

# Page title
st.title("🏠 Floor Plan Comparison Dashboard")
import streamlit as st
from PIL import Image

st.subheader("📷 Ground Floor Plans")

# Project selector
project = st.selectbox("Choose Project", ["Bhavisha", "Saiven", "NCC"])

# Image mapping
image_map = {
    "Bhavisha": "images/bhavisha_GF.jpg",
    "Saiven": "images/saiven_GF.jpg",
    "NCC": "images/ncc_GF.jpg",
}

# Load and display
image_path = image_map.get(project)
if image_path:
    try:
        image = Image.open(image_path)
        st.image(image, caption=f"{project} - Ground Floor", use_container_width=True)
    except FileNotFoundError:
        st.warning("Image not found. Make sure it exists in the 'images' folder.")

# Show table
st.subheader("Data Table")
st.dataframe(filtered_df)

# Plot
st.subheader("📊 Room Area Comparison")
fig = px.bar(filtered_df,
             x="Room",
             y="Area (sqft)",
             color="Project",
             facet_col="Floor",
             barmode="group",
             title="Room Area by Project and Floor")

st.plotly_chart(fig, use_container_width=True)
