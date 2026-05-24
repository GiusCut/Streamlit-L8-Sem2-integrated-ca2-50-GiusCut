import streamlit as st
import pandas as pd
import plotly.express as px


# Page setup

st.set_page_config(
    page_title="Bakery Purchases Dashboard",
    layout="wide"
)

st.title("Bakery Purchases Dashboard")
st.write("Explore item popularity, monthly trends, order contents, and purchase times.")


# Load and prepare data

df = pd.read_csv("bread_basket_dataset.csv")

@st.cache_data
def prepare_data(df):
    bak_df = df.copy()

    bak_df["date_time"] = pd.to_datetime(bak_df["date_time"])
    bak_df["hour"] = bak_df["date_time"].dt.hour
    bak_df["month"] = bak_df["date_time"].dt.to_period("M").astype(str)
    bak_df["date"] = bak_df["date_time"].dt.date

    return bak_df


# This assumes your original dataframe is already called df.
# If you load from CSV instead, replace this with pd.read_csv(...)
bak_df = prepare_data(df)


# Options

period_options = ["all"] + sorted(bak_df["period_day"].unique())
day_type_options = ["all"] + sorted(bak_df["weekday_weekend"].unique())
transaction_options = sorted(bak_df["Transaction"].unique())


# Colors

colors = {
    "background": "linen",
    "sidebar": "antiquewhite",
    "text": "darkslategray",
    "helper_text": "dimgray",
    "main_chart_color": "sienna"
}


# Sidebar controls

text_size = 18

st.sidebar.header("Filters")

st.sidebar.write("Use the filters to explore bakery purchases by item, time, and order structure.")

selected_period = st.sidebar.selectbox(
    "Select period of day",
    period_options
)

selected_day_type = st.sidebar.selectbox(
    "Select weekday or weekend",
    day_type_options
)

top_n = st.sidebar.slider(
    "Items to display, starting from the most frequent",
    min_value=5,
    max_value=20,
    value=10,
    step=5
)

if st.sidebar.checkbox("Show raw data"):
    st.subheader("Raw data")
    st.write(bak_df)


# Shared filtering

filtered_df = bak_df.copy()

if selected_period != "all":
    filtered_df = filtered_df[filtered_df["period_day"] == selected_period]

if selected_day_type != "all":
    filtered_df = filtered_df[filtered_df["weekday_weekend"] == selected_day_type]


# Section 1: Top bakery items

st.header("Top bakery items")
st.write("Use the sidebar to filter results and explore bakery behavior.")

item_counts = (
    filtered_df["Item"]
    .value_counts()
    .head(top_n)
    .reset_index()
)

item_counts.columns = ["Item", "Count"]

fig_top_items = px.bar(
    item_counts,
    x="Count",
    y="Item",
    orientation="h",
    title="Top Bakery Items by Count",
    text="Count",
)

fig_top_items.update_layout(
    font_size=text_size,
    title_font_size=text_size + 6,
    xaxis_title="Amount",
    yaxis_title="Item",
    yaxis={"categoryorder": "total ascending"},
    xaxis={"range": [0, item_counts["Count"].max() * 1.20]},
    plot_bgcolor=colors["background"],
    paper_bgcolor=colors["background"],
    font_color=colors["text"],
)

fig_top_items.update_traces(
    marker_color=colors["main_chart_color"],
    textposition="outside",
    texttemplate="%{text}",
    cliponaxis=False,
)

st.plotly_chart(fig_top_items, use_container_width=True)


# Section 2: Monthly evolution

st.header("Monthly Evolution of Top Bakery Items")
st.write(
    "Use the sidebar to filter results and explore bakery behavior over time. "
    "October 2016 and April 2017 are partial months, so compare them carefully."
)

top_items = (
    filtered_df["Item"]
    .value_counts()
    .head(top_n)
    .index
    .tolist()
)

monthly_df = filtered_df[filtered_df["Item"].isin(top_items)]

monthly_counts = (
    monthly_df
    .groupby(["month", "Item"])
    .size()
    .reset_index(name="Count")
)

month_order = sorted(bak_df["month"].unique())

complete_index = pd.MultiIndex.from_product(
    [month_order, top_items],
    names=["month", "Item"]
)

monthly_counts = (
    monthly_counts
    .set_index(["month", "Item"])
    .reindex(complete_index, fill_value=0)
    .reset_index()
)

max_count = monthly_counts["Count"].max()
dynamic_height = max(600, top_n * 45)

fig_monthly = px.bar(
    monthly_counts,
    x="Count",
    y="Item",
    orientation="h",
    animation_frame="month",
    title="Monthly Evolution of Top Bakery Items",
    text="Count",
    height=dynamic_height,
)

fig_monthly.update_layout(
    font_size=text_size,
    title_font_size=text_size + 6,
    xaxis_title="Amount",
    yaxis_title="Item",
    yaxis={"categoryorder": "total ascending"},
    xaxis={"range": [0, max_count * 1.30]},
    plot_bgcolor=colors["background"],
    paper_bgcolor=colors["background"],
    font_color=colors["text"],
    margin={"l": 160, "r": 140, "t": 90, "b": 90},
    transition={"duration": 800},
)

fig_monthly.update_traces(
    marker_color=colors["main_chart_color"],
    textposition="outside",
    texttemplate="%{text}",
    cliponaxis=False,
)

st.plotly_chart(fig_monthly, use_container_width=True)


# Section 3: Order contents

st.header("Order contents")
st.write("Select a transaction number to visualize its contents.")

selected_transaction = st.selectbox(
    "Transaction number",
    transaction_options
)

order_df = bak_df[bak_df["Transaction"] == selected_transaction].copy()

order_items = (
    order_df["Item"]
    .value_counts()
    .reset_index()
)

order_items.columns = ["Item", "Quantity"]

st.dataframe(order_items, use_container_width=True)


# Section 4: Item popularity by hour

st.header("Item popularity by hour")
st.write(
    "Use the sidebar to restrict contents and hover over the bubbles to see details. "
    "Larger bubbles indicate more unique transactions."
)

bubble_df_source = filtered_df.copy()

top_items_for_bubble = (
    bubble_df_source["Item"]
    .value_counts()
    .head(top_n)
    .index
    .tolist()
)

bubble_df_source = bubble_df_source[
    bubble_df_source["Item"].isin(top_items_for_bubble)
]

bubble_df = (
    bubble_df_source
    .groupby(["hour", "Item"])["Transaction"]
    .nunique()
    .reset_index(name="Transactions")
)

dynamic_height = max(800, top_n * 55)

fig_bubble = px.scatter(
    bubble_df,
    x="hour",
    y="Item",
    size="Transactions",
    color="Transactions",
    color_continuous_scale="OrRd",
    title="Item Popularity by Hour",
    size_max=40,
    height=dynamic_height,
)

fig_bubble.update_layout(
    font_size=text_size,
    title_font_size=text_size + 6,
    xaxis_title="Hour of day",
    yaxis_title="Item",
    plot_bgcolor=colors["background"],
    paper_bgcolor=colors["background"],
    font_color=colors["text"],
    margin={"l": 180, "r": 120, "t": 90, "b": 90},
    xaxis={
        "tickmode": "array",
        "tickvals": list(range(0, 24)),
        "range": [6, 24],
        "tickangle": -45,
    },
)

st.plotly_chart(fig_bubble, use_container_width=True)