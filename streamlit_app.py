import streamlit as st
import pandas as pd
import altair as alt
import snowflake.connector
import base64

st.set_page_config(page_title="Blinkit Analytics Dashboard", page_icon="🛵", layout="wide")

DELIVERY_BOY_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" opacity="0.06">
  <g transform="translate(200, 80)">
    <circle cx="280" cy="60" r="30" fill="#0C831F"/>
    <rect x="258" y="90" width="44" height="55" rx="10" fill="#0C831F"/>
    <rect x="230" y="95" width="30" height="8" rx="4" fill="#0C831F" transform="rotate(-20, 245, 99)"/>
    <rect x="298" y="95" width="35" height="8" rx="4" fill="#0C831F" transform="rotate(15, 315, 99)"/>
    <rect x="330" y="80" width="45" height="55" rx="6" fill="#F9E51C" stroke="#0C831F" stroke-width="3"/>
    <text x="352" y="115" font-size="12" font-weight="bold" fill="#0C831F" text-anchor="middle">B</text>
    <rect x="260" y="145" width="12" height="50" rx="4" fill="#0C831F" transform="rotate(-10, 266, 170)"/>
    <rect x="286" y="145" width="12" height="50" rx="4" fill="#0C831F" transform="rotate(10, 292, 170)"/>
    <ellipse cx="220" cy="250" rx="45" ry="45" fill="none" stroke="#0C831F" stroke-width="8"/>
    <ellipse cx="380" cy="250" rx="45" ry="45" fill="none" stroke="#0C831F" stroke-width="8"/>
    <circle cx="220" cy="250" r="8" fill="#0C831F"/>
    <circle cx="380" cy="250" r="8" fill="#0C831F"/>
    <path d="M220 250 Q260 200 300 210 Q340 200 380 250" fill="none" stroke="#0C831F" stroke-width="8" stroke-linecap="round"/>
    <rect x="280" y="190" width="40" height="25" rx="5" fill="#0C831F"/>
    <path d="M300 210 L280 180 L260 100" fill="none" stroke="#0C831F" stroke-width="6" stroke-linecap="round"/>
    <path d="M300 210 L330 180 L340 95" fill="none" stroke="#0C831F" stroke-width="4" stroke-linecap="round"/>
    <rect x="260" y="165" width="20" height="6" rx="3" fill="#F9E51C"/>
    <rect x="325" y="165" width="20" height="6" rx="3" fill="#F9E51C"/>
    <path d="M180 250 L160 250" stroke="#0C831F" stroke-width="3" opacity="0.5"/>
    <path d="M140 250 L120 250" stroke="#0C831F" stroke-width="3" opacity="0.3"/>
    <path d="M100 250 L80 250" stroke="#0C831F" stroke-width="3" opacity="0.15"/>
  </g>
</svg>"""

DELIVERY_BOY_B64 = base64.b64encode(DELIVERY_BOY_SVG.encode()).decode()

BLINKIT_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 60">
  <rect width="200" height="60" rx="12" fill="#F9E51C"/>
  <text x="100" y="42" font-family="Arial Black, Arial, sans-serif" font-size="32" font-weight="900" text-anchor="middle">
    <tspan fill="#0C831F">blink</tspan><tspan fill="#2D2D2D">it</tspan>
  </text>
</svg>"""

BLINKIT_LOGO_B64 = base64.b64encode(BLINKIT_LOGO_SVG.encode()).decode()

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Poppins', sans-serif;
}}

[data-testid="stAppViewContainer"] {{
    background-image: url("data:image/svg+xml;base64,{DELIVERY_BOY_B64}");
    background-repeat: no-repeat;
    background-position: bottom right;
    background-size: 500px auto;
    background-attachment: fixed;
}}

