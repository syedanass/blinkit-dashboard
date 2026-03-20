import streamlit as st
import pandas as pd
import altair as alt
import snowflake.connector
from cryptography.hazmat.primitives import serialization

st.set_page_config(page_title="Blinkit Analytics Dashboard", page_icon="🛒", layout="wide")

@st.cache_resource
def get_connection():
    sf = st.secrets["snowflake"]
    p_key = serialization.load_pem_private_key(sf["private_key"].encode(), password=None)
    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return snowflake.connector.connect(
        account=sf["account"],
        user=sf["user"],
        private_key=pkb,
        warehouse=sf["warehouse"],
        role=sf["role"],
    )

conn = get_connection()

def run_query(sql):
    cur = conn.cursor()
    cur.execute(sql)
    df = cur.fetch_pandas_all()
    cur.close()
    return df

@st.cache_data(ttl=600)
def load_orders():
    return run_query("SELECT * FROM BLINKIT_DW.RAW.BLINKIT_ORDERS")

@st.cache_data(ttl=600)
def load_order_items():
    return run_query("SELECT * FROM BLINKIT_DW.RAW.BLINKIT_ORDER_ITEMS")

@st.cache_data(ttl=600)
def load_delivery():
    return run_query("SELECT * FROM BLINKIT_DW.RAW.BLINKIT_DELIVERY_PERFORMANCE")

@st.cache_data(ttl=600)
def load_marketing():
    return run_query("SELECT * FROM BLINKIT_DW.RAW.BLINKIT_MARKETING_PERFORMANCE")

orders = load_orders()
order_items = load_order_items()
delivery = load_delivery()
marketing = load_marketing()

orders["ORDER_DATE"] = pd.to_datetime(orders["ORDER_DATE"])
marketing["DATE"] = pd.to_datetime(marketing["DATE"])

st.title("Blinkit Analytics Dashboard")

with st.sidebar:
    st.header("Filters")

    min_date = orders["ORDER_DATE"].min().date()
    max_date = orders["ORDER_DATE"].max().date()
    date_range = st.date_input("Order Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    all_statuses = orders["DELIVERY_STATUS"].dropna().unique().tolist()
    selected_status = st.multiselect("Delivery Status", all_statuses, default=all_statuses)

    all_payments = orders["PAYMENT_METHOD"].dropna().unique().tolist()
    selected_payment = st.multiselect("Payment Method", all_payments, default=all_payments)

    all_channels = marketing["CHANNEL"].dropna().unique().tolist()
    selected_channel = st.multiselect("Marketing Channel", all_channels, default=all_channels)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

mask = (
    (orders["ORDER_DATE"].dt.date >= start_date)
    & (orders["ORDER_DATE"].dt.date <= end_date)
    & (orders["DELIVERY_STATUS"].isin(selected_status))
    & (orders["PAYMENT_METHOD"].isin(selected_payment))
)
f_orders = orders[mask]
f_order_ids = set(f_orders["ORDER_ID"])
f_items = order_items[order_items["ORDER_ID"].isin(f_order_ids)]
f_delivery = delivery[delivery["ORDER_ID"].isin(f_order_ids)]
f_marketing = marketing[
    (marketing["DATE"].dt.date >= start_date)
    & (marketing["DATE"].dt.date <= end_date)
    & (marketing["CHANNEL"].isin(selected_channel))
]

total_orders = len(f_orders)
total_revenue = f_orders["ORDER_TOTAL"].sum()
avg_order_value = f_orders["ORDER_TOTAL"].mean() if total_orders > 0 else 0
on_time_count = len(f_orders[f_orders["DELIVERY_STATUS"] == "On Time"])
on_time_pct = (on_time_count / total_orders * 100) if total_orders > 0 else 0
total_spend = f_marketing["SPEND"].sum()
avg_roas = f_marketing["ROAS"].mean() if len(f_marketing) > 0 else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Orders", f"{total_orders:,}")
col2.metric("Total Revenue", f"₹{total_revenue:,.2f}")
col3.metric("Avg Order Value", f"₹{avg_order_value:,.2f}")
col4.metric("On-Time %", f"{on_time_pct:.1f}%")
col5.metric("Mkt Spend", f"₹{total_spend:,.2f}")
col6.metric("Avg ROAS", f"{avg_roas:.2f}x")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Orders Over Time")
    daily = f_orders.groupby(f_orders["ORDER_DATE"].dt.date).size().reset_index(name="Orders")
    daily.columns = ["Date", "Orders"]
    daily["Date"] = pd.to_datetime(daily["Date"])
    chart = alt.Chart(daily).mark_area(opacity=0.5, color="#4F8BF9").encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("Orders:Q", title="Orders"),
        tooltip=["Date:T", "Orders:Q"]
    )
    st.altair_chart(chart, use_container_width=True)

