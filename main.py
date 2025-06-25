import streamlit as st
import pandas as pd
from io import BytesIO
import os
import plotly.express as px


# ✅ Excel ফাইলের পাথ (সঠিকভাবে raw string হিসাবে লিখুন)
file_path = r"C:\Users\User\Desktop\Accounts\2025\JUNE\sales_deposit_return\june_sales_data.xlsx"

#page configuration
st.set_page_config(
    page_title="Sales & Deposit Management System",
    page_icon="📊"
)
# Title and header

st.header("📊 WELBURG METAL PVT LTD")
st.subheader("Sales & Deposit Management System")

           
# Load data
if os.path.exists(file_path):
    df = pd.read_excel(file_path)
else:
    df = pd.DataFrame(columns=[
        "date", "Order No","customer_name", "customer_type", "sales_executive",
        "sales_amount", "sales_return", "paid_amount",
        "customer_cashback_on_paid_amount",
        "executive_commission", "zonal_officer_commission",
        "gm_commission", "company_profit"
    ])

df['date'] = pd.to_datetime(df['date'], errors='coerce')

st.header("➕ Add New Transaction")

# Dropdowns with search
customer_names = sorted(df["customer_name"].dropna().unique())
customer_types = sorted(df["customer_type"].dropna().unique())
sales_executives = sorted(df["sales_executive"].dropna().unique())

date = st.date_input("Date (required)")
order_no = st.text_input("Order No (required)", placeholder="Enter Order Number")
customer_name = st.selectbox("Customer Name (required)", customer_names)
customer_type = st.selectbox("Customer Type (required)", customer_types)
sales_executive = st.selectbox("Sales Executive Name (required)", sales_executives)
sales_amount = st.number_input("Sales Amount (required)", value=0.0)
sales_return = st.number_input("Sales Return (required)", value=0.0)
paid_amount = st.number_input("Paid Amount (required)", value=0.0)

# Cashback eligibility
enable_cashback = st.checkbox("Eligible for 2% Cashback?", value=True)
if enable_cashback:
    default_cashback = round(paid_amount * 0.02, 2)
else:
    default_cashback = 0.0

customer_cashback_on_paid_amount = st.number_input(
    "Customer Cashback on Paid Amount (default 2% of Paid Amount, override if needed)",
    value=default_cashback
)

# Auto-calculate commissions and profit
sales_ex_commission = round(paid_amount * 0.01, 2)
zonal_officer_commission = round(paid_amount * 0.003, 2)
gm_commission = round(paid_amount * 0.002, 2)
company_profit = round(paid_amount * 0.05, 2)

st.markdown(f"**Executive Commission (1%):** {sales_ex_commission} BDT")
st.markdown(f"**Zonal Officer Commission (0.3%):** {zonal_officer_commission} BDT")
st.markdown(f"**GM Commission (0.2%):** {gm_commission} BDT")
st.markdown(f"**Company Profit (5%):** {company_profit} BDT")

