import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io
import os

# Page configuration
st.set_page_config(page_title="Metal Price Analyzer", page_icon="📊", layout="wide")

st.title("🔩 Metal Price Data Analyzer")
st.markdown("Analyze and download historical price data for Copper, Aluminum, and Iron")

# File paths
COPPER_FILE = "LME_Copper.csv"
ALUMINUM_FILE = "LME_Aluminium.csv"
IRON_FILE = "LME_Iron.csv"

def load_and_process_data(file_path):
    """Load CSV from file path and ensure date and price columns are properly formatted"""
    if file_path and os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            # Strip whitespace from column names
            df.columns = df.columns.str.strip()
            # Try to find date column (case insensitive)
            date_col = [col for col in df.columns if col.lower() == 'date']
            if date_col:
                df['date'] = pd.to_datetime(df[date_col[0]], dayfirst=True)
                if date_col[0] != 'date':
                    df = df.drop(columns=[date_col[0]])
            else:
                df['date'] = pd.to_datetime(df.iloc[:, 0], dayfirst=True)
            
            # Try to find price column (case insensitive)
            price_col = [col for col in df.columns if col.lower() == 'price']
            if price_col:
                df['price'] = pd.to_numeric(df[price_col[0]], errors='coerce')
                if price_col[0] != 'price':
                    df = df.drop(columns=[price_col[0]])
            
            df = df.sort_values('date').reset_index(drop=True)
            return df
        except Exception as e:
            st.error(f"Error loading {file_path}: {str(e)}")
            return None
    return None

def filter_data(df, date_range, month_filter, year_filter):
    """Apply filters to dataframe"""
    filtered_df = df.copy()
    
    # Date range filter
    if date_range:
        filtered_df = filtered_df[(filtered_df['date'] >= pd.to_datetime(date_range[0])) & 
                                  (filtered_df['date'] <= pd.to_datetime(date_range[1]))]
    
    # Month filter
    if month_filter and month_filter != "All":
        month_num = datetime.strptime(month_filter, "%B").month
        filtered_df = filtered_df[filtered_df['date'].dt.month == month_num]
    
    # Year filter
    if year_filter and year_filter != "All":
        filtered_df = filtered_df[filtered_df['date'].dt.year == int(year_filter)]
    
    return filtered_df

def create_download_button(df, filename, button_label):
    """Create a download button for filtered data"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    output.seek(0)
    
    st.download_button(
        label=button_label,
        data=output,
        file_name=filename,
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def display_metal_tab(df, metal_name, color):
    """Display content for each metal tab"""
    if df is None:
        st.warning(f"⚠️ {metal_name} data file not found. Please ensure the CSV file is in the folder.")
        return
    
    st.subheader(f"📈 {metal_name} Price Analysis")
    
    # Filters in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Year filter
        years = ["All"] + sorted(df['date'].dt.year.unique().astype(str).tolist(), reverse=True)
        year_filter = st.selectbox(f"Select Year", years, key=f"{metal_name}_year")
    
    with col2:
        # Month filter
        months = ["All", "January", "February", "March", "April", "May", "June", 
                  "July", "August", "September", "October", "November", "December"]
        month_filter = st.selectbox(f"Select Month", months, key=f"{metal_name}_month")
    
    with col3:
        # Date range filter
        use_date_range = st.checkbox("Use Date Range", key=f"{metal_name}_use_range")
    
    date_range = None
    if use_date_range:
        col_a, col_b = st.columns(2)
        with col_a:
            start_date = st.date_input("Start Date", df['date'].min(), key=f"{metal_name}_start")
        with col_b:
            end_date = st.date_input("End Date", df['date'].max(), key=f"{metal_name}_end")
        date_range = (start_date, end_date)
    
    # Apply filters
    filtered_df = filter_data(df, date_range, month_filter, year_filter)
    
    # Display metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Total Records", len(filtered_df))
    with col_m2:
        st.metric("Average Price", f"${filtered_df['price'].mean():.2f}")
    with col_m3:
        st.metric("Min Price", f"${filtered_df['price'].min():.2f}")
    with col_m4:
        st.metric("Max Price", f"${filtered_df['price'].max():.2f}")
    
    # Plot
    fig = px.line(filtered_df, x='date', y='price', 
                  title=f"{metal_name} Price Over Time",
                  labels={'date': 'Date', 'price': 'Price ($)'},
                  color_discrete_sequence=[color])
    fig.update_layout(height=400, hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.subheader("📊 Data Table")
    st.dataframe(filtered_df, use_container_width=True, height=300)
    
    # Download buttons
    st.subheader("💾 Download Options")
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        create_download_button(
            filtered_df, 
            f"{metal_name.lower()}_filtered_data.xlsx",
            f"📥 Download Filtered Data ({len(filtered_df)} records)"
        )
    
    with col_d2:
        create_download_button(
            df, 
            f"{metal_name.lower()}_complete_data.xlsx",
            f"📥 Download Complete Dataset ({len(df)} records)"
        )

# Load data from files
cu_df = load_and_process_data(COPPER_FILE)
al_df = load_and_process_data(ALUMINUM_FILE)
fe_df = load_and_process_data(IRON_FILE)

# Create tabs
tab1, tab2, tab3 = st.tabs(["🟠 Copper (Cu)", "⚪ Aluminum (Al)", "🔴 Iron (Fe)"])

with tab1:
    display_metal_tab(cu_df, "Copper", "#FF6B35")

with tab2:
    display_metal_tab(al_df, "Aluminum", "#4ECDC4")

with tab3:
    display_metal_tab(fe_df, "Iron", "#95A3A4")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("📁 Data files loaded from:\n- LME_Copper.csv\n- LME_Aluminium.csv\n- LME_Iron.csv")