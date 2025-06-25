import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import os
import shutil
import plotly.express as px
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# =============================================
# CONFIGURATION & SETUP
# =============================================
st.set_page_config(
    page_title="WM Sales Pro+",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main {background-color: #f8f9fa;}
    .sidebar .sidebar-content {background-color: #ffffff; border-right: 1px solid #e0e0e0;}
    .st-bb {background-color: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
    .metric-card {padding: 20px; border-radius: 10px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.05);}
    .nav-button {padding: 10px 15px; border-radius: 5px; font-weight: 500; margin: 5px 0;}
    .nav-button:hover {background-color: #e9ecef;}
    .positive {color: #28a745;}
    .negative {color: #dc3545;}
    .stAlert {border-left: 4px solid #4CAF50;}
</style>
""", unsafe_allow_html=True)

file_path = r"C:\\Users\\User\\Desktop\\Accounts\\2025\\JUNE\\sales_deposit_return\\june_sales_data.xlsx"

# =============================================
# LOAD DATA
# =============================================
@st.cache_data(ttl=3600)
def load_data(path):
    required_cols = {
        "date": pd.to_datetime("today"),
        "Order No": "",
        "customer_name": "",
        "customer_type": "",
        "sales_executive": "",
        "sales_amount": 0.0,
        "sales_return": 0.0,
        "paid_amount": 0.0,
        "customer_cashback_on_paid_amount": 0.0,
        "executive_commission": 0.0,
        "zonal_officer_commission": 0.0,
        "gm_commission": 0.0,
        "company_profit": 0.0,
        "open_value": 0.0
    }
    try:
        if os.path.exists(path):
            df = pd.read_excel(path)
            for col, default in required_cols.items():
                if col not in df.columns:
                    df[col] = default
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df['month'] = df['date'].dt.month_name()
            df['quarter'] = df['date'].dt.quarter
            df['year'] = df['date'].dt.year
            df['day_of_week'] = df['date'].dt.day_name()
            return df.sort_values('date', ascending=False)
        else:
            return pd.DataFrame(columns=required_cols.keys())
    except Exception as e:
        st.error(f"Data loading error: {str(e)}")
        return pd.DataFrame(columns=required_cols.keys())

df = load_data(file_path)

# =============================================
# NAVIGATION
# =============================================
def show_navigation():
    st.sidebar.title("🧽 Navigation")
    nav_options = {
        "📊 Live Dashboard": "dashboard",
        "📝 Transaction Entry": "entry",
        "🧑‍💼 Executive Analytics": "executive",
        "🏢 Customer Insights": "customer",
        "📄 Report Generator": "reports",
        "⚙️ Settings": "settings"
    }
    selected = st.sidebar.radio("Go to", list(nav_options.keys()), label_visibility="collapsed")
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Quick Filters")
    if not df.empty:
        date_min, date_max = df['date'].min().date(), df['date'].max().date()
        date_range = st.sidebar.date_input("Date Range", value=(date_min, date_max), key="nav_date_filter")
        exec_filter = st.sidebar.multiselect("Sales Executives", options=sorted(df['sales_executive'].unique()), key="nav_exec_filter")
        cust_type_filter = st.sidebar.multiselect("Customer Types", options=sorted(df['customer_type'].unique()), key="nav_cust_filter")
        filtered_df = df[(df['date'].dt.date >= date_range[0]) & (df['date'].dt.date <= date_range[1])]
        if exec_filter:
            filtered_df = filtered_df[filtered_df['sales_executive'].isin(exec_filter)]
        if cust_type_filter:
            filtered_df = filtered_df[filtered_df['customer_type'].isin(cust_type_filter)]
    else:
        filtered_df = pd.DataFrame()
    return nav_options[selected], filtered_df

current_page, filtered_data = show_navigation()

# =============================================
# PAGE ROUTING (Transaction Entry Part Updated)
# =============================================
if current_page == "entry":
    st.title("📝 New Transaction Entry")
    with st.form("entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Transaction Date*", value=datetime.today())
            order_no = st.text_input("Order No*", placeholder="ORD-2024-001")
            customer_name = st.text_input("Customer Name*")
            customer_type = st.selectbox("Customer Type*", options=sorted(df['customer_type'].unique()) if not df.empty else [])
        with col2:
            sales_executive = st.selectbox("Sales Executive*", options=sorted(df['sales_executive'].unique()) if not df.empty else [])
            sales_amount = st.number_input("Sales Amount (BDT)*", min_value=0.0)
            paid_amount = st.number_input("Paid Amount (BDT)*", min_value=0.0)
            cashback = st.number_input("Customer Cashback (BDT)", min_value=0.0, max_value=paid_amount, value=min(paid_amount * 0.02, paid_amount))
        if st.form_submit_button("💾 Save Transaction", use_container_width=True):
            if not all([date, order_no, customer_name, sales_executive, sales_amount]):
                st.error("Please fill required fields (*)")
            else:
                new_row = {
                    "date": date,
                    "Order No": order_no,
                    "customer_name": customer_name,
                    "customer_type": customer_type,
                    "sales_executive": sales_executive,
                    "sales_amount": sales_amount,
                    "paid_amount": paid_amount,
                    "customer_cashback_on_paid_amount": cashback,
                    "executive_commission": paid_amount * 0.01,
                    "company_profit": paid_amount * 0.05
                }
                try:
                    if os.path.exists(file_path):
                        backup_path = file_path.replace(".xlsx", f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                        shutil.copy(file_path, backup_path)
                    global df
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    df.to_excel(file_path, index=False)
                    st.success("✅ Transaction saved successfully!")
                    st.balloons()
                except PermissionError as e:
                    st.error("🚫 Permission denied! Please close the Excel file.")
                    st.caption(f"🔍 {e}")
                except Exception as e:
                    st.error(f"❗ Error saving: {str(e)}")
