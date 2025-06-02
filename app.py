import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import altair as alt

st.set_page_config(layout="wide")
st.title("Residential Project Floor Plan & Area Comparison")

# Load CSV data
@st.cache_data
def load_data():
    return pd.read_csv("floor_plan_visual/floor_plan_comparison.csv")

df_area = load_data()

# Sidebar project selectors
projects = df_area["Project"].unique().tolist()
project_a = st.sidebar.selectbox("Select Project A", projects, index=0)
project_b = st.sidebar.selectbox("Select Project B", projects, index=1 if len(projects) > 1 else 0)

# Floors available in either project
floors_a = df_area[df_area["Project"] == project_a]["Floor"].unique()
floors_b = df_area[df_area["Project"] == project_b]["Floor"].unique()
common_floors = sorted(set(floors_a) | set(floors_b))
selected_floors = st.sidebar.multiselect("Select Floors", common_floors, default=common_floors)

# Function to draw Plotly floor plan for a project and floor
def plot_floor_plan(project, floor):
    df = df_area[
        (df_area["Project"] == project) &
        (df_area["Floor"] == floor) &
        (df_area["Area (sqft)"] > 0)
    ]

    if df.empty:
        return None

    fig = go.Figure()
    for _, row in df.iterrows():
        length = row["Length (ft)"]
        breadth = row["Breadth (ft)"]
        area = row["Area (sqft)"]
        room = row["Room"]

        # Represent room as rectangle starting at (0,0), stacked vertically by index for example
        # (You can improve with real coordinates if available)
        x0, y0 = 0, 0
        fig.add_trace(go.Scatter(
            x=[x0, x0 + length, x0 + length, x0, x0],
            y=[y0, y0, y0 + breadth, y0 + breadth, y0],
            fill="toself",
            name=f"{room} ({area:.1f} sqft)",
            text=f"{room}<br>Length: {length} ft<br>Breadth: {breadth} ft<br>Area: {area:.1f} sqft",
            hoverinfo="text",
            mode="lines",
            line=dict(width=2)
        ))

    fig.update_layout(
        title=f"{project} - {floor} Floor Plan (Approx.)",
        xaxis_title="Length (ft)",
        yaxis_title="Breadth (ft)",
        yaxis=dict(scaleanchor="x", scaleratio=1),
        height=500,
        showlegend=True
    )
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=True)

    return fig

# Show floor plan images side by side
col1, col2 = st.columns(2)
with col1:
    st.subheader(f"{project_a} Floor Plans")
    for floor in selected_floors:
        st.markdown(f"**{floor}**")
        img_path = f"floor_plan_visual/{project_a}_{floor}.png"
        try:
            st.image(img_path, use_column_width=True)
        except Exception:
            st.info(f"No floor plan image for {project_a} {floor}")

with col2:
    st.subheader(f"{project_b} Floor Plans")
    for floor in selected_floors:
        st.markdown(f"**{floor}**")
        img_path = f"floor_plan_visual/{project_b}_{floor}.png"
        try:
            st.image(img_path, use_column_width=True)
        except Exception:
            st.info(f"No floor plan image for {project_b} {floor}")

st.markdown("---")

# Show Plotly floor plans side by side
col1, col2 = st.columns(2)
with col1:
    st.subheader(f"{project_a} Floor Plan Visualizations")
    for floor in selected_floors:
        fig = plot_floor_plan(project_a, floor)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No floor plan data for {project_a} {floor}")

with col2:
    st.subheader(f"{project_b} Floor Plan Visualizations")
    for floor in selected_floors:
        fig = plot_floor_plan(project_b, floor)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No floor plan data for {project_b} {floor}")

st.markdown("---")
st.header("🏠 Built-up Area Summary")

# Total area summary for the two projects only
df_area_summary = (
    df_area[df_area["Project"].isin([project_a, project_b])]
    .groupby("Project")["Area (sqft)"]
    .sum()
    .reset_index()
    .sort_values("Area (sqft)", ascending=False)
)

bar_area = (
    alt.Chart(df_area_summary)
    .mark_bar()
    .encode(
        x=alt.X("Project", sort="-y"),
        y=alt.Y("Area (sqft)", title="Total Built-up Area (sqft)"),
        tooltip=["Project", "Area (sqft)"],
        color=alt.Color("Project", legend=None),
    )
    .properties(width=600, height=300)
)

st.altair_chart(bar_area, use_container_width=True)

st.header("📊 Room Area Comparison by Floor and Project")

room_area_filtered = df_area[
    (df_area["Project"].isin([project_a, project_b])) &
    (df_area["Floor"].isin(selected_floors)) &
    (df_area["Area (sqft)"] > 0)
]

bar_room = (
    alt.Chart(room_area_filtered)
    .mark_bar()
    .encode(
        x=alt.X("Room", sort=None, title="Room"),
        y=alt.Y("Area (sqft)", title="Area (sqft)"),
        color=alt.Color("Project"),
        column=alt.Column("Floor", header=alt.Header(title="Floor")),
        tooltip=["Project", "Floor", "Room", "Area (sqft)"],
    )
    .properties(width=150, height=300)
    .interactive()
)

st.altair_chart(bar_room, use_container_width=True)