with col2:
    st.subheader("Revenue by Payment Method")
    pay_rev = f_orders.groupby("PAYMENT_METHOD")["ORDER_TOTAL"].sum().reset_index()
    pay_rev.columns = ["Payment Method", "Revenue"]
    chart = alt.Chart(pay_rev).mark_arc(innerRadius=50).encode(
        theta=alt.Theta("Revenue:Q"),
        color=alt.Color("Payment Method:N"),
        tooltip=["Payment Method:N", alt.Tooltip("Revenue:Q", format=",.2f")]
    )
    st.altair_chart(chart, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    st.subheader("Delivery Status Distribution")
    status_counts = f_orders["DELIVERY_STATUS"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    chart = alt.Chart(status_counts).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X("Status:N", title="Status", sort="-y"),
        y=alt.Y("Count:Q", title="Count"),
        color=alt.Color("Status:N", legend=None),
        tooltip=["Status:N", "Count:Q"]
    )
    st.altair_chart(chart, use_container_width=True)

with col4:
    st.subheader("Avg Delivery Time (min)")
    if len(f_delivery) > 0 and "DELIVERY_TIME_MINUTES" in f_delivery.columns:
        avg_by_status = f_delivery.groupby("DELIVERY_STATUS")["DELIVERY_TIME_MINUTES"].mean().reset_index()
        avg_by_status.columns = ["Status", "Avg Minutes"]
        chart = alt.Chart(avg_by_status).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X("Status:N", title="Status", sort="-y"),
            y=alt.Y("Avg Minutes:Q", title="Minutes"),
            color=alt.Color("Status:N", legend=None),
            tooltip=["Status:N", alt.Tooltip("Avg Minutes:Q", format=".1f")]
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No delivery data available for selected filters.")

st.divider()
st.subheader("Marketing Performance")

col5, col6 = st.columns(2)

with col5:
    st.markdown("**Spend vs Revenue by Channel**")
    ch_perf = f_marketing.groupby("CHANNEL").agg(
        Spend=("SPEND", "sum"),
        Revenue=("REVENUE_GENERATED", "sum")
    ).reset_index()
    melted = ch_perf.melt(id_vars="CHANNEL", var_name="Metric", value_name="Amount")
    chart = alt.Chart(melted).mark_bar().encode(
        x=alt.X("Metric:N", title=""),
        y=alt.Y("Amount:Q", title="Amount"),
        color=alt.Color("Metric:N"),
        column=alt.Column("CHANNEL:N", title="Channel"),
        tooltip=["CHANNEL:N", "Metric:N", alt.Tooltip("Amount:Q", format=",.2f")]
    ).properties(width=100)
    st.altair_chart(chart, use_container_width=True)

with col6:
    st.markdown("**Conversions by Channel**")
    conv = f_marketing.groupby("CHANNEL")["CONVERSIONS"].sum().reset_index()
    conv.columns = ["Channel", "Conversions"]
    chart = alt.Chart(conv).mark_arc(innerRadius=50).encode(
        theta=alt.Theta("Conversions:Q"),
        color=alt.Color("Channel:N"),
        tooltip=["Channel:N", "Conversions:Q"]
    )
    st.altair_chart(chart, use_container_width=True)

st.subheader("Top 10 Products by Quantity Sold")
if len(f_items) > 0:
    top_products = f_items.groupby("PRODUCT_ID")["QUANTITY"].sum().reset_index().nlargest(10, "QUANTITY")
    top_products["PRODUCT_ID"] = top_products["PRODUCT_ID"].astype(str)
    top_products.columns = ["Product ID", "Quantity"]
    chart = alt.Chart(top_products).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color="#4F8BF9").encode(
        x=alt.X("Quantity:Q", title="Quantity Sold"),
        y=alt.Y("Product ID:N", title="Product", sort="-x"),
        tooltip=["Product ID:N", "Quantity:Q"]
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("No order items data for selected filters.")

st.subheader("Delayed Delivery Reasons")
if len(f_delivery) > 0:
    delayed = f_delivery[f_delivery["REASONS_IF_DELAYED"].notna() & (f_delivery["REASONS_IF_DELAYED"] != "")]
    if len(delayed) > 0:
        reasons = delayed["REASONS_IF_DELAYED"].value_counts().reset_index()
        reasons.columns = ["Reason", "Count"]
        chart = alt.Chart(reasons).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color="#FF6B6B").encode(
            x=alt.X("Count:Q", title="Count"),
            y=alt.Y("Reason:N", title="Reason", sort="-x"),
            tooltip=["Reason:N", "Count:Q"]
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No delayed deliveries in selected filters.")
else:
    st.info("No delivery data available.")
