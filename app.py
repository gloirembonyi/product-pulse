import streamlit as st
import pandas as pd
import io
from utils.data_processor import clean_data, detect_data_type, prepare_sample_data
from utils.visualization import create_dashboard, create_trend_plot, create_distribution_plot
from utils.analysis import perform_trend_analysis, segment_data
from utils.chatbot import process_query

# Set page config
st.set_page_config(
    page_title="Product Analytics Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

# Title and description
st.title("Product Analytics Dashboard")
st.markdown("""
This tool helps product managers analyze and visualize data to discover insights and trends.
Upload your data, explore metrics, and even chat with your data using natural language!
""")

# Sidebar for data upload and configuration
with st.sidebar:
    st.header("Data Input")
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    
    if uploaded_file is not None:
        try:
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
            
            st.success(f"Successfully loaded data with {data.shape[0]} rows and {data.shape[1]} columns")
        except Exception as e:
            st.error(f"Error loading data: {e}")
    
    # Sample data option if no data is uploaded
    if st.session_state.data is None:
        if st.button("Use Sample Data"):
            st.session_state.data, st.session_state.data_types, st.session_state.metrics, st.session_state.dimensions, st.session_state.time_columns = prepare_sample_data()
            st.success("Sample product analytics data loaded")

# Main content based on whether data is loaded
if st.session_state.data is not None:
    data = st.session_state.data
    
    # Data Overview Section
    st.header("Data Overview")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.dataframe(data.head(), use_container_width=True)
    
    with col2:
        st.write("Dataset Statistics:")
        st.write(f"- Rows: {data.shape[0]}")
        st.write(f"- Columns: {data.shape[1]}")
        st.write(f"- Metrics: {len(st.session_state.metrics)}")
        st.write(f"- Dimensions: {len(st.session_state.dimensions)}")
        
        # Data Export Option
        if st.button("Generate Report"):
            # Create a buffer
            buffer = io.StringIO()
            
            # Write some markdown
            buffer.write("# Product Analytics Report\n\n")
            buffer.write(f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}\n\n")
            buffer.write("## Dataset Overview\n")
            buffer.write(f"- Rows: {data.shape[0]}\n")
            buffer.write(f"- Columns: {data.shape[1]}\n\n")
            buffer.write("## Summary Statistics\n\n")
            buffer.write(data.describe().to_markdown())
            
            # Convert to string and create download button
            report_data = buffer.getvalue()
            st.download_button(
                label="Download Report",
                data=report_data,
                file_name="product_analytics_report.md",
                mime="text/markdown"
            )
    
    # Dashboard Section
    st.header("Interactive Dashboard")
    
    # Allow user to select metrics and dimensions
    tab1, tab2, tab3 = st.tabs(["Custom Visualizations", "Trend Analysis", "Data Segmentation"])
    
    with tab1:
        st.subheader("Create Custom Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_metrics = st.multiselect(
                "Select metrics to visualize:",
                st.session_state.metrics,
                default=st.session_state.metrics[:1] if st.session_state.metrics else []
            )
        
        with col2:
            selected_dimension = st.selectbox(
                "Group by dimension:",
                ["None"] + st.session_state.dimensions,
                index=0
            )
        
        visual_type = st.selectbox(
            "Visualization type:",
            ["Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot", "Box Plot", "Histogram"]
        )
        
        if selected_metrics:
            # Create and show visualization
            fig = create_dashboard(data, selected_metrics, 
                                  selected_dimension if selected_dimension != "None" else None, 
                                  visual_type)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Please select at least one metric to visualize")
    
    with tab2:
        st.subheader("Trend Analysis")
        
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
                # Perform trend analysis
                trend_data, insights = perform_trend_analysis(
                    data, 
                    time_column, 
                    trend_metric, 
                    options=trend_options
                )
                
                # Display trend plot
                trend_fig = create_trend_plot(trend_data, time_column, trend_metric, trend_options)
                st.plotly_chart(trend_fig, use_container_width=True)
                
                # Show insights
                st.subheader("Trend Insights")
                for insight in insights:
                    st.info(insight)
            except Exception as e:
                st.error(f"Error in trend analysis: {e}")
    
    with tab3:
        st.subheader("Data Segmentation")
        
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
                # Perform segmentation
                segment_data, segment_insights = segment_data(data, segment_by, compare_metric, segment_options)
                
                # Display segmentation visualization
                segment_fig = create_distribution_plot(segment_data, segment_by, compare_metric, segment_options)
                st.plotly_chart(segment_fig, use_container_width=True)
                
                # Show segment insights
                st.subheader("Segment Insights")
                for insight in segment_insights:
                    st.info(insight)
            except Exception as e:
                st.error(f"Error in data segmentation: {e}")
    
    # AI Chatbot Section
    st.header("Data Chat")
    st.markdown("Ask questions about your data in natural language")
    
    # Chat input
    user_query = st.text_input("Ask a question about your data:")
    
    if user_query:
        with st.spinner("Processing your query..."):
            try:
                response = process_query(user_query, data)
                
                # Add to chat history
                st.session_state.chat_history.append({"user": user_query, "bot": response})
                
                # Clear input
                user_query = ""
            except Exception as e:
                st.error(f"Error processing query: {e}")
    
    # Display chat history
    for chat in st.session_state.chat_history:
        st.markdown(f"**You:** {chat['user']}")
        st.markdown(f"**AI:** {chat['bot']}")
        st.markdown("---")

else:
    # Show welcome message and instructions when no data is loaded
    st.info("Please upload a CSV file or use sample data to get started.")
    
    st.markdown("""
    ### How to use this tool:
    
    1. **Upload Data**: Start by uploading your CSV file using the sidebar
    2. **Explore Dashboard**: Visualize key metrics and dimensions
    3. **Analyze Trends**: Identify patterns and anomalies over time
    4. **Segment Data**: Compare different user groups and behaviors
    5. **Chat with Data**: Ask questions in natural language
    
    Common data formats for product analytics include user behavior data, conversion metrics, 
    engagement statistics, and feature usage information.
    """)
