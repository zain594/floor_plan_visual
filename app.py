import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import os

# Load CSV data
@st.cache_data
def load_data():
    return pd.read_csv("floor_plan_comparison.csv")

df = load_data()

# Sidebar selectors
floor = st.selectbox("Select Floor", sorted(df["Floor"].unique()))

col1, col2 = st.columns(2)
with col1:
    project_a = st.selectbox("Project A", sorted(df["Project"].unique()), key="proj_a")
with col2:
    project_b = st.selectbox("Project B", sorted(df["Project"].unique()), key="proj_b")

# Filter data by floor and project
df_a = df[(df["Project"] == project_a) & (df["Floor"] == floor)]
df_b = df[(df["Project"] == project_b) & (df["Floor"] == floor)]

# Room selector
common_rooms = sorted(set(df_a["Room"]).intersection(set(df_b["Room"])))
selected_room = st.selectbox("Highlight Room (if exists in both)", ["All"] + common_rooms)

# Coordinate generator
def add_coordinates(df_subset):
    df_subset = df_subset.copy()
    current_y = 0
    x_origin = 0
    for i, row in df_subset.iterrows():
        try:
            length = float(row["Length (ft)"])
            breadth = float(row["Breadth (ft)"])
        except:
            continue
        df_subset.at[i, "x0"] = x_origin
        df_subset.at[i, "x1"] = x_origin + breadth
        df_subset.at[i, "y0"] = current_y
        df_subset.at[i, "y1"] = current_y + length
        current_y += length + 2  # spacing
    return df_subset

# Add coordinates
df_a = add_coordinates(df_a)
df_b = add_coordinates(df_b)

# Plotting function
def plot_project(df_project, project_name):
    fig = go.Figure()
    for _, row in df_project.iterrows():
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
            font=dict(size=10)
        )
    fig.update_layout(
        title=f"{project_name} - {floor}",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
        height=400,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    return fig

# Show visuals
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(plot_project(df_a, project_a), use_container_width=True)
    image_path_a = f"images/{project_a.replace(' ', '_')}_{floor}.jpg"
    if os.path.exists(image_path_a):
        st.image(image_path_a, caption=f"{project_a} - {floor}", use_container_width=True)
    else:
        st.warning(f"No image found for {project_a} - {floor}")

with col2:
    st.plotly_chart(plot_project(df_b, project_b), use_container_width=True)
    image_path_b = f"images/{project_b.replace(' ', '_')}_{floor}.jpg"
    if os.path.exists(image_path_b):
        st.image(image_path_b, caption=f"{project_b} - {floor}", use_container_width=True)
    else:
        st.warning(f"No image found for {project_b} - {floor}")


