import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import altair as alt
import os

st.set_page_config(layout="wide")

@st.cache_data
def load_layout_data():
    df_layout = pd.read_csv("room_layout_with_dimensions.csv")
    for col in ["x0", "x1", "y0", "y1"]:
        df_layout[col] = pd.to_numeric(df_layout[col], errors="coerce")
    return df_layout.dropna(subset=["x0", "x1", "y0", "y1"])

@st.cache_data
def load_area_data():
    df_area = pd.read_csv("floor_plan_comparison.csv")
    # Clean columns and string data for merging
    df_area.columns = [col.strip() for col in df_area.columns]
    for col in ["Project", "Floor", "Room"]:
        df_area[col] = df_area[col].astype(str).str.strip()
    return df_area

# Load data
df_layout = load_layout_data()
df_area = load_area_data()

# Clean strings for merging
for col in ["project", "floor", "room"]:
    df_layout[col] = df_layout[col].astype(str).str.strip()

# Merge layout and area data
df = pd.merge(
    df_layout,
    df_area,
    left_on=["project", "floor", "room"],
    right_on=["Project", "Floor", "Room"],
    how="left"
)

rename_map = {
    "LIVING": "Living", "KITCHEN": "Kitchen", "UTILITY": "Utility", "PARKING": "Parking",
    "GUEST BEDROOM1": "Guest Bedroom", "ATTD.TOILET 1": "Toilet", "DRESS 1": "Dress",
    "MASTER BEDROOM 2": "Master Bedroom", "ATTD.TOILET 2": "Toilet", "DRESS 2": "Dress",
    "BALCONY": "Balcony", "CHILDREN BEDROOM 3": "Children Bedroom", "DRESS 3": "Dress",
    "ATTD.TOILET 3": "Toilet", "FAMILY ROOM": "Family Room", "SIT OUT": "Sit Out",
    "MASTER BEDROOM 4": "Master Bedroom", "ATTD.TOILET 4": "Toilet",
    "WASH AREA & C.TOILET": "Wash Area & Toilet", "BAR COUNTER": "Bar Counter", "TERRACE": "Terrace"
}

color_map = {
    "Living": "#a6cee3", "Kitchen": "#1f78b4", "Utility": "#b2df8a", "Parking": "#33a02c",
    "Guest Bedroom": "#fb9a99", "Toilet": "#e31a1c", "Dress": "#fdbf6f", "Master Bedroom": "#ff7f00",
    "Balcony": "#cab2d6", "Children Bedroom": "#6a3d9a", "Family Room": "#ffff99", "Sit Out": "#b15928",
    "Wash Area & Toilet": "#8dd3c7", "Bar Counter": "#ffffb3", "Terrace": "#bebada", "Other": "#cccccc"
}

def get_color(room_group):
    return color_map.get(room_group, color_map["Other"])

st.sidebar.title("🏘️ Floor Plan Comparison Tool")

projects = sorted(df["project"].unique())
floors = sorted(df["floor"].unique())
rooms = ["All"] + sorted(df["room"].unique())

project_a = st.sidebar.selectbox("Select project A", projects)
project_b = st.sidebar.selectbox("Select project B", projects, index=1 if len(projects) > 1 else 0)
selected_floors = st.sidebar.multiselect("Select floors to compare (stacked)", floors, default=floors)
highlight_room = st.sidebar.selectbox("Highlight room", rooms)

df["Room Grouped"] = df["room"].str.strip().map(rename_map).fillna("Other")

scale = 1.5
vertical_gap = 50

