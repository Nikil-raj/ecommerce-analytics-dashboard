import streamlit as st
from utils.data_loader import run_query
import plotly.express as px
import pandas as pd
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

st.set_page_config(page_title="E-commerce Dashboard", layout="wide")

st.markdown("# 📊 E-commerce Analytics Dashboard")
st.caption("Real-time insights powered by Snowflake")
st.markdown("<br>", unsafe_allow_html=True)


st.sidebar.title("📊 Analytics Dashboard")
st.sidebar.markdown("E-commerce Insights")
st.sidebar.markdown("---")

st.sidebar.markdown("---")
st.sidebar.subheader("🤖 Ask Your Data")

user_question = st.sidebar.text_input("Ask a question")


st.markdown("""
<style>
.main {
    background-color: #f5f7fb;
}
</style>
""", unsafe_allow_html=True)


    

st.markdown("### 📊 Overview")
st.markdown("---")

# =========================
# KPI SECTION
# =========================

revenue_query = """
SELECT SUM(price) AS total_revenue
FROM order_items;
"""

customer_query = """
SELECT COUNT(DISTINCT customer_unique_id) AS total_customers
FROM customers;
"""

revenue_df = run_query(revenue_query)
customer_df = run_query(customer_query)

total_revenue = revenue_df.iloc[0, 0]
total_customers = customer_df.iloc[0, 0]

col1, col2,col3 = st.columns(3)

col1.metric("💰 Total Revenue", f"₹{total_revenue:,.0f}")
col2.metric("👤 Total Customers", f"{total_customers:,}")

aov_query = """
SELECT SUM(price) / COUNT(DISTINCT order_id) AS avg_order_value
FROM order_items;
"""

aov_df = run_query(aov_query)
avg_order_value = aov_df.iloc[0, 0]

col3.metric("🛒 Avg Order Value", f"₹{avg_order_value:,.0f}")



# =========================
# FILTER SECTION
# =========================

state_query = """
SELECT DISTINCT customer_state
FROM customers
ORDER BY customer_state;
"""

states_df = run_query(state_query)
states = ["All"] + states_df["CUSTOMER_STATE"].tolist()

selected_state = st.sidebar.selectbox("🌍 Select State", states)

# =========================
# MONTHLY REVENUE (WITH FILTER)
# =========================

if selected_state == "All":
    revenue_trend_query = """
    SELECT DATE_TRUNC('month', o.order_purchase_timestamp) AS month,
           SUM(oi.price) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY month
    ORDER BY month;
    """
else:
    revenue_trend_query = f"""
    SELECT DATE_TRUNC('month', o.order_purchase_timestamp) AS month,
           SUM(oi.price) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE c.customer_state = '{selected_state}'
    GROUP BY month
    ORDER BY month;
    """

revenue_df = run_query(revenue_trend_query)
revenue_df.columns = revenue_df.columns.str.upper()

st.line_chart(revenue_df.set_index("MONTH"))

# =========================
# TOP PRODUCTS
# =========================

top_products_query = """
SELECT product_id, SUM(price) AS revenue
FROM order_items
GROUP BY product_id
ORDER BY revenue DESC
LIMIT 10;
"""

top_products_df = run_query(top_products_query)

st.subheader("🏆 Top 10 Products by Revenue")

fig = px.bar(
    top_products_df,
    x="PRODUCT_ID",
    y="REVENUE",
    title="Top Products"
)

st.plotly_chart(fig, width="stretch")


st.markdown("---")
st.header("👤 Customer Insights")

retention_query = """
SELECT COUNT(*) * 100.0 / 
       (SELECT COUNT(DISTINCT customer_unique_id) FROM customers) AS retention_rate
FROM (
  SELECT c.customer_unique_id
  FROM customers c 
  JOIN orders o ON c.customer_id = o.customer_id  
  GROUP BY c.customer_unique_id 
  HAVING COUNT(DISTINCT DATE_TRUNC('month', o.order_purchase_timestamp)) > 1
) t;
"""
churn_query = """
SELECT COUNT(*) * 100.0 / 
       (SELECT COUNT(DISTINCT customer_unique_id) FROM customers) AS churn_rate
FROM (
  SELECT c.customer_unique_id
  FROM customers c 
  JOIN orders o ON c.customer_id = o.customer_id 
  GROUP BY c.customer_unique_id 
  HAVING DATEDIFF('day', MAX(o.order_purchase_timestamp), CURRENT_DATE) > 90
) t;
"""
retention_df = run_query(retention_query)
churn_df = run_query(churn_query)