if st.button("Add Transaction"):
    new_row = {
        "date": pd.to_datetime(date),
        "Order No": order_no,
        "customer_name": customer_name,
        "customer_type": customer_type,
        "sales_executive": sales_executive,
        "sales_amount": sales_amount,
        "sales_return": sales_return,
        "paid_amount": paid_amount,
        "customer_cashback_on_paid_amount": customer_cashback_on_paid_amount,
        "executive_commission": sales_ex_commission,
        "zonal_officer_commission": zonal_officer_commission,
        "gm_commission": gm_commission,
        "company_profit": company_profit
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_excel(file_path, index=False, engine='openpyxl')
    st.success("Transaction added and saved to Excel!")

st.header("📋 All Transactions")
st.dataframe(df, use_container_width=True)

# ✅ Excel ফাইল থেকে ডেটা লোড করা
@st.cache_data
def load_data(path):
    return pd.read_excel(path)

df = load_data(file_path)

# ✅ Title
st.title("📊 Sales & Deposit Dashboard")

# ✅ কাস্টমার আউটস্ট্যান্ডিং হিসাব করুন
df["customer_outstanding"] = (
    df["open_value"].fillna(0) +
    df["sales_amount"].fillna(0) -
    df["sales_return"].fillna(0)
)

# ✅ Sales Executive অনুযায়ী গ্রুপ করে দেখানো
st.subheader("Sales Executive Wise Summary")
grouped_exec = df.groupby("sales_executive")[
    ["open_value", "sales_amount", "sales_return", "paid_amount", "customer_outstanding"]
].sum().reset_index()

# ✅ শুধুমাত্র number columns format করুন
number_cols = ["open_value", "sales_amount", "sales_return", "paid_amount", "customer_outstanding"]
st.dataframe(
    grouped_exec.style.format({col: "{:,.2f}" for col in number_cols}),
    use_container_width=True
)

# ✅ Sales Executive বেছে নিন
executives = df["sales_executive"].dropna().unique()
selected_exec = st.selectbox("🔍 Select Sales Executive", executives)

# ✅ নির্বাচিত Executive-এর রিপোর্ট দেখানো
filtered_df = df[df["sales_executive"] == selected_exec]

st.subheader(f"📄 Detailed Transactions for: {selected_exec}")
st.dataframe(filtered_df)


# ...existing code...

# ✅ Download বাটন (fixed)
output = BytesIO()
filtered_df.to_excel(output, index=False, engine='openpyxl')
output.seek(0)

st.download_button(
    label="Download This Report as Excel",
    data=output,
    file_name=f"{selected_exec}_transactions.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


# ...existing code...

# ✅ Customer selection
customers = df["customer_name"].dropna().unique()
selected_customer = st.selectbox("🔍 Select Customer", customers)

# ✅ Filter for selected customer
customer_df = df[df["customer_name"] == selected_customer].copy()

# ✅ Calculate outstanding for each transaction (if not already present)
customer_df["outstanding"] = (
    customer_df["open_value"].fillna(0) +
    customer_df["sales_amount"].fillna(0) -
    customer_df["paid_amount"].fillna(0) -
    customer_df["sales_return"].fillna(0) -
    customer_df["customer_cashback_on_paid_amount"].fillna(0)
    if "customer_cashback_on_paid_amount" in customer_df.columns else 0
)

# ✅ Show all transactions for the customer
st.subheader(f"📄 All Transactions for: {selected_customer}")
st.dataframe(customer_df, use_container_width=True)

# ✅ Show total outstanding for the customer
total_outstanding = customer_df["outstanding"].sum()
st.success(f"Total Outstanding for {selected_customer}: {total_outstanding:,.2f} BDT")

# ✅ Download button for customer transactions
output = BytesIO()
customer_df.to_excel(output, index=False, engine='openpyxl')
output.seek(0)

st.download_button(
    label="Download Customer Transactions as Excel",
    data=output,
    file_name=f"{selected_customer}_transactions.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)






# Load data
file_path = r"C:\Users\User\Desktop\Accounts\2025\JUNE\sales_deposit_return\june_sales_data.xlsx"
df = pd.read_excel(file_path)
df['date'] = pd.to_datetime(df['date'])

# Fill missing values for calculation
for col in ["open_value", "sales_amount", "paid_amount", "sales_return", "customer_cashback_on_paid_amount"]:
    if col in df.columns:
        df[col] = df[col].fillna(0)

# Calculate outstanding for each transaction
df["outstanding"] = (
    df["open_value"] +
    df["sales_amount"] -
    df["paid_amount"] -
    df["sales_return"] -
    df["customer_cashback_on_paid_amount"]
)

st.title("📊 Sales & Deposit Dashboard")

# --- Executive-wise Section ---
st.header("Executive-wise Transactions")
executives = df["sales_executive"].dropna().unique()
selected_exec = st.selectbox("Select Sales Executive", executives, key="exec")

# Date range for executive
min_date, max_date = df["date"].min(), df["date"].max()
exec_date_range = st.date_input("Select Date Range (Executive)", [min_date, max_date], key="exec_date")

exec_filtered = df[
    (df["sales_executive"] == selected_exec) &
    (df["date"] >= pd.to_datetime(exec_date_range[0])) &
    (df["date"] <= pd.to_datetime(exec_date_range[1]))
]

st.subheader(f"All Transactions for: {selected_exec}")
st.dataframe(exec_filtered, use_container_width=True)
st.success(f"Total Outstanding: {exec_filtered['outstanding'].sum():,.2f} BDT")

# Download button for executive
output_exec = BytesIO()
exec_filtered.to_excel(output_exec, index=False, engine='openpyxl')
output_exec.seek(0)
st.download_button(
    label="Download Executive Transactions as Excel",
    data=output_exec,
    file_name=f"{selected_exec}_transactions.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="exec_download"
)

# --- Customer-wise Section ---
st.header("Customer-wise Transactions")
customers = df["customer_name"].dropna().unique()
selected_customer = st.selectbox("Select Customer", customers, key="cust")

# Date range for customer
cust_date_range = st.date_input("Select Date Range (Customer)", [min_date, max_date], key="cust_date")

cust_filtered = df[
    (df["customer_name"] == selected_customer) &
    (df["date"] >= pd.to_datetime(cust_date_range[0])) &
    (df["date"] <= pd.to_datetime(cust_date_range[1]))
]

st.subheader(f"All Transactions for: {selected_customer}")
st.dataframe(cust_filtered, use_container_width=True)
st.success(f"Total Outstanding: {cust_filtered['outstanding'].sum():,.2f} BDT")

# Download button for customer
output_cust = BytesIO()
cust_filtered.to_excel(output_cust, index=False, engine='openpyxl')
output_cust.seek(0)
st.download_button(
    label="Download Customer Transactions as Excel",
    data=output_cust,
    file_name=f"{selected_customer}_transactions.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="cust_download"
)




# Executive-wise, customer-wise total outstanding

st.header("🔎 Executive-wise Customer Outstanding")

# Select executive
exec_names = sorted(df["sales_executive"].dropna().unique())
selected_exec = st.selectbox("Select Sales Executive for Outstanding", exec_names, key="outstanding_exec")

# Filter for selected executive
exec_df = df[df["sales_executive"] == selected_exec].copy()

# Calculate outstanding for each row if not already present
if "outstanding" not in exec_df.columns:
    exec_df["outstanding"] = (
        exec_df["sales_amount"].fillna(0)
        - exec_df["paid_amount"].fillna(0)
        - exec_df["sales_return"].fillna(0)
        - exec_df["customer_cashback_on_paid_amount"].fillna(0)
    )

# Group by customer and sum outstanding
customer_outstanding = exec_df.groupby("customer_name")["outstanding"].sum().reset_index()

st.subheader(f"Customer-wise Total Outstanding for {selected_exec}")
st.dataframe(customer_outstanding, use_container_width=True)

# Show total outstanding amount for the executive
total_outstanding = customer_outstanding["outstanding"].sum()
st.success(f"Total Outstanding Amount for {selected_exec}: {total_outstanding:,.2f} BDT")

#######

# ...your existing code...

# Download button for outstanding table
output = BytesIO()
customer_outstanding.to_excel(output, index=False, engine='openpyxl')
output.seek(0)
st.download_button(
    label="Download Outstanding as Excel",
    data=output,
    file_name=f"{selected_exec}_customer_outstanding.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="outstanding_download"
)

# Bar chart for customer-wise outstanding
fig = px.bar(
    customer_outstanding,
    x="customer_name",
    y="outstanding",
    title=f"Customer-wise Outstanding for {selected_exec}",
    labels={"outstanding": "Outstanding (BDT)", "customer_name": "Customer"}
)
fig.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True, key="outstanding_chart")


##################


# Assuming df is already loaded and processed as before

st.header("📈 Sales Trends & Performance Analytics")

# --- Sales Trends Over Time ---
st.subheader("Sales Trends Over Time")
df['date'] = pd.to_datetime(df['date'], errors='coerce')
sales_trend = df.groupby('date')['sales_amount'].sum().reset_index()
fig_trend = px.line(sales_trend, x='date', y='sales_amount', title="Total Sales Amount Over Time")
st.plotly_chart(fig_trend, use_container_width=True)

# --- Sales Person (Executive) Performance ---
st.subheader("Sales Executive Performance (Bar Chart)")
exec_perf = df.groupby('sales_executive')[['sales_amount', 'paid_amount']].sum().reset_index()
fig_exec = px.bar(
    exec_perf,
    x='sales_executive',
    y=['sales_amount', 'paid_amount'],
    barmode='group',
    title="Sales & Deposit by Executive",
    labels={'value': 'Amount (BDT)', 'sales_executive': 'Executive'}
)
fig_exec.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_exec, use_container_width=True)

# --- Customer Performance ---
st.subheader("Customer Performance (Bar Chart)")
cust_perf = df.groupby('customer_name')[['sales_amount', 'paid_amount']].sum().reset_index()
fig_cust = px.bar(
    cust_perf,
    x='customer_name',
    y=['sales_amount', 'paid_amount'],
    barmode='group',
    title="Sales & Deposit by Customer",
    labels={'value': 'Amount (BDT)', 'customer_name': 'Customer'}
)
fig_cust.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_cust, use_container_width=True)

