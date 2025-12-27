"""Meal Planning Streamlit App."""

from __future__ import annotations

import streamlit as st
import plotly.express as px

from meal_planning.app import get_app_context

# Get services (auto-initializes if needed)
ctx = get_app_context()

st.set_page_config(page_title="Meal Planner", page_icon="", layout="wide")
st.title("Meal Planner")

# Load catalogue
dishes = ctx.catalogue.list_dishes()
dish_map = {d.name: d for d in dishes}

# === SIDEBAR: Filters ===
st.sidebar.header("Filters")
cuisines = sorted(set(d.cuisine.value for d in dishes))
selected_cuisine = st.sidebar.selectbox("Cuisine", ["All"] + cuisines)

# Filter dishes
if selected_cuisine != "All":
    filtered = [d for d in dishes if d.cuisine.value == selected_cuisine]
else:
    filtered = dishes

# === MAIN: Selection ===
col1, col2 = st.columns(2)

with col1:
    st.subheader("Catalogue")
    selected_names = st.multiselect(
        "Select dishes for your meal plan",
        options=[d.name for d in filtered],
        default=[],
    )

with col2:
    st.subheader("Shortlist")
    if selected_names:
        shortlist_data = [
            {"Name": d.name, "Cuisine": d.cuisine.value, "Region": d.region.value}
            for d in dishes
            if d.name in selected_names
        ]
        st.dataframe(shortlist_data, use_container_width=True)
        st.caption(f"Selected: {len(selected_names)} dishes")
    else:
        st.info("Select dishes from the catalogue")

# === PLAN GENERATION ===
st.divider()

if st.button("Generate Plan", type="primary", disabled=len(selected_names) < 1):
    selected_dishes = [dish_map[name] for name in selected_names]

    plan, result = ctx.planning.create_plan(
        name="Generated Plan",
        dishes=selected_dishes,
        weeks=4,
        dishes_per_week=4,
    )

    # Store in session state
    st.session_state["plan"] = plan
    st.session_state["plan_dishes"] = selected_dishes

# === DISPLAY PLAN ===
if "plan" in st.session_state:
    plan = st.session_state["plan"]
    plan_dishes = st.session_state["plan_dishes"]
    dish_uid_map = {d.uid: d for d in plan_dishes}

    st.subheader("Meal Plan")
    for i, week in enumerate(plan.weeks, 1):
        dish_names = [
            dish_uid_map[uid].name for uid in week.dishes if uid in dish_uid_map
        ]
        st.write(f"**Week {i}:** {', '.join(dish_names)}")

    # === ANALYSIS ===
    st.divider()
    st.subheader("Analysis")

    report = ctx.analysis.get_variety_report(plan.uid)

    if report:
        col1, col2 = st.columns(2)

        with col1:
            # Cuisine distribution
            if report.cuisine_distribution:
                cuisine_fig = px.bar(
                    x=list(report.cuisine_distribution.values()),
                    y=list(report.cuisine_distribution.keys()),
                    orientation="h",
                    title="Cuisine Distribution",
                )
                cuisine_fig.update_layout(
                    showlegend=False, xaxis_title="Count", yaxis_title=""
                )
                st.plotly_chart(cuisine_fig, use_container_width=True)

        with col2:
            # Region balance
            if report.region_distribution:
                region_fig = px.pie(
                    values=list(report.region_distribution.values()),
                    names=list(report.region_distribution.keys()),
                    title="Region Balance",
                )
                st.plotly_chart(region_fig, use_container_width=True)

        st.metric("Variety Score", f"{report.variety_score}/100")