[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0C831F 0%, #065216 50%, #043D10 100%);
    border-right: 3px solid #F9E51C;
}}
[data-testid="stSidebar"] * {{
    color: #FFFFFF !important;
}}
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stDateInput label {{
    color: #F9E51C !important;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.5px;
}}
[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {{
    padding-bottom: 0;
}}

[data-testid="stMetric"] {{
    background: linear-gradient(135deg, #0C831F 0%, #0A9E24 50%, #0BBF2A 100%);
    border-radius: 14px;
    padding: 18px 22px;
    color: #FFFFFF;
    box-shadow: 0 6px 20px rgba(12,131,31,0.35);
    border-left: 4px solid #F9E51C;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
[data-testid="stMetric"]:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(12,131,31,0.45);
}}
[data-testid="stMetric"] label {{
    color: #F9E51C !important;
    font-weight: 600;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    color: #FFFFFF !important;
    font-weight: 700;
}}

.blinkit-banner {{
    background: linear-gradient(135deg, #0C831F 0%, #0A6E1B 100%);
    border-radius: 16px;
    padding: 24px 32px;
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 10px;
    box-shadow: 0 8px 30px rgba(12,131,31,0.3);
    position: relative;
    overflow: hidden;
}}
.blinkit-banner::before {{
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(249,229,28,0.15) 0%, transparent 70%);
    border-radius: 50%;
}}
.blinkit-banner-logo {{
    flex-shrink: 0;
}}
.blinkit-banner-text {{
    color: #FFFFFF;
    z-index: 1;
}}
.blinkit-banner-text h2 {{
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
    color: #FFFFFF;
}}
.blinkit-banner-text p {{
    margin: 4px 0 0 0;
    color: rgba(255,255,255,0.8);
    font-size: 0.9rem;
}}
.blinkit-banner-rider {{
    position: absolute;
    right: 30px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 3rem;
    opacity: 0.3;
}}

.section-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    color: #0C831F;
    font-weight: 700;
    font-size: 1.25rem;
    border-left: 4px solid #F9E51C;
    padding-left: 14px;
    margin: 10px 0;
    background: linear-gradient(90deg, rgba(12,131,31,0.05) 0%, transparent 100%);
    border-radius: 0 8px 8px 0;
    padding: 8px 14px;
}}

.sidebar-logo {{
    text-align: center;
    padding: 10px 0 20px 0;
}}

hr {{
    border: none;
    height: 2px;
    background: linear-gradient(90deg, #F9E51C, #0C831F, #F9E51C);
    margin: 20px 0;
    opacity: 0.5;
}}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_connection():
    if "snowflake" in st.secrets:
        sf = st.secrets["snowflake"]
    elif "connections" in st.secrets and "snowflake" in st.secrets["connections"]:
        sf = st.secrets["connections"]["snowflake"]
    else:
        sf = st.secrets
    pkb = base64.b64decode(sf["private_key_b64"])
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

st.markdown(f"""
<div class="blinkit-banner">
    <div class="blinkit-banner-logo">
        <img src="data:image/svg+xml;base64,{BLINKIT_LOGO_B64}" width="160" alt="Blinkit Logo"/>
    </div>
    <div class="blinkit-banner-text">
        <h2>Analytics Dashboard</h2>
        <p>India's Last Minute App &mdash; delivering insights at speed</p>
    </div>
    <div class="blinkit-banner-rider">🛵💨</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-logo">
        <img src="data:image/svg+xml;base64,{BLINKIT_LOGO_B64}" width="140" alt="Blinkit"/>
        <p style="color: #F9E51C; font-size: 0.75rem; margin-top: 8px; letter-spacing: 1px;">ANALYTICS PORTAL</p>
    </div>
    """, unsafe_allow_html=True)
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
col2.metric("Total Revenue", f"\u20b9{total_revenue:,.2f}")
col3.metric("Avg Order Value", f"\u20b9{avg_order_value:,.2f}")
col4.metric("On-Time %", f"{on_time_pct:.1f}%")
col5.metric("Mkt Spend", f"\u20b9{total_spend:,.2f}")
col6.metric("Avg ROAS", f"{avg_roas:.2f}x")

st.divider()

BLINKIT_GREEN = "#0C831F"
BLINKIT_YELLOW = "#F9E51C"
BLINKIT_PALETTE = ["#0C831F", "#F9E51C", "#0BBF2A", "#FFD700", "#065216", "#FFF176"]

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-header">Orders Over Time</div>', unsafe_allow_html=True)
    daily = f_orders.groupby(f_orders["ORDER_DATE"].dt.date).size().reset_index(name="Orders")
    daily.columns = ["Date", "Orders"]
    daily["Date"] = pd.to_datetime(daily["Date"])
    chart = alt.Chart(daily).mark_area(
        opacity=0.6,
        line={"color": BLINKIT_GREEN, "strokeWidth": 2},
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color="rgba(12,131,31,0.4)", offset=0),
                alt.GradientStop(color="rgba(12,131,31,0.05)", offset=1)
            ],
            x1=0, x2=0, y1=0, y2=1
        )
    ).encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("Orders:Q", title="Orders"),
        tooltip=["Date:T", "Orders:Q"]
    )
    st.altair_chart(chart, use_container_width=True)