# --- Top 5 Executives and Customers ---
st.subheader("🏆 Top 10 Executives by Sales")
top_exec = exec_perf.sort_values('sales_amount', ascending=False).head(10)
st.dataframe(top_exec, use_container_width=True)

st.subheader("🏆 Top 10 Customers by Sales")
top_cust = cust_perf.sort_values('sales_amount', ascending=False).head(10)
st.dataframe(top_cust, use_container_width=True)

st.markdown("---")
# --- Custom Date Range Analytics ---
# --- Custom Date Range & Executive-wise Analytics ---

st.header("📅 Executive-wise Sales, Deposit, Return & Customer Commission (Custom Date Range)")

# Ensure date column is datetime
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# Executive selection
exec_names = sorted(df["sales_executive"].dropna().unique())
selected_exec = st.selectbox("Select Sales Executive", exec_names, key="custom_exec")

# Date range selection
min_date, max_date = df['date'].min(), df['date'].max()
date_range = st.date_input("Select Date Range", [min_date, max_date], key="custom_exec_date")

# Filter data
filtered = df[
    (df["sales_executive"] == selected_exec) &
    (df["date"] >= pd.to_datetime(date_range[0])) &
    (df["date"] <= pd.to_datetime(date_range[1]))
].copy()

# Calculate customer commission (2% on paid_amount)
filtered["customer_commission"] = filtered["paid_amount"].fillna(0) * 0.02