def add_room_traces(fig, df_proj, col, floors_to_show):
    floor_to_offset = {f: idx * vertical_gap for idx, f in enumerate(floors_to_show)}
    for floor in floors_to_show:
        df_floor = df_proj[df_proj["floor"] == floor]
        y_offset = floor_to_offset[floor]
        for idx, row in df_floor.iterrows():
            room_color = get_color(row["Room Grouped"])
            if highlight_room != "All" and row["room"] == highlight_room:
                room_color = "red"

            x0_scaled = row["x0"] * scale
            x1_scaled = row["x1"] * scale
            y0_scaled = (row["y0"] + y_offset) * scale
            y1_scaled = (row["y1"] + y_offset) * scale

            length = row.get("Length (ft)", "N/A")
            breadth = row.get("Breadth (ft)", "N/A")
            area = row.get("Area (sqft)", "N/A")

            text = (
                f"Room: {row['room']}<br>"
                f"Floor: {floor}<br>"
                f"Length: {length} ft<br>"
                f"Breadth: {breadth} ft<br>"
                f"Area: {area} sqft"
            )

            fig.add_trace(
                go.Scatter(
                    x=[x0_scaled, x1_scaled, x1_scaled, x0_scaled, x0_scaled],
                    y=[y0_scaled, y0_scaled, y1_scaled, y1_scaled, y0_scaled],
                    fill="toself",
                    fillcolor=room_color,
                    line=dict(color="black"),
                    mode="lines",
                    name=row["Room Grouped"],
                    showlegend=False,
                    hoverinfo="text",
                    text=text,
                ),
                row=1, col=col
            )
            fig.add_trace(
                go.Scatter(
                    x=[(x0_scaled + x1_scaled) / 2],
                    y=[(y0_scaled + y1_scaled) / 2],
                    mode="text",
                    text=[row["room"]],
                    showlegend=False,
                    hoverinfo="skip",
                    textfont=dict(color="black", size=10),
                ),
                row=1, col=col
            )

df_a = df[df["project"] == project_a]
df_b = df[df["project"] == project_b]

fig = make_subplots(rows=1, cols=2, subplot_titles=[project_a, project_b], horizontal_spacing=0.1)

add_room_traces(fig, df_a, col=1, floors_to_show=selected_floors)
add_room_traces(fig, df_b, col=2, floors_to_show=selected_floors)

max_x = max(
    (df_a["x1"] * scale).max() if not df_a.empty else 100,
    (df_b["x1"] * scale).max() if not df_b.empty else 100
) + 10

max_y = max(
    ((df_a["y1"] + vertical_gap * (len(selected_floors) - 1)) * scale).max() if not df_a.empty else 100,
    ((df_b["y1"] + vertical_gap * (len(selected_floors) - 1)) * scale).max() if not df_b.empty else 100
) + 10

for i in [1, 2]:
    fig.update_xaxes(visible=False, scaleanchor=f"y{i}", scaleratio=1, row=1, col=i, range=[-10, max_x])
    fig.update_yaxes(visible=False, autorange="reversed", row=1, col=i, range=[-10, max_y])

fig.update_layout(
    height=800,
    margin=dict(l=10, r=10, t=50, b=10),
    showlegend=False,
    title_text=f"Floor Plans: {project_a} vs {project_b} (Floors: {', '.join(selected_floors)})",
)

st.plotly_chart(fig, use_container_width=True)

# Show floor plan images side by side if available
col1, col2 = st.columns(2)

with col1:
    image_path_a = f"images/{project_a.replace(' ', '_')}_{selected_floors[0]}.jpg" if selected_floors else None
    if image_path_a and os.path.exists(image_path_a):
        st.image(image_path_a, caption=f"{project_a} - {selected_floors[0]}", use_container_width=True)
    else:
        st.info(f"No image found for {project_a} - {selected_floors[0]}")

with col2:
    image_path_b = f"images/{project_b.replace(' ', '_')}_{selected_floors[0]}.jpg" if selected_floors else None
    if image_path_b and os.path.exists(image_path_b):
        st.image(image_path_b, caption=f"{project_b} - {selected_floors[0]}", use_container_width=True)
    else:
        st.info(f"No image found for {project_b} - {selected_floors[0]}")

# ==== ADD ALTair bar charts here ====

st.subheader("Total Built-up Area by Project")

# Filter area data for selected projects and floors only
df_area_filtered = df_area[
    (df_area["Project"].isin([project_a, project_b])) &
    (df_area["Floor"].isin(selected_floors))
]

total_area = df_area_filtered.groupby("Project")["Area (sqft)"].sum().reset_index()

bar_chart = alt.Chart(total_area).mark_bar().encode(
    x=alt.X("Project:N", sort="-y"),
    y="Area (sqft):Q",
    tooltip=["Project", "Area (sqft)"],
    color="Project:N"
).properties(width=700, height=400)

st.altair_chart(bar_chart, use_container_width=True)

st.subheader("Room Area Comparison")

room_chart = alt.Chart(df_area_filtered).mark_bar().encode(
    x=alt.X("Room:N", sort=None),
    y=alt.Y("Area (sqft):Q"),
    color=alt.Color("Project:N"),
    tooltip=["Project", "Floor", "Room", "Length (ft)", "Breadth (ft)", "Area (sqft)"]
).properties(width=700, height=400).interactive()

st.altair_chart(room_chart, use_container_width=True)

st.markdown("""
