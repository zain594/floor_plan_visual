import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv("room_layout_coordinates.csv")  # CSV with Project, Floor, Room, x0, y0, x1, y1

df = load_data()

# Sidebar
st.sidebar.title("🏘️ Floor Plan Comparison Tool")

projects = sorted(df["project"].unique())
floors = sorted(df["Floor"].unique())
rooms = ["All"] + sorted(df["Room"].unique())

project_a = st.sidebar.selectbox("Select project A", projects)
project_b = st.sidebar.selectbox("Select project B", projects, index=1 if len(projects) > 1 else 0)
floor = st.sidebar.selectbox("Select Floor", floors)
selected_room = st.sidebar.selectbox("Highlight Room", rooms)

# Filter data
df_a = df[(df["project"] == project_a) & (df["Floor"] == floor)]
df_b = df[(df["project"] == project_b) & (df["Floor"] == floor)]

def plot_project(df_project, project_name):
    fig = go.Figure()
    for _, row in df_project.iterrows():
        # Highlight selected room or show default color
        color = "#ff6961" if selected_room != "All" and row["Room"] == selected_room else "lightblue"
        fig.add_shape(
            type="rect",
            x0=row["x0"], x1=row["x1"], y0=row["y0"], y1=row["y1"],
            line=dict(color="black"), fillcolor=color
        )
        fig.add_annotation(
            x=(row["x0"] + row["x1"]) / 2,
            y=(row["y0"] + row["y1"]) / 2,
            text=row["Room"],
            showarrow=False,
            font=dict(size=10),
            align="center"
        )
    fig.update_layout(
        title=f"{project_name} - {floor}",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
        height=500,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    return fig

# Layout columns for comparison
col1, col2 = st.columns(2)

with col1:
    if df_a.empty:
        st.warning(f"No data for {project_a} on floor {floor}")
    else:
        st.plotly_chart(plot_project(df_a, project_a), use_container_width=True)
        # Show image if exists
        image_path_a = f"images/{project_a.replace(' ', '_')}_{floor}.jpg"
        if os.path.exists(image_path_a):
            st.image(image_path_a, caption=f"{project_a} - {floor}", use_container_width=True)
        else:
            st.info(f"No image found for {project_a} - {floor}")

with col2:
    if df_b.empty:
        st.warning(f"No data for {project_b} on floor {floor}")
    else:
        st.plotly_chart(plot_project(df_b, project_b), use_container_width=True)
        image_path_b = f"images/{project_b.replace(' ', '_')}_{floor}.jpg"
        if os.path.exists(image_path_b):
            st.image(image_path_b, caption=f"{project_b} - {floor}", use_container_width=True)
        else:
            st.info(f"No image found for {project_b} - {floor}")

st.markdown("""
---
Built with ❤️ to compare residential projects room-by-room visually.  
Ensure your CSV includes columns: `Project`, `Floor`, `Room`, `x0`, `y0`, `x1`, `y1`.
""")