# Show summary table
summary = filtered.groupby("customer_name").agg({
    "sales_amount": "sum",
    "paid_amount": "sum",
    "sales_return": "sum",
    "customer_commission": "sum"
}).reset_index()

st.subheader(f"Summary for {selected_exec} ({date_range[0]} to {date_range[1]})")
st.dataframe(summary, use_container_width=True)

# Show totals
totals = summary[["sales_amount", "paid_amount", "sales_return", "customer_commission"]].sum()
st.success(
    f"**Total Sales:** {totals['sales_amount']:,.2f} | "
    f"**Total Deposit:** {totals['paid_amount']:,.2f} | "
    f"**Total Return:** {totals['sales_return']:,.2f} | "
    f"**Total Customer Commission:** {totals['customer_commission']:,.2f}"
)

st.markdown("---")

# Pie chart for sales by executive
st.subheader("Sales Distribution by Executive")
fig_pie_exec = px.pie(df, names='sales_executive', values='sales_amount', title="Sales by Executive")
st.plotly_chart(fig_pie_exec, use_container_width=True, key="pie_exec")

# Pie chart for sales by customer
st.subheader("Sales Distribution by Customer")
fig_pie_cust = px.pie(df, names='customer_name', values='sales_amount', title="Sales by Customer")
st.plotly_chart(fig_pie_cust, use_container_width=True, key="pie_cust")


