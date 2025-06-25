import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import io

# Page configuration
st.set_page_config(
    page_title="Sales Performance & Profitability Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data function with caching
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path)  # or pd.read_csv()
    
    # Data preprocessing
    df['date'] = pd.to_datetime(df['date'])
    df['net_sales'] = df['sales_amount'] - df['sales_return']
    df['gross_profit'] = df['sales_amount'] - df['total_commission']
    df['due_amount'] = df['net_sales'] - df['paid_amount']
    
    # Extract month and year for time-based analysis
    df['month_year'] = df['date'].dt.to_period('M').astype(str)
    df['year'] = df['date'].dt.year
    
    return df

# Main app function
def main():
    # Sidebar - Filters
    st.sidebar.header("Filters")
    
    # Load data
    uploaded_file = st.sidebar.file_uploader("Upload your sales data (Excel or CSV)", type=['xlsx', 'csv'])
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        
        # Date range filter
        min_date = df['date'].min()
        max_date = df['date'].max()
        date_range = st.sidebar.date_input(
            "Select Date Range",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
        
        # Convert to datetime
        if len(date_range) == 2:
            start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        # Other filters
        customer_types = st.sidebar.multiselect(
            "Customer Types",
            options=df['customer_type'].unique(),
            default=df['customer_type'].unique()
        )
        
        area_zones = st.sidebar.multiselect(
            "Area Zones",
            options=df['area_zone'].unique(),
            default=df['area_zone'].unique()
        )
        
        sales_executives = st.sidebar.multiselect(
            "Sales Executives",
            options=df['sales_by'].unique(),
            default=df['sales_by'].unique()
        )
        
        # Apply filters
        df = df[
            (df['customer_type'].isin(customer_types)) &
            (df['area_zone'].isin(area_zones)) &
            (df['sales_by'].isin(sales_executives))
        ]
        
        # Main dashboard
        st.title("📊 Sales Performance & Profitability Dashboard")
        
        # KPI Cards
        st.subheader("Key Performance Indicators")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sales", f"${df['sales_amount'].sum():,.2f}")
        with col2:
            st.metric("Net Sales", f"${df['net_sales'].sum():,.2f}")
        with col3:
            st.metric("Total Profit", f"${df['company_profit'].sum():,.2f}")
        with col4:
            st.metric("Avg. Profit Margin", f"{df['company_profit'].sum() / df['net_sales'].sum() * 100:.2f}%")
        
        # Tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Sales Overview", 
            "Profitability Analysis", 
            "Executive Performance", 
            "Customer Insights",
            "Raw Data"
        ])
        
        with tab1:
            # Sales Trend
            st.subheader("Sales Trend Over Time")
            sales_trend = df.groupby('month_year').agg({
                'sales_amount': 'sum',
                'sales_return': 'sum',
                'net_sales': 'sum'
            }).reset_index()
            
            fig = px.line(
                sales_trend, 
                x='month_year', 
                y=['sales_amount', 'net_sales'],
                title="Monthly Sales Performance",
                labels={'value': 'Amount', 'variable': 'Metric'},
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Customer Type Distribution
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Sales by Customer Type")
                cust_type_sales = df.groupby('customer_type')['net_sales'].sum().reset_index()
                fig = px.pie(
                    cust_type_sales,
                    names='customer_type',
                    values='net_sales',
                    hole=0.3
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Sales by Area Zone")
                zone_sales = df.groupby('area_zone')['net_sales'].sum().nlargest(10).reset_index()
                fig = px.bar(
                    zone_sales,
                    x='net_sales',
                    y='area_zone',
                    orientation='h',
                    title="Top 10 Zones by Sales"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # Profitability Analysis
            st.subheader("Profitability Metrics")
            
            # High-profit vs low-profit customers
            st.subheader("Customer Profitability Analysis")
            customer_profit = df.groupby('customer_name').agg({
                'net_sales': 'sum',
                'company_profit': 'sum'
            }).reset_index()
            customer_profit['profit_margin'] = customer_profit['company_profit'] / customer_profit['net_sales'] * 100
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("Top 10 Customers by Profit")
                top_customers = customer_profit.nlargest(10, 'company_profit')
                st.dataframe(top_customers.sort_values('company_profit', ascending=False))
            
            with col2:
                st.write("Customers with Highest Profit Margins")
                margin_customers = customer_profit.nlargest(10, 'profit_margin')
                st.dataframe(margin_customers.sort_values('profit_margin', ascending=False))
            
            # Commission analysis
            st.subheader("Commission Breakdown")
            commission_data = df.groupby('customer_type').agg({
                'sales_person_commission': 'sum',
                'marketing_commission': 'sum',
                'customer_commission': 'sum'
            }).reset_index()
            
            fig = px.bar(
                commission_data,
                x='customer_type',
                y=['sales_person_commission', 'marketing_commission', 'customer_commission'],
                title="Commission Distribution by Customer Type",
                barmode='stack'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            # Executive Performance
            st.subheader("Sales Executive Performance")
            
            exec_performance = df.groupby('sales_by').agg({
                'net_sales': 'sum',
                'sales_person_commission': 'sum',
                'order_no': 'nunique',
                'customer_name': 'nunique'
            }).reset_index()
            exec_performance.columns = [
                'Sales Executive', 
                'Total Sales', 
                'Total Commission', 
                'Number of Orders', 
                'Unique Customers'
            ]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("Sales Performance")
                fig = px.bar(
                    exec_performance.nlargest(10, 'Total Sales'),
                    x='Total Sales',
                    y='Sales Executive',
                    orientation='h'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.write("Commission Earned")
                fig = px.bar(
                    exec_performance.nlargest(10, 'Total Commission'),
                    x='Total Commission',
                    y='Sales Executive',
                    orientation='h',
                    color='Total Sales'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.write("Detailed Executive Metrics")
            st.dataframe(exec_performance.sort_values('Total Sales', ascending=False))
        
        with tab4:
            # Customer Insights
            st.subheader("Customer Summary")
            
            customer_summary = df.groupby(['customer_name', 'phone_number', 'customer_type', 'area_zone']).agg({
                'customer_opening': 'first',
                'net_sales': 'sum',
                'paid_amount': 'sum',
                'due_amount': 'sum',
                'customer_cashback_on_paid_amount': 'sum',
                'customer_commission': 'sum'
            }).reset_index()
            
            # Search functionality
            search_term = st.text_input("Search by Customer Name or Phone Number")
            if search_term:
                customer_summary = customer_summary[
                    (customer_summary['customer_name'].str.contains(search_term, case=False)) |
                    (customer_summary['phone_number'].astype(str).str.contains(search_term))
                ]
            
            st.dataframe(customer_summary)
            
            # Due analysis
            st.subheader("Customer Due Analysis")
            due_customers = customer_summary[customer_summary['due_amount'] > 0]
            st.write(f"Total Due Amount: ${due_customers['due_amount'].sum():,.2f}")
            st.dataframe(due_customers.sort_values('due_amount', ascending=False))
        
        with tab5:
            # Raw Data with download option
            st.subheader("Filtered Data")
            st.write(f"Showing {len(df)} records")
            st.dataframe(df)
            
            # Download button
            def to_excel(df):
                output = io.BytesIO()
                writer = pd.ExcelWriter(output, engine='xlsxwriter')
                df.to_excel(writer, index=False, sheet_name='SalesData')
                writer.close()
                processed_data = output.getvalue()
                return processed_data
            
            excel_data = to_excel(df)
            st.download_button(
                label="📥 Download Filtered Data as Excel",
                data=excel_data,
                file_name="filtered_sales_data.xlsx",
                mime="application/vnd.ms-excel"
            )
    
    else:
        st.info("Please upload a data file to begin analysis")

if __name__ == "__main__":
    main()