retention_rate = retention_df.iloc[0, 0]
churn_rate = churn_df.iloc[0, 0]

col1, col2,col3 = st.columns(3)

col1.metric("🔁 Retention Rate", f"{retention_rate:.2f}%")
col2.metric("⚠️ Churn Rate", f"{churn_rate:.2f}%")


st.title("📈 Cohort Analysis")

query = """
WITH cohort AS (
  SELECT 
    c.customer_unique_id,
    DATE_TRUNC('month', MIN(o.order_purchase_timestamp)) AS cohort_month  
  FROM customers c 
  JOIN orders o ON c.customer_id = o.customer_id 
  GROUP BY c.customer_unique_id
)

SELECT 
  co.cohort_month,
  DATEDIFF('month', co.cohort_month, DATE_TRUNC('month', o.order_purchase_timestamp)) AS month_number,
  COUNT(DISTINCT co.customer_unique_id) AS customers
FROM cohort co 
JOIN customers c ON co.customer_unique_id = c.customer_unique_id
JOIN orders o ON c.customer_id = o.customer_id 
GROUP BY co.cohort_month, month_number
ORDER BY co.cohort_month, month_number;
"""

cohort_df = run_query(query)
cohort_df.columns = cohort_df.columns.str.upper()

pivot_df = cohort_df.pivot(
    index="COHORT_MONTH",
    columns="MONTH_NUMBER",
    values="CUSTOMERS"
)
pivot_pct = pivot_df.div(pivot_df[0], axis=0) * 100

fig = px.imshow(
    pivot_pct,
    text_auto=".1f",
    aspect="auto",
    title="Cohort Retention (%)"
)

fig.update_layout(
    xaxis_title="Months Since First Purchase",
    yaxis_title="Cohort Month"
)



st.plotly_chart(fig, width="stretch")


orders_query = """
SELECT DATE_TRUNC('month', order_purchase_timestamp) AS month,
       COUNT(order_id) AS total_orders
FROM orders
GROUP BY month
ORDER BY month;
"""

orders_df = run_query(orders_query)
st.subheader("📦 Order Volume Trend")
orders_df.columns = orders_df.columns.str.upper()
st.line_chart(orders_df.set_index("MONTH"))

repeat_query = """
SELECT
  CASE 
    WHEN order_count = 1 THEN 'New'
    ELSE 'Repeat'
  END AS customer_type,
  COUNT(*) AS customers
FROM (
  SELECT c.customer_unique_id, COUNT(o.order_id) AS order_count
  FROM orders o
  JOIN customers c ON o.customer_id = c.customer_id
  GROUP BY c.customer_unique_id
) t
GROUP BY customer_type;
"""

repeat_df = run_query(repeat_query)

fig = px.pie(
    repeat_df,
    names="CUSTOMER_TYPE",
    values="CUSTOMERS",
    title="New vs Repeat Customers"
)

st.plotly_chart(fig, width="stretch", key="repeat_customers")

def generate_sql(question):
    prompt = f"""
    You are a data analyst working with an e-commerce database.

    Tables:
    - customers(customer_id, customer_unique_id, customer_state)
    - orders(order_id, customer_id, order_purchase_timestamp)
    - order_items(order_id, product_id, price)

    Convert this question into SQL:

    Question: {question}

    Only return SQL query.
    """

    response = model.generate_content(prompt)

    return response.text.replace("```sql", "").replace("```", "").strip()

if user_question:
    try:
        sql_query = generate_sql(user_question)

        st.subheader("🧠 Generated SQL")
        st.code(sql_query, language="sql")

        result = run_query(sql_query)

        st.subheader("📊 Result")
        st.dataframe(result)

    except Exception as e:
        st.error(f"Error: {e}")
st.markdown("---")
st.caption("Built by Nikil | Data Analytics Project")