st.markdown("---")
# Place this near the top after loading df
total_sales = df['sales_amount'].sum()
total_deposit = df['paid_amount'].sum()
total_outstanding = df['outstanding'].sum() if 'outstanding' in df.columns else 0
num_customers = df['customer_name'].nunique()
num_executives = df['sales_executive'].nunique()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Sales", f"{total_sales:,.2f} BDT")
col2.metric("Total Deposit", f"{total_deposit:,.2f} BDT")
col3.metric("Total Outstanding", f"{total_outstanding:,.2f} BDT")
col4.metric("Customers", num_customers)
col5.metric("Executives", num_executives)

st.markdown("---")
# Add after outstanding analytics
threshold = st.number_input("Outstanding Alert Threshold", value=50000.0)
if 'outstanding' in df.columns:
    high_outstanding = df.groupby("customer_name")["outstanding"].sum().reset_index()
    alert_customers = high_outstanding[high_outstanding["outstanding"] > threshold]
    if not alert_customers.empty:
        st.warning("⚠️ Customers with high outstanding:")
        st.dataframe(alert_customers, use_container_width=True)
st.markdown("---")


import streamlit as st
import pandas as pd

# --- Date Range & Employee Commission/Profit Analytics ---

st.header("💼 Commission & Profit Analytics (By Date Range & Employee)")

# Ensure date column is datetime
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# 1. Select date range first
min_date, max_date = df['date'].min(), df['date'].max()
selected_range = st.date_input("Select Date Range", [min_date, max_date], key="commission_date")

# 2. Filter by date range
date_filtered = df[
    (df['date'] >= pd.to_datetime(selected_range[0])) &
    (df['date'] <= pd.to_datetime(selected_range[1]))
]

# 3. Select employee name (sales executive)
employee_names = sorted(date_filtered["sales_executive"].dropna().unique())
selected_employee = st.selectbox("Select Employee Name", employee_names, key="commission_employee")

# 4. Filter by employee
emp_filtered = date_filtered[date_filtered["sales_executive"] == selected_employee]

# 5. Show commission and profit summary
commission_summary = emp_filtered.agg({
    "sales_ex_commission": "sum",
    "zonal_officer_commission": "sum",
    "gm_commission": "sum",
    "company_profit": "sum"
}).rename({
    "sales_ex_commission": "Executive Commission",
    "zonal_officer_commission": "Zonal Officer Commission",
    "gm_commission": "GM Commission",
    "company_profit": "Company Profit"
})

st.subheader(f"Commission & Profit for {selected_employee} ({selected_range[0]} to {selected_range[1]})")
st.write(commission_summary)

# Optional: Show detailed transactions
with st.expander("Show Detailed Transactions"):
    st.dataframe(emp_filtered, use_container_width=True)

st.markdown("---")


# --- Date Range Wise Totals (All Employees or Selected Employee) ---
st.header("📅 Date Range Wise Totals (Sales, Deposit, Return, etc.)")

# Ensure date column is datetime
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# 1. Select date range
min_date, max_date = df['date'].min(), df['date'].max()
date_range = st.date_input("Select Date Range for Totals", [min_date, max_date], key="date_range_totals")

# 2. Optional: Select employee (or show all)
employee_options = ["All"] + sorted(df["sales_executive"].dropna().unique())
selected_emp = st.selectbox("Select Employee (optional)", employee_options, key="totals_employee")

# 3. Filter by date range (and employee if selected)
filtered = df[
    (df['date'] >= pd.to_datetime(date_range[0])) &
    (df['date'] <= pd.to_datetime(date_range[1]))
].copy()

if selected_emp != "All":
    filtered = filtered[filtered["sales_executive"] == selected_emp]