with col2:
    st.markdown('<div class="section-header">Revenue by Payment Method</div>', unsafe_allow_html=True)
    pay_rev = f_orders.groupby("PAYMENT_METHOD")["ORDER_TOTAL"].sum().reset_index()
    pay_rev.columns = ["Payment Method", "Revenue"]
    chart = alt.Chart(pay_rev).mark_arc(innerRadius=50).encode(
        theta=alt.Theta("Revenue:Q"),
        color=alt.Color("Payment Method:N", scale=alt.Scale(range=BLINKIT_PALETTE)),
        tooltip=["Payment Method:N", alt.Tooltip("Revenue:Q", format=",.2f")]
    )
    st.altair_chart(chart, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    st.markdown('<div class="section-header">Delivery Status Distribution</div>', unsafe_allow_html=True)
    status_counts = f_orders["DELIVERY_STATUS"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    chart = alt.Chart(status_counts).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
        x=alt.X("Status:N", title="Status", sort="-y"),
        y=alt.Y("Count:Q", title="Count"),
        color=alt.Color("Status:N", scale=alt.Scale(range=[BLINKIT_GREEN, BLINKIT_YELLOW, "#E53935"]), legend=None),
        tooltip=["Status:N", "Count:Q"]
    )
    st.altair_chart(chart, use_container_width=True)

with col4:
    st.markdown('<div class="section-header">Avg Delivery Time (min)</div>', unsafe_allow_html=True)
    if len(f_delivery) > 0 and "DELIVERY_TIME_MINUTES" in f_delivery.columns:
        avg_by_status = f_delivery.groupby("DELIVERY_STATUS")["DELIVERY_TIME_MINUTES"].mean().reset_index()
        avg_by_status.columns = ["Status", "Avg Minutes"]
        chart = alt.Chart(avg_by_status).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
            x=alt.X("Status:N", title="Status", sort="-y"),
            y=alt.Y("Avg Minutes:Q", title="Minutes"),
            color=alt.Color("Status:N", scale=alt.Scale(range=[BLINKIT_GREEN, BLINKIT_YELLOW, "#E53935"]), legend=None),
            tooltip=["Status:N", alt.Tooltip("Avg Minutes:Q", format=".1f")]
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No delivery data available for selected filters.")

st.divider()
st.markdown('<div class="section-header">Marketing Performance</div>', unsafe_allow_html=True)

col5, col6 = st.columns(2)

with col5:
    st.markdown("**Spend vs Revenue by Channel**")
    ch_perf = f_marketing.groupby("CHANNEL").agg(
        Spend=("SPEND", "sum"),
        Revenue=("REVENUE_GENERATED", "sum")
    ).reset_index()
    melted = ch_perf.melt(id_vars="CHANNEL", var_name="Metric", value_name="Amount")
    chart = alt.Chart(melted).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
        x=alt.X("Metric:N", title=""),
        y=alt.Y("Amount:Q", title="Amount"),
        color=alt.Color("Metric:N", scale=alt.Scale(range=[BLINKIT_GREEN, BLINKIT_YELLOW])),
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
        color=alt.Color("Channel:N", scale=alt.Scale(range=BLINKIT_PALETTE)),
        tooltip=["Channel:N", "Conversions:Q"]
    )
    st.altair_chart(chart, use_container_width=True)

st.markdown('<div class="section-header">Top 10 Products by Quantity Sold</div>', unsafe_allow_html=True)
if len(f_items) > 0:
    top_products = f_items.groupby("PRODUCT_ID")["QUANTITY"].sum().reset_index().nlargest(10, "QUANTITY")
    top_products["PRODUCT_ID"] = top_products["PRODUCT_ID"].astype(str)
    top_products.columns = ["Product ID", "Quantity"]
    chart = alt.Chart(top_products).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, color=BLINKIT_GREEN).encode(
        x=alt.X("Quantity:Q", title="Quantity Sold"),
        y=alt.Y("Product ID:N", title="Product", sort="-x"),
        tooltip=["Product ID:N", "Quantity:Q"]
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("No order items data for selected filters.")

st.markdown('<div class="section-header">Delayed Delivery Reasons</div>', unsafe_allow_html=True)
if len(f_delivery) > 0:
    delayed = f_delivery[f_delivery["REASONS_IF_DELAYED"].notna() & (f_delivery["REASONS_IF_DELAYED"] != "")]
    if len(delayed) > 0:
        reasons = delayed["REASONS_IF_DELAYED"].value_counts().reset_index()
        reasons.columns = ["Reason", "Count"]
        chart = alt.Chart(reasons).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, color="#E53935").encode(
            x=alt.X("Count:Q", title="Count"),
            y=alt.Y("Reason:N", title="Reason", sort="-x"),
            tooltip=["Reason:N", "Count:Q"]
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No delayed deliveries in selected filters.")
else:
    st.info("No delivery data available.")
