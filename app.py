import streamlit as st
import pandas as pd
import io
import base64
import json
import uuid
from datetime import datetime
import plotly.express as px
from utils.data_processor import clean_data, detect_data_type, prepare_sample_data
from utils.visualization import create_dashboard, create_trend_plot, create_distribution_plot
from utils.analysis import perform_trend_analysis, segment_data
from utils.chatbot import process_query, generate_insights
from utils.database import (
    save_dataset, get_saved_datasets, load_dataset, delete_dataset,
    save_analysis, get_saved_analyses, load_analysis, delete_analysis
)

# Set page config
st.set_page_config(
    page_title="Product Analytics Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS to enhance the appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4267B2;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #4C4C6D;
        margin-bottom: 1rem;
    }
    .insight-card {
        background-color: #F8F9FA;
        border-left: 5px solid #4267B2;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: white;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #4267B2;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
    }
    .tab-container {
        border-radius: 0.5rem;
        padding: 1rem;
        background-color: #F0F2F5;
    }
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #F8F9FA;
        margin-bottom: 1rem;
    }
    .chat-user {
        background-color: #4267B2;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 1rem 1rem 0 1rem;
        margin: 0.5rem 0;
        display: inline-block;
        max-width: 80%;
    }
    .chat-bot {
        background-color: #E9EBEE;
        color: #1C1E21;
        padding: 0.5rem 1rem;
        border-radius: 1rem 1rem 1rem 0;
        margin: 0.5rem 0;
        display: inline-block;
        max-width: 80%;
    }
    .stButton button {
        background-color: #4267B2;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
    }
    /* Make the Streamlit tabs more attractive */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        margin-bottom: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 4px 4px 0 0;
        background-color: #f0f2f5;
        color: #4C4C6D;
        border-bottom: 2px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: white;
        border-bottom: 2px solid #4267B2;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'data' not in st.session_state:
    st.session_state.data = None
if 'data_types' not in st.session_state:
    st.session_state.data_types = None
if 'metrics' not in st.session_state:
    st.session_state.metrics = []
if 'dimensions' not in st.session_state:
    st.session_state.dimensions = []
if 'time_columns' not in st.session_state:
    st.session_state.time_columns = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'auto_insights' not in st.session_state:
    st.session_state.auto_insights = []
if 'dashboard_tab' not in st.session_state:
    st.session_state.dashboard_tab = 0
if 'refresh_insights' not in st.session_state:
    st.session_state.refresh_insights = False
if 'current_dataset_id' not in st.session_state:
    st.session_state.current_dataset_id = None
if 'current_dataset_name' not in st.session_state:
    st.session_state.current_dataset_name = ""
if 'saved_analyses' not in st.session_state:
    st.session_state.saved_analyses = None