# 4. Calculate totals
totals = {
    "Total Sales": filtered["sales_amount"].sum(),
    "Total Deposit": filtered["paid_amount"].sum(),
    "Total Return": filtered["sales_return"].sum(),
    "Total Customer Cashback": filtered["customer_cashback_on_paid_amount"].sum() if "customer_cashback_on_paid_amount" in filtered.columns else 0,
    "Total Executive Commission": filtered["sales_ex_commission"].sum() if "sales_ex_commission" in filtered.columns else filtered["executive_commission"].sum() if "executive_commission" in filtered.columns else 0,
    "Total Zonal Officer Commission": filtered["zonal_officer_commission"].sum() if "zonal_officer_commission" in filtered.columns else 0,
    "Total GM Commission": filtered["gm_commission"].sum() if "gm_commission" in filtered.columns else 0,
    "Total Company Profit": filtered["company_profit"].sum() if "company_profit" in filtered.columns else 0,
}

# 5. Show totals
st.subheader(
    f"Totals from {date_range[0]} to {date_range[1]}"
    + (f" for {selected_emp}" if selected_emp != "All" else " (All Employees)")
)
for k, v in totals.items():
    st.write(f"**{k}:** {v:,.2f}")

# Optional: Show filtered transactions
with st.expander("Show Transactions in Date Range"):
    st.dataframe(filtered, use_container_width=True)

st.markdown("---")

st.header("📊 Sales Executive-wise Sales & Deposit (Bar Chart)")

# Group by sales executive and sum sales and deposit
exec_summary = df.groupby("sales_executive")[["sales_amount", "paid_amount"]].sum().reset_index()

# Create bar chart
fig = px.bar(
    exec_summary,
    x="sales_executive",
    y=["sales_amount", "paid_amount"],
    barmode="group",
    labels={"value": "Amount (BDT)", "sales_executive": "Sales Executive"},
    title="Sales & Deposit by Sales Executive"
)
fig.update_layout(xaxis_tickangle=-45)

st.plotly_chart(fig, use_container_width=True)
st.markdown("---")

st.header("🏢 Chairman's Custom Date Range Company Report")

# 1. Select custom date range
min_date, max_date = df['date'].min(), df['date'].max()
chairman_range = st.date_input(
    "Select Date Range for Chairman's Report",
    [min_date, max_date],
    key="chairman_date"
)

# 2. Filter data for selected range
chairman_df = df[
    (df['date'] >= pd.to_datetime(chairman_range[0])) &
    (df['date'] <= pd.to_datetime(chairman_range[1]))
].copy()

# 3. Calculate totals
chairman_totals = {
    "Total Sales": chairman_df["sales_amount"].sum(),
    "Total Deposit": chairman_df["paid_amount"].sum(),
    "Total Return": chairman_df["sales_return"].sum(),
    "Total Outstanding": chairman_df["outstanding"].sum() if "outstanding" in chairman_df.columns else 0,
    "Total Company Profit": chairman_df["company_profit"].sum() if "company_profit" in chairman_df.columns else 0,
}

# 4. Show summary
st.subheader(
    f"Company Totals ({chairman_range[0]} to {chairman_range[1]})"
)
for k, v in chairman_totals.items():
    st.write(f"**{k}:** {v:,.2f}")

# 5. Optional: Show all transactions in range
with st.expander("Show All Transactions in Date Range"):
    st.dataframe(chairman_df, use_container_width=True)

# 6. Optional: Download button
from io import BytesIO
output_chairman = BytesIO()
chairman_df.to_excel(output_chairman, index=False, engine='openpyxl')
output_chairman.seek(0)
st.download_button(
    label="Download Chairman's Report as Excel",
    data=output_chairman,
    file_name=f"chairman_report_{chairman_range[0]}_{chairman_range[1]}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="chairman_download"
)

st.markdown("---")



st.markdown(
    """
    <div style='text-align: center; font-size: 15px;'>
        <b>Developed & Maintained by:</b> Mujakkir Ahmad<br>
        Accountant | Data Analyst<br>
        WELBURG METAL PVT LTD<br>
        Sadapur, Nagorkonda, Savar, Dhaka, Bangladesh<br>
        <b>Contact:</b> 01787933422<br>
        <b>Email:</b> mujakkirar4@gmail.com<br>
        <br>
        &copy; 2025 WELBURG METAL PVT LTD. All rights reserved.
    </div>
    """,
    unsafe_allow_html=True
)