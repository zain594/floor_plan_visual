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

# Normalize case to lowercase for merging and matching
df_layout["room_lc"] = df_layout["room"].str.lower().str.strip()
df_area["room_lc"] = df_area["Room"].str.lower().str.strip()
df_layout["project_lc"] = df_layout["project"].str.lower().str.strip()
df_area["project_lc"] = df_area["Project"].str.lower().str.strip()
df_layout["floor_lc"] = df_layout["floor"].str.lower().str.strip()
df_area["floor_lc"] = df_area["Floor"].str.lower().str.strip()

# Merge layout and area data on lowercase keys
df = pd.merge(
    df_layout,
    df_area,
    left_on=["project_lc", "floor_lc", "room_lc"],
    right_on=["project_lc", "floor_lc", "room_lc"],
    how="left",
    suffixes=('_layout', '_area')
)

# Rename map to group similar rooms under consistent names
rename_map = {
    "attd. toilet 1": "Toilet",
    "attd. toilet 2": "Toilet",
    "attd. toilet 3": "Toilet",
    "attd. toilet 4": "Toilet",
    "toilet 1": "Toilet",
    "toilet 2": "Toilet",
    "toilet 3": "Toilet",
    "toilet": "Toilet",
    "bedroom 1": "Bedroom",
    "bedroom 2": "Bedroom",
    "bedroom 3": "Bedroom",
    "bedroom 4": "Bedroom",
    "parents/guest bedroom": "Guest Bedroom",
    "guest bedroom": "Guest Bedroom",
    "family room": "Family Room",
    "drawing room": "Drawing Room",
    "living": "Living",
    "living room": "Living",
    "living/dining": "Living/Dining",
    "kitchen": "Kitchen",
    "utility": "Utility",
    "parking": "Parking",
    "dress 1": "Dress",
    "dress 2": "Dress",
    "dress 3": "Dress",
    "balcony": "Balcony",
    "bar counter": "Bar Counter",
    "deck": "Deck",
    "terrace": "Terrace",
    "sit out": "Sit Out",
    "study": "Study",
    "garden 1": "Garden",
    "garden 2": "Garden",
    "pooja": "Pooja",
    "walk-in": "Walk-In",
    "theatre/gym": "Theatre/Gym",
    "lobby": "Lobby",
    "wash area & c.toilet": "Wash Area & Toilet",
    "powder": "Toilet",
    "family": "Family Room",
    "dining": "Dining",
    # Add more mappings if needed
}

# Apply rename map to create a "Room Grouped" column
df["Room Grouped"] = df["room_lc"].map(rename_map).fillna("Other")

color_map = {
    "Toilet": "#e31a1c",
    "Bedroom": "#fb9a99",
    "Guest Bedroom": "#fdbf6f",
    "Family Room": "#ffff99",
    "Drawing Room": "#cab2d6",
    "Living": "#a6cee3",
    "Living/Dining": "#1f78b4",
    "Kitchen": "#b2df8a",
    "Utility": "#33a02c",
    "Parking": "#8dd3c7",
    "Dress": "#fbb4ae",
    "Balcony": "#bebada",
    "Bar Counter": "#ffffb3",
    "Deck": "#b15928",
    "Terrace": "#fb8072",
    "Sit Out": "#80b1d3",
    "Study": "#fccde5",
    "Garden": "#ccebc5",
    "Pooja": "#d9d9d9",
    "Walk-In": "#fdb462",
    "Theatre/Gym": "#bc80bd",
    "Lobby": "#ffffcc",
    "Wash Area & Toilet": "#8dd3c7",
    "Dining": "#fb9a99",
    "Other": "#cccccc"
}

def get_color(room_group):
    return color_map.get(room_group, color_map["Other"])

st.sidebar.title("🏘️ Floor Plan Comparison Tool")

projects = sorted(df["project"].unique())
floors = sorted(df["floor"].unique())

project_a = st.sidebar.selectbox("Select project A", projects)
project_b = st.sidebar.selectbox("Select project B", projects, index=1 if len(projects) > 1 else 0)
selected_floors = st.sidebar.multiselect("Select floors to compare (stacked)", floors, default=floors)

scale = 1.5
vertical_gap = 50

def add_room_traces(fig, df_proj, col, floors_to_show):
    floor_to_offset = {f: idx * vertical_gap for idx, f in enumerate(floors_to_show)}
    for floor in floors_to_show:
        df_floor = df_proj[df_proj["floor"] == floor]
        y_offset = floor_to_offset[floor]
        for idx, row in df_floor.iterrows():
            room_color = get_color(row["Room Grouped"])

            x0_scaled = row["x0"] * scale
            x1_scaled = row["x1"] * scale
            y0_scaled = (row["y0"] + y_offset) * scale
            y1_scaled = (row["y1"] + y_offset) * scale

            length = row.get("Length (ft)", "N/A")
            breadth = row.get("Breadth (ft)", "N/A")
            area = row.get("Area (sqft)", "N/A")

            # Fix for NaNs to show N/A
            length = length if pd.notna(length) else "N/A"
            breadth = breadth if pd.notna(breadth) else "N/A"
            area = area if pd.notna(area) else "N/A"

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
    (df_b["x1"] * scale).max() if not df_b.empty else 100,
) * 1.05

max_y = vertical_gap * len(selected_floors) * scale * 1.05

fig.update_layout(
    height=700,
    width=1200,
    title_text=f"Floor Plan Comparison: {project_a} vs {project_b}",
    showlegend=False,
)

fig.update_xaxes(range=[0, max_x], zeroline=False, showgrid=False, showticklabels=False)
fig.update_yaxes(range=[0, max_y], scaleanchor="x", scaleratio=1, zeroline=False, showgrid=False, showticklabels=False)

st.plotly_chart(fig, use_container_width=True)

# Summary data for area bar charts

# Compute total built-up area per project
df_total_area = df_area.groupby("Project")["Area (sqft)"].sum().reset_index()

st.markdown("### Total Built-up Area by Project")
bar_total = (
    alt.Chart(df_total_area)
    .mark_bar()
    .encode(
        x=alt.X("Project:N", sort="-y"),
        y=alt.Y("Area (sqft):Q"),
        color=alt.Color("Project:N"),
        tooltip=["Project", alt.Tooltip("Area (sqft):Q", format=".2f")],
    )
    .properties(width=600, height=300)
)

st.altair_chart(bar_total, use_container_width=True)

# Compute area by project and room group for stacked comparison
df_area_grouped = df.copy()
df_area_grouped["Area (sqft)"] = pd.to_numeric(df_area_grouped["Area (sqft)"], errors="coerce").fillna(0)
df_area_grouped_summary = (
    df_area_grouped.groupby(["Project", "Room Grouped"])["Area (sqft)"]
    .sum()
    .reset_index()
)

st.markdown("### Built-up Area by Room Type and Project")

bar_room = (
    alt.Chart(df_area_grouped_summary)
    .mark_bar()
    .encode(
        x=alt.X("Project:N", sort="-y"),
        y=alt.Y("Area (sqft):Q"),
        color=alt.Color("Room Grouped:N", scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values()))),
        tooltip=["Project", "Room Grouped", alt.Tooltip("Area (sqft):Q", format=".2f")],
    )
    .properties(width=800, height=400)
)

st.altair_chart(bar_room, use_container_width=True)