# Helper functions
def add_logo():
    """Add a logo to the sidebar"""
    st.sidebar.markdown(
        """
        <div style="text-align: center; padding: 1.5rem 0; background: linear-gradient(135deg, #4267B2, #5B86E5); border-radius: 0.5rem; margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <h2 style="color: white; margin: 0; font-weight: 600;">
                <span style="margin-right: 10px;">📊</span> ProductPulse
            </h2>
            <p style="font-size: 0.9rem; color: rgba(255, 255, 255, 0.8); margin-top: 0.5rem;">
                Advanced Analytics for Product Managers
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

def get_current_date():
    """Return formatted current date"""
    now = datetime.now()
    return now.strftime("%B %d, %Y")

def format_number(num):
    """Format numbers for display"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return f"{num:.1f}"

# Functions for database operations
def load_saved_dataset(dataset_id):
    """Load a dataset from the database"""
    try:
        with st.spinner("Loading dataset from database..."):
            df, column_data = load_dataset(dataset_id)
            
            # Set up metrics, dimensions and time columns
            metrics = column_data[column_data['is_metric']]['name'].tolist()
            dimensions = column_data[column_data['is_dimension']]['name'].tolist()
            time_columns = column_data[column_data['is_time']]['name'].tolist()
            
            # Extract dataset name
            all_datasets = get_saved_datasets()
            dataset_name = all_datasets[all_datasets['id'] == dataset_id]['name'].iloc[0]
            
            # Store in session state
            st.session_state.data = df
            st.session_state.metrics = metrics
            st.session_state.dimensions = dimensions
            st.session_state.time_columns = time_columns
            st.session_state.current_dataset_id = dataset_id
            st.session_state.current_dataset_name = dataset_name
            
            # Generate auto insights
            st.session_state.auto_insights = generate_insights(df)
            
            return True
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        return False

# Sidebar for data upload and configuration
with st.sidebar:
    add_logo()
    
    st.markdown("---")
    
    # Create tabs for data input methods with custom styling
    st.markdown("""
    <style>
        div[data-testid="stHorizontalBlock"] {
            background-color: #F0F2F5;
            border-radius: 0.5rem;
            padding: 0.5rem;
            margin-bottom: 1rem;
        }
        div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] {
            background-color: transparent;
            padding: 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    input_tab1, input_tab2 = st.tabs(["📤 Upload Data", "📁 Saved Datasets"])
    
    with input_tab1:
        st.header("Data Input")
        
        # File upload with nicer UI
        uploaded_file = st.file_uploader("Upload your CSV data", type=["csv"])
        
        if uploaded_file is not None:
            try:
                with st.spinner("Processing your data..."):
                    # Read the data
                    data = pd.read_csv(uploaded_file)
                    
                    # Clean the data
                    data = clean_data(data)
                    
                    # Detect data types and columns
                    data_types, metrics, dimensions, time_columns = detect_data_type(data)
                    
                    # Store in session state
                    st.session_state.data = data
                    st.session_state.data_types = data_types
                    st.session_state.metrics = metrics
                    st.session_state.dimensions = dimensions
                    st.session_state.time_columns = time_columns
                    
                    # Reset current dataset ID (this is a new upload)
                    st.session_state.current_dataset_id = None
                    st.session_state.current_dataset_name = uploaded_file.name.replace(".csv", "")
                    
                    # Generate auto insights
                    st.session_state.auto_insights = generate_insights(data)
                    
                    st.success(f"✅ Loaded data: {data.shape[0]} rows × {data.shape[1]} columns")
            except Exception as e:
                st.error(f"Error loading data: {e}")
        
        # Sample data option with a nicer button
        if st.session_state.data is None:
            st.markdown(
                """
                <div style="text-align: center; margin: 1rem 0;">
                    <p>No data uploaded yet. You can:</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            if st.button("📊 Use Sample Product Analytics Data"):
                with st.spinner("Generating sample data..."):
                    st.session_state.data, st.session_state.data_types, st.session_state.metrics, st.session_state.dimensions, st.session_state.time_columns = prepare_sample_data()
                    # Reset current dataset ID (this is sample data)
                    st.session_state.current_dataset_id = None
                    st.session_state.current_dataset_name = "Sample Product Analytics"
                    # Generate auto insights
                    st.session_state.auto_insights = generate_insights(st.session_state.data)
                    st.success("✅ Sample product analytics data loaded!")
    
    with input_tab2:
        st.header("Saved Datasets")
        
        # Display saved datasets
        try:
            saved_datasets = get_saved_datasets()
            
            if not saved_datasets.empty:
                # Format the dataset list
                for _, row in saved_datasets.iterrows():
                    st.markdown(f"""
                    <div style="margin-bottom: 0.5rem; padding: 0.5rem; background-color: #F8F9FA; border-radius: 0.3rem;">
                        <strong>{row['name']}</strong><br>
                        <small>{row['rows']} rows, {row['columns']} columns</small><br>
                        <small>Last modified: {row['last_modified'].strftime('%Y-%m-%d')}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button(f"📂 Load", key=f"load_{row['id']}"):
                            if load_saved_dataset(row['id']):
                                st.success(f"Dataset '{row['name']}' loaded successfully!")
                    with col2:
                        if st.button(f"🗑️ Delete", key=f"delete_{row['id']}"):
                            if delete_dataset(row['id']):
                                st.success(f"Dataset '{row['name']}' deleted.")
                                st.rerun()
            else:
                st.info("No saved datasets found. Upload a dataset and save it first.")
                
        except Exception as e:
            st.error(f"Error loading saved datasets: {e}")
    
    # Add data info section
    if st.session_state.data is not None:
        st.markdown("---")
        st.subheader("Data Overview")
        
        # Dataset Name
        if st.session_state.current_dataset_name:
            st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <strong>Dataset:</strong> {st.session_state.current_dataset_name}
            </div>
            """, unsafe_allow_html=True)
        
        # Save dataset option
        with st.expander("💾 Save Current Dataset"):
            dataset_name = st.text_input("Dataset Name", value=st.session_state.current_dataset_name)
            dataset_desc = st.text_area("Description (optional)", height=80)
            
            if st.button("Save Dataset"):
                if dataset_name:
                    with st.spinner("Saving dataset to database..."):
                        try:
                            dataset_id = save_dataset(st.session_state.data, dataset_name, dataset_desc)
                            st.session_state.current_dataset_id = dataset_id
                            st.session_state.current_dataset_name = dataset_name
                            st.success(f"Dataset '{dataset_name}' saved successfully!")
                        except Exception as e:
                            st.error(f"Error saving dataset: {e}")
                else:
                    st.error("Please enter a dataset name.")
        
        # Metrics count
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(st.session_state.metrics)}</div>
            <div class="metric-label">Metrics available</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Dimensions count
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(st.session_state.dimensions)}</div>
            <div class="metric-label">Dimensions available</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.time_columns:
            time_range = "Available"
        else:
            time_range = "Not available"
            
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{time_range}</div>
            <div class="metric-label">Time series analysis</div>
        </div>
        """, unsafe_allow_html=True)

# Main content
# Use custom HTML for header
st.markdown(
    """
    <div style="padding: 1rem 0 2rem 0;">
        <h1 class="main-header">Product Analytics Dashboard</h1>
        <p class="sub-header">Discover insights, track metrics, and make data-driven decisions</p>
    </div>
    """, 
    unsafe_allow_html=True
)

# Main content based on whether data is loaded
if st.session_state.data is not None:
    data = st.session_state.data
    
    # Create a dashboard container
    st.markdown('<div class="tab-container">', unsafe_allow_html=True)
    
    # Create tabs with icons
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview", 
        "📈 Interactive Dashboard", 
        "📆 Trend Analysis", 
        "🔍 Segmentation", 
        "🤖 AI Assistant",
        "💾 Saved Analyses"
    ])
    
    with tab1:
        # Data Overview Section with Key Metrics
        st.markdown('<h2 class="sub-header">Data Overview</h2>', unsafe_allow_html=True)
        
        # Add a date indicator
        st.markdown(f"<p style='text-align: right; color: #6c757d;'>Analysis date: {get_current_date()}</p>", unsafe_allow_html=True)
        
        # Show data sample with improved styling
        st.markdown('<h3 style="font-size: 1.2rem; margin-top: 1rem;">Data Sample</h3>', unsafe_allow_html=True)
        st.dataframe(data.head(5), use_container_width=True, height=180)
        
        # Key metrics section
        st.markdown('<h3 style="font-size: 1.2rem; margin-top: 1.5rem;">Key Metrics</h3>', unsafe_allow_html=True)
        
        # Display key summary statistics in a more visual way
        col1, col2, col3 = st.columns(3)
        
        # Find the most important metrics
        if st.session_state.metrics:
            primary_metric = st.session_state.metrics[0]
            metric_avg = data[primary_metric].mean()
            metric_max = data[primary_metric].max()
            
            col1.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{primary_metric}</div>
                <div class="metric-value">{format_number(metric_avg)}</div>
                <div class="metric-label">Average</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Show active users if available
        if 'user_id' in data.columns:
            unique_users = data['user_id'].nunique()
            col2.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Users</div>
                <div class="metric-value">{format_number(unique_users)}</div>
                <div class="metric-label">Unique</div>
            </div>
            """, unsafe_allow_html=True)
        elif len(st.session_state.metrics) > 1:
            second_metric = st.session_state.metrics[1]
            metric2_avg = data[second_metric].mean()
            col2.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{second_metric}</div>
                <div class="metric-value">{format_number(metric2_avg)}</div>
                <div class="metric-label">Average</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Show conversion if available
        if 'conversion' in data.columns:
            conversion_rate = data['conversion'].mean() * 100
            col3.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Conversion</div>
                <div class="metric-value">{conversion_rate:.1f}%</div>
                <div class="metric-label">Rate</div>
            </div>
            """, unsafe_allow_html=True)
        elif len(st.session_state.metrics) > 2:
            third_metric = st.session_state.metrics[2]
            metric3_avg = data[third_metric].mean()
            col3.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{third_metric}</div>
                <div class="metric-value">{format_number(metric3_avg)}</div>
                <div class="metric-label">Average</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Auto-insights section
        st.markdown('<h3 style="font-size: 1.2rem; margin-top: 1.5rem;">Key Insights</h3>', unsafe_allow_html=True)
        
        for i, insight in enumerate(st.session_state.auto_insights):
            st.markdown(f"""
            <div class="insight-card">
                <p style="margin: 0;">💡 {insight}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Data Export Options
        st.markdown('<h3 style="font-size: 1.2rem; margin-top: 1.5rem;">Export Options</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Generate Report"):
                # Create a buffer
                buffer = io.StringIO()
                
                # Write some markdown
                buffer.write(f"# Product Analytics Report\n\n")
                buffer.write(f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}\n\n")
                buffer.write("## Dataset Overview\n")
                buffer.write(f"- Rows: {data.shape[0]}\n")
                buffer.write(f"- Columns: {data.shape[1]}\n\n")
                buffer.write("## Key Metrics\n\n")
                
                # Add metrics
                for metric in st.session_state.metrics[:5]:  # First 5 metrics
                    buffer.write(f"### {metric}\n")
                    buffer.write(f"- Mean: {data[metric].mean():.2f}\n")
                    buffer.write(f"- Median: {data[metric].median():.2f}\n")
                    buffer.write(f"- Min: {data[metric].min():.2f}\n")
                    buffer.write(f"- Max: {data[metric].max():.2f}\n\n")
                
                # Add insights
                buffer.write("## Insights\n\n")
                for insight in st.session_state.auto_insights:
                    buffer.write(f"- {insight}\n")
                
                buffer.write("\n## Summary Statistics\n\n")
                # Convert the describe dataframe to a string format manually instead of using to_markdown()
                # Using a safer approach to format statistics
                stats_df = data.describe().reset_index()
                
                # Get column names as strings
                header = ["Statistic"]
                for col in stats_df.columns[1:]:
                    header.append(str(col))
                
                buffer.write("| " + " | ".join(header) + " |\n")
                buffer.write("| " + " | ".join(["---" for _ in range(len(header))]) + " |\n")
                
                # Process each row
                for idx in range(len(stats_df)):
                    row_values = [str(stats_df.iloc[idx, 0])]  # First column (statistic name)
                    
                    # Process numeric columns
                    for col_idx in range(1, len(stats_df.columns)):
                        val = stats_df.iloc[idx, col_idx]
                        if isinstance(val, (int, float)):
                            row_values.append(f"{val:.2f}")
                        else:
                            row_values.append(str(val))
                    
                    buffer.write("| " + " | ".join(row_values) + " |\n")
                
                # Convert to string and create download button
                report_data = buffer.getvalue()
                st.download_button(
                    label="Download Report",
                    data=report_data,
                    file_name=f"product_analytics_report_{pd.Timestamp.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown"
                )
        
        with col2:
            # CSV Download
            csv_buffer = io.StringIO()
            data.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="💾 Download Processed Data",
                data=csv_data,
                file_name=f"processed_data_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with tab2:
        # Interactive Dashboard Section
        st.markdown('<h2 class="sub-header">Interactive Dashboard</h2>', unsafe_allow_html=True)
        
        # Improved UI for selecting metrics and dimensions
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            selected_metrics = st.multiselect(
                "Select metrics:",
                st.session_state.metrics,
                default=st.session_state.metrics[:1] if st.session_state.metrics else []
            )
        
        with col2:
            selected_dimension = st.selectbox(
                "Group by dimension:",
                ["None"] + st.session_state.dimensions,
                index=0
            )
        
        with col3:
            visual_type = st.selectbox(
                "Chart type:",
                ["Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot", "Box Plot", "Histogram"]
            )
        
        if selected_metrics:
            # Create and show visualization with improved styling
            fig = create_dashboard(data, selected_metrics, 
                                  selected_dimension if selected_dimension != "None" else None, 
                                  visual_type)
            st.plotly_chart(fig, use_container_width=True, height=500)
            
            # Add a description of the chart
            metric_names = ", ".join(selected_metrics)
            if selected_dimension != "None":
                st.markdown(f"""
                <div style="background-color: #F0F2F5; padding: 0.75rem; border-radius: 0.5rem; font-size: 0.85rem;">
                    <strong>Chart Description:</strong> This {visual_type.lower()} shows {metric_names} grouped by {selected_dimension}.
                    Use this visualization to compare {metric_names} across different {selected_dimension} categories.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #F0F2F5; padding: 0.75rem; border-radius: 0.5rem; font-size: 0.85rem;">
                    <strong>Chart Description:</strong> This {visual_type.lower()} shows {metric_names} across your data.
                    Use this visualization to understand the overall {metric_names} metrics.
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Please select at least one metric to visualize")
    
    with tab3:
        # Trend Analysis Section
        st.markdown('<h2 class="sub-header">Trend Analysis</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.time_columns:
                time_column = st.selectbox("Select time column:", st.session_state.time_columns)
                trend_metric = st.selectbox("Select metric to analyze:", st.session_state.metrics)
            else:
                st.warning("No time columns detected in your data")
                time_column = None
                trend_metric = None
        
        with col2:
            trend_options = st.multiselect(
                "Analysis options:",
                ["Moving Average", "Trend Line", "Seasonality", "Outliers"],
                default=["Moving Average", "Trend Line"]
            )
        
        if time_column and trend_metric:
            try:
                with st.spinner("Analyzing trends..."):
                    # Perform trend analysis
                    trend_data, insights = perform_trend_analysis(
                        data, 
                        time_column, 
                        trend_metric, 
                        options=trend_options
                    )
                    
                    # Display trend plot with improved styling
                    trend_fig = create_trend_plot(trend_data, time_column, trend_metric, trend_options)
                    st.plotly_chart(trend_fig, use_container_width=True, height=500)
                    
                    # Show insights in a more attractive way
                    st.markdown('<h3 style="font-size: 1.2rem; margin-top: 1rem;">Trend Insights</h3>', unsafe_allow_html=True)
                    
                    for insight in insights:
                        st.markdown(f"""
                        <div class="insight-card">
                            <p style="margin: 0;">📈 {insight}</p>
                        </div>
                        """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error in trend analysis: {e}")
    
    with tab4:
        # Data Segmentation Section
        st.markdown('<h2 class="sub-header">Data Segmentation</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            segment_by = st.selectbox("Segment by dimension:", st.session_state.dimensions)
            compare_metric = st.selectbox("Compare metric:", st.session_state.metrics)
        
        with col2:
            segment_options = st.multiselect(
                "Segment options:",
                ["Value Distribution", "Compare to Average", "Detect Outliers"],
                default=["Value Distribution"]
            )
        
        if segment_by and compare_metric:
            try:
                with st.spinner("Analyzing segments..."):
                    # Perform segmentation
                    segment_data, segment_insights = segment_data(data, segment_by, compare_metric, segment_options)
                    
                    # Display segmentation visualization with improved styling
                    segment_fig = create_distribution_plot(segment_data, segment_by, compare_metric, segment_options)
                    st.plotly_chart(segment_fig, use_container_width=True, height=500)
                    
                    # Show segment insights in a more attractive way
                    st.markdown('<h3 style="font-size: 1.2rem; margin-top: 1rem;">Segment Insights</h3>', unsafe_allow_html=True)
                    
                    for insight in segment_insights:
                        st.markdown(f"""
                        <div class="insight-card">
                            <p style="margin: 0;">🔍 {insight}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    # Add a callout with recommendations
                    st.markdown(f"""
                    <div style="background-color: #E9F7EF; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;">
                        <h4 style="margin-top: 0; font-size: 1rem;">Recommendations</h4>
                        <p>Based on the segmentation analysis, consider these actions:</p>
                        <ul>
                            <li>Investigate why certain segments perform differently</li>
                            <li>Create targeted strategies for high-performing segments</li>
                            <li>Address issues in underperforming segments</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error in data segmentation: {e}")
    
    with tab5:
        # AI Assistant Section with improved UI
        st.markdown('<h2 class="sub-header">AI Data Assistant</h2>', unsafe_allow_html=True)
        st.markdown("""
        <p style="margin-bottom: 1.5rem;">
            Ask questions about your data in natural language and get AI-powered insights.
        </p>
        """, unsafe_allow_html=True)
        
        # Chat container
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Display chat history with better formatting
        if st.session_state.chat_history:
            for chat in st.session_state.chat_history:
                st.markdown(f"""
                <div style="text-align: right; margin-bottom: 0.5rem;">
                    <div class="chat-user">{chat['user']}</div>
                </div>
                <div style="text-align: left; margin-bottom: 1rem;">
                    <div class="chat-bot">{chat['bot']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Suggested prompts
            st.markdown("""
            <p style="color: #6c757d; text-align: center; margin: 2rem 0;">
                No chat history yet. Try asking a question below or use one of the suggested prompts.
            </p>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Suggestion chips
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Summarize key metrics"):
                with st.spinner("Analyzing..."):
                    query = "Summarize the key metrics in this dataset"
                    response = process_query(query, data)
                    st.session_state.chat_history.append({"user": query, "bot": response})
                    st.rerun()
        
        with col2:
            if st.button("🔍 Identify patterns"):
                with st.spinner("Analyzing..."):
                    query = "What interesting patterns do you see in this data?"
                    response = process_query(query, data)
                    st.session_state.chat_history.append({"user": query, "bot": response})
                    st.rerun()
        
        with col3:
            if st.button("🚀 Suggest improvements"):
                with st.spinner("Analyzing..."):
                    query = "Based on this data, what product improvements would you suggest?"
                    response = process_query(query, data)
                    st.session_state.chat_history.append({"user": query, "bot": response})
                    st.rerun()
        
        # Chat input with better styling
        with st.form(key="chat_form", clear_on_submit=True):
            user_query = st.text_input("Ask a question about your data:", key="chat_input")
            submit_button = st.form_submit_button("💬 Send")
        
        if submit_button and user_query:
            with st.spinner("Processing your query..."):
                try:
                    response = process_query(user_query, data)
                    
                    # Add to chat history
                    st.session_state.chat_history.append({"user": user_query, "bot": response})
                    
                    # Rerun to update the UI
                    st.rerun()
                except Exception as e:
                    st.error(f"Error processing query: {e}")
    
    # Close the dashboard container
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # Show welcome message and instructions when no data is loaded with improved styling
    st.markdown("""
    <div style="text-align: center; padding: 3rem 1rem; background-color: #F8F9FA; border-radius: 1rem; margin: 2rem 0;">
        <h1 style="color: #4267B2; font-size: 2rem;">Welcome to ProductPulse</h1>
        <p style="font-size: 1.2rem; margin: 1rem 0;">Your advanced analytics dashboard for product managers</p>
        <img src="https://img.icons8.com/fluency/96/null/combo-chart--v2.png" style="margin: 1.5rem 0;" alt="Analytics Icon"/>
        <p style="margin: 2rem 0 1rem 0;">Please upload a CSV file or use sample data to get started</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Instructions with better formatting
    st.markdown("""
    <div style="padding: 1.5rem; background-color: white; border-radius: 1rem; box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.1);">
        <h3 style="color: #4267B2; font-size: 1.3rem; margin-bottom: 1rem;">How to use this tool:</h3>
        
        <div style="display: flex; align-items: flex-start; margin-bottom: 1rem;">
            <div style="background-color: #4267B2; color: white; border-radius: 50%; width: 25px; height: 25px; display: flex; justify-content: center; align-items: center; margin-right: 10px;">1</div>
            <div><strong>Upload Data:</strong> Start by uploading your CSV file using the sidebar or use our sample dataset</div>
        </div>
        
        <div style="display: flex; align-items: flex-start; margin-bottom: 1rem;">
            <div style="background-color: #4267B2; color: white; border-radius: 50%; width: 25px; height: 25px; display: flex; justify-content: center; align-items: center; margin-right: 10px;">2</div>
            <div><strong>Explore Dashboard:</strong> Visualize key metrics and dimensions with interactive charts</div>
        </div>
        
        <div style="display: flex; align-items: flex-start; margin-bottom: 1rem;">
            <div style="background-color: #4267B2; color: white; border-radius: 50%; width: 25px; height: 25px; display: flex; justify-content: center; align-items: center; margin-right: 10px;">3</div>
            <div><strong>Analyze Trends:</strong> Identify patterns and anomalies over time with our trend analysis</div>
        </div>
        
        <div style="display: flex; align-items: flex-start; margin-bottom: 1rem;">
            <div style="background-color: #4267B2; color: white; border-radius: 50%; width: 25px; height: 25px; display: flex; justify-content: center; align-items: center; margin-right: 10px;">4</div>
            <div><strong>Segment Data:</strong> Compare different user groups and behaviors</div>
        </div>
        
        <div style="display: flex; align-items: flex-start; margin-bottom: 1rem;">
            <div style="background-color: #4267B2; color: white; border-radius: 50%; width: 25px; height: 25px; display: flex; justify-content: center; align-items: center; margin-right: 10px;">5</div>
            <div><strong>Chat with Data:</strong> Ask questions in natural language and get AI-powered insights</div>
        </div>
    </div>
    
    <div style="margin-top: 2rem; padding: 1rem; background-color: #E9F7EF; border-radius: 0.5rem;">
        <h4 style="color: #4267B2; margin-top: 0;">Data Format Tips</h4>
        <p>Common data formats for product analytics include:</p>
        <ul>
            <li>User behavior data (pageviews, sessions, interactions)</li>
            <li>Conversion metrics and funnels</li>
            <li>Engagement statistics (session duration, feature usage)</li>
            <li>User demographics and segments</li>
            <li>Time-based metrics for trend analysis</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
