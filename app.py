import sqlite3
import altair as alt
import pandas as pd
import streamlit as st

DB_FILE = "finance.db"

# ------------------- DATA LOADING ------------------- #

def load_data():
    conn = sqlite3.connect(DB_FILE)
    query = """
        SELECT 
            t.transaction_id,
            t.date,
            t.description,
            t.amount,
            t.type,
            a.account_name,
            c.category_name
        FROM Transactions t
        JOIN Accounts a ON t.account_id = a.account_id
        JOIN Categories c ON t.category_id = c.category_id
        ORDER BY t.date;
    """
    df = pd.read_sql(query, conn, parse_dates=["date"])
    conn.close()
    return df


# ------------------- PAGE CONFIG ------------------- #

st.set_page_config(
    page_title="Monthly Budget Tracker",
    page_icon="💗",
    layout="wide",
)

df = load_data()
# Normalize transaction type casing
df["type"] = df["type"].str.lower()


# ------------------- MONTH HANDLING ------------------- #

df["year_month"] = df["date"].dt.to_period("M").astype(str)

available_months = sorted(df["year_month"].unique())

selected_months = st.sidebar.multiselect(
    "📅 Select Month(s)",
    available_months,
    default=available_months
)

# ------------------- GLOBAL CSS ------------------- #

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Quicksand', sans-serif; }
    body { background: linear-gradient(135deg, #ffe6f5, #ffffff, #ffe4f0); }
    [data-testid="stSidebar"] { background: #ffd6ec; }
    .pink-divider { border: 2px solid #ff69b4; margin: 20px 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------- HEADER ------------------- #

st.markdown('<div class="banner-frame">', unsafe_allow_html=True)
st.image("budgetimage.jpg", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    "<div style='text-align:center;font-size:22px;color:#ff69b4;font-weight:600;'>🌸 Monthly Finance Tracker & Planner 🌸</div>",
    unsafe_allow_html=True,
)

st.markdown("<hr class='pink-divider'>", unsafe_allow_html=True)

# ------------------- FILTERING PIPELINE ------------------- #

filtered = df.copy()

# 1️⃣ Month filter
if selected_months:
    filtered = filtered[filtered["year_month"].isin(selected_months)]

# Sidebar filters
st.sidebar.header("Filters")

min_date = df["date"].min().date()
max_date = df["date"].max().date()

start_date, end_date = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# 2️⃣ Date filter
filtered = filtered[
    (filtered["date"].dt.date >= start_date)
    & (filtered["date"].dt.date <= end_date)
]

# 3️⃣ Category filter
categories = sorted(filtered["category_name"].unique())
selected_categories = st.sidebar.multiselect(
    "Categories",
    categories,
    default=categories,
)
if selected_categories:
    filtered = filtered[filtered["category_name"].isin(selected_categories)]

# 4️⃣ Account filter
accounts = sorted(filtered["account_name"].unique())
selected_accounts = st.sidebar.multiselect(
    "Accounts",
    accounts,
    default=accounts,
)
if selected_accounts:
    filtered = filtered[filtered["account_name"].isin(selected_accounts)]

# ------------------- SUMMARY METRICS ------------------- #

income = filtered[filtered["type"] == "income"]["amount"].sum()
expenses = filtered[filtered["type"] == "expense"]["amount"].sum()
net = income - expenses

saved = filtered[
    filtered["category_name"].str.contains("Savings", case=False, na=False)
]["amount"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("💖 Total Income", f"${income:,.2f}")
col2.metric("💸 Total Expenses", f"${expenses:,.2f}")
col3.metric("💗 Net Balance", f"${net:,.2f}")

st.markdown("<hr class='pink-divider'>", unsafe_allow_html=True)

# ------------------- BAR CHART ------------------- #

st.subheader("🌸 Spending by Category")

expense_df = filtered[filtered["type"] == "expense"]

if not expense_df.empty:
    category_totals = expense_df.groupby("category_name", as_index=False)["amount"].sum()
    bar_chart = (
        alt.Chart(category_totals)
        .mark_bar(color="#ff69b4", cornerRadius=8)
        .encode(
            x="amount:Q",
            y=alt.Y("category_name:N", sort="-x"),
            tooltip=["category_name", "amount"]
        )
    )
    st.altair_chart(bar_chart, use_container_width=True)
else:
    st.info("No expense data for the selected filters.")

st.markdown("<hr class='pink-divider'>", unsafe_allow_html=True)

# ------------------- PIE CHART ------------------- #

st.subheader("🎀 Category Share")

if not expense_df.empty:
    pie = (
        alt.Chart(category_totals)
        .mark_arc()
        .encode(
            theta="amount:Q",
            color="category_name:N",
            tooltip=["category_name", "amount"]
        )
    )
    st.altair_chart(pie, use_container_width=True)
else:
    st.info("No expense data to show.")

st.markdown("<hr class='pink-divider'>", unsafe_allow_html=True)

# ------------------- TOP 5 EXPENSES ------------------- #

st.subheader("🌸 Top 5 Biggest Expenses")

if not expense_df.empty:
    top5 = expense_df.sort_values("amount", ascending=False).head(5)
    for _, row in top5.iterrows():
        st.markdown(
            f"""
            <div style="background:#ffe6f2;padding:15px;border-radius:16px;
            border-left:6px solid hotpink;margin-bottom:10px;">
            <strong>{row['category_name']}</strong><br>
            {row['date'].date()}<br>
            {row['description']}<br>
            <strong>${row['amount']:,.2f}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("No expense records to display.")

st.markdown("<hr class='pink-divider'>", unsafe_allow_html=True)

# ------------------- TABLE + DOWNLOAD ------------------- #

st.subheader("🌸 Filtered Transactions")
st.dataframe(filtered, use_container_width=True)

csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "📥 Download Filtered Data",
    csv,
    "filtered_transactions.csv",
    "text/csv"
)

# ------------------- FOOTER ------------------- #

st.markdown(
    "<div style='text-align:center;color:#ff69b4;font-size:14px;'>Built with 💗 for INFO 531 Final Project (2025)</div>",
    unsafe_allow_html=True,
)
