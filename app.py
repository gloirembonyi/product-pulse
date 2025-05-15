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
from utils.chatbot import process_query, generate_insights, reload_api_config
from utils.database import (
    save_dataset, get_saved_datasets, load_dataset, delete_dataset,
    save_analysis, get_saved_analyses, load_analysis, delete_analysis
)
import os
import numpy as np
from sklearn.cluster import KMeans

# Set page config with a modern look
st.set_page_config(
    page_title="ProductPulse Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Enhanced Custom CSS with modern design - improved version
st.markdown("""
<style>
    /* Modern color palette with enhanced gradients */
    :root {
        --primary-color: #4361ee;
        --primary-light: #4895ef;
        --secondary-color: #3a0ca3;
        --accent-color: #4cc9f0;
        --background-color: #f8f9fa;
        --card-color: #ffffff;
        --text-color: #2b2d42;
        --light-text: #8d99ae;
        --border-radius: 1rem;
        --shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        --hover-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
        --gradient: linear-gradient(120deg, var(--primary-color), var(--accent-color));
    }

    /* Optimized spacing */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 95%;
    }
    
    .stApp {
        line-height: 1.4;
    }
    
    /* Typography */
    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: var(--background-color);
        color: var(--text-color);
    }

    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        background: var(--gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        line-height: 1.2;
        animation: fadeIn 0.8s ease-in-out;
    }

    .sub-header {
        font-size: 1.6rem;
        color: var(--text-color);
        font-weight: 600;
        margin-bottom: 1.2rem;
        opacity: 0.9;
        line-height: 1.2;
    }
    
    /* Pro section styling for How to use this tool */
    .how-to-section {
        background: white;
        border-radius: var(--border-radius);
        padding: 1.2rem;
        box-shadow: var(--shadow);
        margin-bottom: 1.5rem;
        position: relative;
        border-left: 4px solid var(--primary-color);
    }
    
    .how-to-section h3 {
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
        color: var(--primary-color);
    }
    
    .feature-step {
        display: flex;
        align-items: flex-start;
        margin-bottom: 0.8rem;
        padding: 0.6rem;
        border-radius: 0.5rem;
        background: rgba(248, 249, 250, 0.7);
        transition: all 0.2s ease;
    }
    
    .feature-step:hover {
        background: rgba(236, 240, 253, 0.7);
        transform: translateX(3px);
    }
    
    .step-number {
        background: var(--gradient);
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.9rem;
        margin-right: 0.8rem;
        flex-shrink: 0;
    }
    
    .step-content {
        flex: 1;
    }
    
    .step-title {
        font-weight: 600;
        color: var(--secondary-color);
        margin-bottom: 0.2rem;
    }
    
    .step-description {
        font-size: 0.9rem;
        color: var(--light-text);
    }
    
    .pro-badge {
        position: absolute;
        top: -10px;
        right: -10px;
        background: linear-gradient(45deg, #ff6b6b, #ff8e53);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(255, 107, 107, 0.4);
    }

    /* Cards and Containers with glass morphism - reduced spacing */
    .insight-card {
        background: var(--card-color);
        border-radius: var(--border-radius);
        padding: 1.2rem;
        box-shadow: var(--shadow);
        margin-bottom: 1.2rem;
        border: 1px solid rgba(255, 255, 255, 0.3);
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }

    .insight-card:hover {
        transform: translateY(-5px);
        box-shadow: var(--hover-shadow);
        border-left: 4px solid var(--primary-color);
    }

    .metric-card {
        background: var(--card-color);
        border-radius: var(--border-radius);
        padding: 1.2rem;
        box-shadow: var(--shadow);
        margin: 0.8rem 0;
        border: 1px solid rgba(255, 255, 255, 0.3);
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }

    .metric-card:hover {
        transform: scale(1.02);
        box-shadow: var(--hover-shadow);
    }

    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }

    .metric-label {
        font-size: 1rem;
        color: var(--light-text);
        font-weight: 500;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 3px;
        background: rgba(248, 249, 250, 0.7);
        padding: 0.5rem;
        border-radius: var(--border-radius);
        backdrop-filter: blur(5px);
    }

    .stTabs [data-baseweb="tab"] {
        height: 2.8rem;
        background: white;
        border-radius: 0.75rem;
        color: var(--text-color);
        font-weight: 500;
        transition: all 0.3s ease;
        padding: 0 1.2rem;
    }

    .stTabs [aria-selected="true"] {
        background: var(--gradient);
        color: white;
        font-weight: 600;
    }

    /* DataFrames and Tables with better readability */
    .dataframe {
        border-radius: 0.75rem;
        overflow: hidden;
        border: 1px solid rgba(0, 0, 0, 0.05);
        box-shadow: var(--shadow);
        font-size: 0.9rem;
    }

    .dataframe th {
        background: var(--gradient);
        color: white;
        padding: 0.8rem 1rem;
        font-weight: 600;
    }

    .dataframe td {
        padding: 0.8rem 1rem;
        border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    }
    
    /* Streamlit native elements styling */
    .css-1544g2n {
        padding: 0.5rem 1rem !important;
    }
    
    .css-12w0qpk {
        background-color: var(--background-color);
    }
    
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
    }
    
    /* Footer styling */
    footer {
        visibility: hidden;
    }
    
    /* Upload file area enhancement */
    [data-testid="stFileUploader"] {
        border: 2px dashed var(--primary-light);
        border-radius: 0.8rem;
        padding: 0.8rem;
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(5px);
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: var(--primary-color);
        background: rgba(255, 255, 255, 0.8);
    }
    
    /* Tooltip styling */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
        color: var(--primary-color);
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: var(--secondary-color);
        color: white;
        text-align: center;
        border-radius: 6px;
        padding: 8px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 0.8rem;
        box-shadow: var(--shadow);
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    
    .status-active {
        background-color: #10b981;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
    }
    
    .status-inactive {
        background-color: #6c757d;
    }
    
    .status-warning {
        background-color: #ffbe0b;
    }

    /* Chat Interface with more depth */
    .chat-container {
        max-height: 450px;
        overflow-y: auto;
        padding: 1.2rem;
        border-radius: var(--border-radius);
        background: var(--card-color);
        box-shadow: var(--shadow);
        margin-bottom: 1.2rem;
        border: 1px solid rgba(255, 255, 255, 0.3);
        scrollbar-width: thin;
    }

    .chat-container::-webkit-scrollbar {
        width: 6px;
    }

    .chat-container::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.05);
        border-radius: 10px;
    }

    .chat-container::-webkit-scrollbar-thumb {
        background: var(--primary-light);
        border-radius: 10px;
    }

    .chat-user {
        background: var(--gradient);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 1.2rem 1.2rem 0.25rem 1.2rem;
        margin: 0.6rem 0;
        display: inline-block;
        max-width: 80%;
        box-shadow: 0 3px 10px rgba(67, 97, 238, 0.2);
        font-weight: 500;
        line-height: 1.5;
    }

    .chat-bot {
        background: var(--background-color);
        color: var(--text-color);
        padding: 0.8rem 1.2rem;
        border-radius: 1.2rem 1.2rem 1.2rem 0.25rem;
        margin: 0.6rem 0;
        display: inline-block;
        max-width: 85%;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        line-height: 1.5;
    }

    /* Input field for chat */
    .chat-input {
        display: flex;
        margin-top: 1rem;
    }

    .chat-input input {
        flex-grow: 1;
        padding: 0.8rem 1rem;
        border: 1px solid #eaeaea;
        border-radius: 2rem;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }

    .chat-input input:focus {
        outline: none;
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(67, 97, 238, 0.2);
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
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# Helper functions
def add_logo():
    """Add a modern logo to the sidebar"""
    st.sidebar.markdown(
        """
        <div style="text-align: center; padding: 1.6rem 0; background: linear-gradient(135deg, #4361ee, #4cc9f0); border-radius: 1rem; margin-bottom: 1.5rem; box-shadow: 0 8px 20px rgba(67, 97, 238, 0.2);">
            <h2 style="color: white; margin: 0; font-weight: 700; letter-spacing: 1px;">
                <span style="margin-right: 12px;">📊</span> ProductPulse
            </h2>
            <p style="font-size: 1rem; color: rgba(255, 255, 255, 0.9); margin-top: 0.5rem; font-weight: 500;">
                Advanced Analytics Dashboard
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

# Enhanced function to display instructions
def display_how_to_use():
    """Display professional how-to-use instructions with step-by-step guidance"""
    st.markdown("## How to Use ProductPulse Analytics")
    
    # Create a container for the how-to section
    with st.container():
        # Add a pro badge
        st.markdown("<div style='text-align: right;'><span style='background: linear-gradient(45deg, #ff6b6b, #ff8e53); color: white; padding: 0.2rem 0.6rem; border-radius: 30px; font-size: 0.8rem; font-weight: 600; box-shadow: 0 2px 8px rgba(255, 107, 107, 0.4);'>PRO</span></div>", unsafe_allow_html=True)
        
        # Step 1
        col1, col2 = st.columns([1, 9])
        with col1:
            st.markdown("<div style='background: var(--gradient); color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.9rem;'>1</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("#### Upload Your Data")
            st.markdown("Import CSV files containing your product analytics data or use our sample datasets to get started quickly.")
        
        # Step 2
        col1, col2 = st.columns([1, 9])
        with col1:
            st.markdown("<div style='background: var(--gradient); color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.9rem;'>2</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("#### Explore Interactive Dashboard")
            st.markdown("Visualize key metrics and dimensions with customizable charts and gain immediate insights from your data.")
        
        # Step 3
        col1, col2 = st.columns([1, 9])
        with col1:
            st.markdown("<div style='background: var(--gradient); color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.9rem;'>3</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("#### Analyze Trends Over Time")
            st.markdown("Identify patterns, seasonality, and anomalies in your product metrics to understand user behavior changes.")
        
        # Step 4
        col1, col2 = st.columns([1, 9])
        with col1:
            st.markdown("<div style='background: var(--gradient); color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.9rem;'>4</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("#### Segment Your Users")
            st.markdown("Compare different user groups to discover which segments perform best and where opportunities exist.")
        
        # Step 5
        col1, col2 = st.columns([1, 9])
        with col1:
            st.markdown("<div style='background: var(--gradient); color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.9rem;'>5</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("#### Ask Questions in Natural Language")
            st.markdown("Use our AI-powered chat interface to analyze your data through simple conversational queries.")
        
        # Pro Tip
        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([1, 9])
            with col1:
                st.markdown("<div style='background: linear-gradient(45deg, #ff6b6b, #ff8e53); color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.9rem;'>✨</div>", unsafe_allow_html=True)
            with col2:
                st.markdown("#### Pro Tip")
                st.markdown("Save your analyses to quickly access insights in the future. Share dashboards with your team for collaborative decision-making.")

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
    <div style="padding: 1rem 0 0.5rem 0;">
        <h1 class="main-header">Product Analytics Dashboard</h1>
        <p class="sub-header">Discover insights, track metrics, and make data-driven decisions</p>
    </div>
    """, 
    unsafe_allow_html=True
)

# Main content based on whether data is loaded with improved styling
if st.session_state.data is not None:
    data = st.session_state.data
    
    # Add status dashboard at the top using Streamlit components instead of raw HTML
    st.markdown("### Dashboard Status", unsafe_allow_html=True)
    
    # Create a container with background and styling
    with st.container():
        st.markdown("""
        <div style="background: white; border-radius: 1rem; padding: 1rem 0.5rem; 
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); margin-bottom: 1.5rem;">
        </div>
        """, unsafe_allow_html=True)
        
        # Create columns for each status item
        status_cols = st.columns([3, 2, 2, 3, 2])
        
        # Current Dataset
        with status_cols[0]:
            st.markdown(f"""
            <div style="font-size: 0.8rem; color: #6c757d; font-weight: 500;">Current Dataset</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: #2b2d42; padding-top: 5px;">
                {st.session_state.current_dataset_name or "Unnamed Dataset"}
            </div>
            """, unsafe_allow_html=True)
        
        # Status
        with status_cols[1]:
            st.markdown(f"""
            <div style="display: flex; align-items: center;">
                <div style="background-color: #10b981; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px;"></div>
                <div>
                    <div style="font-size: 0.8rem; color: #6c757d; font-weight: 500;">Status</div>
                    <div style="font-size: 0.9rem; font-weight: 600; color: #10b981; padding-top: 5px;">Ready for Analysis</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Data Points
        with status_cols[2]:
            st.markdown(f"""
            <div style="font-size: 0.8rem; color: #6c757d; font-weight: 500;">Data Points</div>
            <div style="font-size: 0.9rem; font-weight: 600; color: #2b2d42; padding-top: 5px;">{len(data)}</div>
            """, unsafe_allow_html=True)
        
        # AI Assistant Status
        with status_cols[3]:
            ai_status = "Active" if os.environ.get("GEMINI_API_KEY") else "Backup Mode"
            status_color = "#10b981" if os.environ.get("GEMINI_API_KEY") else "#f43f5e"
            st.markdown(f"""
            <div style="font-size: 0.8rem; color: #6c757d; font-weight: 500;">AI Assistant Status</div>
            <div style="font-size: 0.9rem; font-weight: 600; color: {status_color}; padding-top: 5px;">{ai_status}</div>
            """, unsafe_allow_html=True)
        
        # Last Updated
        with status_cols[4]:
            st.markdown(f"""
            <div style="font-size: 0.8rem; color: #6c757d; font-weight: 500;">Last Updated</div>
            <div style="font-size: 0.9rem; font-weight: 600; color: #2b2d42; padding-top: 5px;">{datetime.now().strftime("%H:%M")}</div>
            """, unsafe_allow_html=True)
    
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
        
        # Display the chat interface
        with st.container():
            st.markdown("<h3 style='margin-bottom: 1rem;'>AI Data Assistant</h3>", unsafe_allow_html=True)
            
            # Add description
            st.markdown("""
            <p style="margin-bottom: 1.5rem; color: #6B7280;">
                Ask questions about your data in natural language and get AI-powered insights.
            </p>
            """, unsafe_allow_html=True)
            
            # Chat container with enhanced styling
            st.markdown("""
            <style>
            .chat-message {
                display: flex;
                margin-bottom: 1rem;
            }
            .chat-message-content {
                border-radius: 1rem;
                padding: 0.75rem 1rem;
                max-width: 80%;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            }
            .user-message {
                justify-content: flex-end;
            }
            .user-message .chat-message-content {
                background-color: #E0F2FE;
                border-radius: 1rem 1rem 0.25rem 1rem;
            }
            .bot-message {
                justify-content: flex-start;
            }
            .bot-message .chat-message-content {
                background-color: #F0F9FF;
                border-radius: 1rem 1rem 1rem 0.25rem;
            }
            .avatar {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 0.5rem;
                flex-shrink: 0;
            }
            .bot-avatar {
                background: linear-gradient(135deg, #4361ee, #4cc9f0);
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            .thinking {
                display: flex;
                align-items: center;
                margin-bottom: 1rem;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Chat container
            chat_container = st.container()
            with chat_container:
                # Display chat history
                for i, chat in enumerate(st.session_state.chat_history):
                    # Make sure chat is a dict and has the expected structure
                    if isinstance(chat, dict):
                        # User messages
                        if chat.get("role") == "user":
                            st.markdown(f"""
                            <div class="chat-message user-message">
                                <div class="chat-message-content">
                                    <div style="font-weight: 500;">{chat.get("content", "")}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        # AI messages
                        elif chat.get("role") == "assistant":
                            st.markdown(f"""
                            <div class="chat-message bot-message">
                                <div class="avatar bot-avatar">AI</div>
                                <div class="chat-message-content">
                                    <div style="font-weight: 400;">{chat.get("content", "")}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    # Handle legacy format (plain strings)
                    elif isinstance(chat, str):
                        st.markdown(f"""
                        <div class="chat-message bot-message">
                            <div class="avatar bot-avatar">AI</div>
                            <div class="chat-message-content">
                                <div style="font-weight: 400;">{chat}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Suggestion chips with improved styling
            st.markdown("""
            <style>
            .suggestion-chip-container {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin-bottom: 1rem;
            }
            .suggestion-chip {
                background-color: #EFF6FF;
                border: 1px solid #DBEAFE;
                color: #1E40AF;
                padding: 0.5rem 0.75rem;
                border-radius: 1rem;
                font-size: 0.875rem;
                cursor: pointer;
                transition: background-color 0.2s, transform 0.1s;
                white-space: nowrap;
            }
            .suggestion-chip:hover {
                background-color: #DBEAFE;
                transform: translateY(-1px);
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            </style>
            
            <div class="suggestion-chip-container">
                <div class="suggestion-chip" onclick="document.querySelector('[data-testid=\\'stText-input-chat_input\\'] input').value='Summarize key metrics'; document.querySelector('form[data-testid=\\'stForm\\'] button').click();">
                    Summarize key metrics
                </div>
                <div class="suggestion-chip" onclick="document.querySelector('[data-testid=\\'stText-input-chat_input\\'] input').value='Identify patterns in the data'; document.querySelector('form[data-testid=\\'stForm\\'] button').click();">
                    Identify patterns
                </div>
                <div class="suggestion-chip" onclick="document.querySelector('[data-testid=\\'stText-input-chat_input\\'] input').value='Suggest improvements based on the data'; document.querySelector('form[data-testid=\\'stForm\\'] button').click();">
                    Suggest improvements
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Chat input form with better styling
            st.markdown("""
            <style>
            .chat-input-container [data-testid="stForm"] {
                background-color: white;
                border-radius: 1rem;
                padding: 0.5rem;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .chat-input-container input {
                border: none !important;
                padding: 0.75rem 1rem !important;
                font-size: 1rem !important;
            }
            .chat-input-container input:focus {
                box-shadow: none !important;
                border: none !important;
            }
            .chat-input-container [data-testid="baseButton-primary"] {
                height: 100%;
                border-radius: 0.75rem;
            }
            </style>
            <div class="chat-input-container">
            """, unsafe_allow_html=True)
            
            # Chat input
            with st.form("chat_form", clear_on_submit=True):
                col1, col2 = st.columns([6, 1])
                
                with col1:
                    user_input = st.text_input(
                        "Ask about your data",
                        label_visibility="collapsed",
                        placeholder="Type your question here...",
                        key="chat_input"
                    )
                
                # Submit button with proper styling
                with col2:
                    submit_button = st.form_submit_button(
                        "Send",
                        type="primary",
                        use_container_width=True
                    )
                    
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Show a "thinking" indicator when processing a query
            if st.session_state.get("thinking", False):
                st.markdown("""
                <style>
                @keyframes pulse {
                    0% { opacity: 0.4; }
                    50% { opacity: 0.8; }
                    100% { opacity: 0.4; }
                }
                .thinking-dots {
                    display: flex;
                    align-items: center;
                    margin-left: 0.5rem;
                }
                .dot {
                    background-color: #CBD5E1;
                    border-radius: 50%;
                    width: 8px;
                    height: 8px;
                    margin-right: 4px;
                    animation: pulse 1.5s infinite;
                }
                .dot:nth-child(2) {
                    animation-delay: 0.2s;
                }
                .dot:nth-child(3) {
                    animation-delay: 0.4s;
                }
                </style>
                
                <div class="thinking">
                    <div class="avatar bot-avatar">AI</div>
                    <div style="background-color: #F0F9FF; padding: 0.75rem; border-radius: 1rem 1rem 1rem 0.25rem; max-width: 80%; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                        <div class="thinking-dots">
                            <div class="dot"></div>
                            <div class="dot"></div>
                            <div class="dot"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Process the user input
            if submit_button and user_input:
                # Set thinking state
                st.session_state.thinking = True
                st.rerun()

            # If we're thinking and not just after hitting submit, process the query
            if st.session_state.get("thinking", False) and not (submit_button and user_input):
                # Add user message to chat history
                st.session_state.last_query = st.session_state.get("last_query", user_input)
                st.session_state.chat_history.append({"role": "user", "content": st.session_state.last_query})
                
                try:
                    # Process the query
                    response = process_query(st.session_state.last_query, st.session_state.data)
                    
                    # Add AI response to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_message = f"Error processing query: {str(e)}"
                    st.session_state.chat_history.append({"role": "assistant", "content": error_message})
                
                # Reset thinking state
                st.session_state.thinking = False
                st.rerun()
    
    with tab6:
        # Saved Analyses Section
        st.header("Saved Analyses")
        
        # Display saved analyses
        try:
            saved_analyses = get_saved_analyses()
            
            if not saved_analyses.empty:
                # Format the analysis list
                for _, row in saved_analyses.iterrows():
                    st.markdown(f"""
                    <div style="margin-bottom: 0.5rem; padding: 0.5rem; background-color: #F8F9FA; border-radius: 0.3rem;">
                        <strong>{row['name']}</strong><br>
                        <small>{row['description']}</small><br>
                        <small>Last modified: {row['last_modified'].strftime('%Y-%m-%d')}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button(f"📂 Load", key=f"load_{row['id']}"):
                            if load_saved_analysis(row['id']):
                                st.success(f"Analysis '{row['name']}' loaded successfully!")
                    with col2:
                        if st.button(f"🗑️ Delete", key=f"delete_{row['id']}"):
                            if delete_analysis(row['id']):
                                st.success(f"Analysis '{row['name']}' deleted.")
                                st.rerun()
            else:
                st.info("No saved analyses found. Create a new analysis and save it first.")
                
        except Exception as e:
            st.error(f"Error loading saved analyses: {e}")

    # Close the dashboard container
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Charts and visualization section
    st.markdown("""
    <div style="margin-top: 2rem; margin-bottom: 1rem;">
        <h2 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 0.5rem;">Interactive Visualizations</h2>
        <p style="color: #6B7280; margin-bottom: 1rem;">Explore your data through interactive charts and graphs</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different visualization types
    chart_tabs = st.tabs(["Time Series", "Distribution", "Correlation", "Segmentation"])

    # Time Series Tab
    with chart_tabs[0]:
        st.subheader("Time Series Analysis")
        
        if 'data' in st.session_state and not st.session_state.data.empty:
            # Column selection
            col1, col2 = st.columns([1, 1])
            with col1:
                date_column = st.selectbox(
                    "Select Date Column",
                    options=st.session_state.data.select_dtypes(include=['datetime64']).columns.tolist(),
                    index=0 if len(st.session_state.data.select_dtypes(include=['datetime64']).columns) > 0 else None,
                    key="time_series_date_col"
                )
            
            with col2:
                value_column = st.selectbox(
                    "Select Value Column",
                    options=st.session_state.data.select_dtypes(include=['number']).columns.tolist(),
                    index=0 if len(st.session_state.data.select_dtypes(include=['number']).columns) > 0 else None,
                    key="time_series_value_col"
                )
                
            if date_column and value_column:
                # Create the time series chart
                chart_data = st.session_state.data[[date_column, value_column]].copy()
                chart_data = chart_data.sort_values(by=date_column)
                
                fig = px.line(
                    chart_data, 
                    x=date_column, 
                    y=value_column,
                    title=f"{value_column} over Time",
                    labels={date_column: "Date", value_column: value_column},
                )
                
                fig.update_layout(
                    height=500,
                    xaxis_title="Date",
                    yaxis_title=value_column,
                    margin=dict(l=40, r=40, t=40, b=40),
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show rolling average option
                show_rolling_avg = st.checkbox("Show Rolling Average", key="show_rolling_avg")
                if show_rolling_avg:
                    window_size = st.slider("Window Size", min_value=2, max_value=50, value=7, key="rolling_window")
                    
                    chart_data[f"{value_column}_rolling_avg"] = chart_data[value_column].rolling(window=window_size).mean()
                    
                    fig = px.line(
                        chart_data, 
                        x=date_column, 
                        y=[value_column, f"{value_column}_rolling_avg"],
                        title=f"{value_column} with {window_size}-Day Rolling Average",
                        labels={date_column: "Date", value_column: value_column, f"{value_column}_rolling_avg": f"{window_size}-Day Rolling Average"},
                    )
                    
                    fig.update_layout(
                        height=500,
                        xaxis_title="Date",
                        yaxis_title=value_column,
                        margin=dict(l=40, r=40, t=40, b=40),
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Please select both date and value columns to create a time series chart.")
        else:
            st.info("Please load data to create visualizations.")
    
    # Distribution Tab
    with chart_tabs[1]:
        st.subheader("Distribution Analysis")
        
        if 'data' in st.session_state and not st.session_state.data.empty:
            column = st.selectbox(
                "Select Column",
                options=st.session_state.data.select_dtypes(include=['number']).columns.tolist(),
                index=0 if len(st.session_state.data.select_dtypes(include=['number']).columns) > 0 else None,
                key="dist_column"
            )
            
            if column:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # Histogram
                    fig_hist = px.histogram(
                        st.session_state.data, 
                        x=column,
                        nbins=30,
                        title=f"Histogram of {column}",
                        opacity=0.8,
                    )
                    
                    fig_hist.update_layout(
                        height=400,
                        xaxis_title=column,
                        yaxis_title="Count",
                        margin=dict(l=40, r=40, t=40, b=40),
                    )
                    
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                with col2:
                    # Box plot
                    fig_box = px.box(
                        st.session_state.data, 
                        y=column,
                        title=f"Box Plot of {column}",
                    )
                    
                    fig_box.update_layout(
                        height=400,
                        yaxis_title=column,
                        margin=dict(l=40, r=40, t=40, b=40),
                    )
                    
                    st.plotly_chart(fig_box, use_container_width=True)
                
                # Statistics
                st.subheader("Descriptive Statistics")
                stats = st.session_state.data[column].describe()
                
                col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                col1.metric("Mean", f"{stats['mean']:.2f}")
                col2.metric("Median", f"{stats['50%']:.2f}")
                col3.metric("Std Dev", f"{stats['std']:.2f}")
                col4.metric("Range", f"{stats['max'] - stats['min']:.2f}")
            else:
                st.warning("Please select a numeric column for distribution analysis.")
        else:
            st.info("Please load data to create visualizations.")
    
    # Correlation Tab
    with chart_tabs[2]:
        st.subheader("Correlation Analysis")
        
        if 'data' in st.session_state and not st.session_state.data.empty:
            numeric_columns = st.session_state.data.select_dtypes(include=['number']).columns.tolist()
            
            if len(numeric_columns) > 1:
                # Multi-select for columns
                selected_columns = st.multiselect(
                    "Select Columns for Correlation Analysis",
                    options=numeric_columns,
                    default=numeric_columns[:min(5, len(numeric_columns))],
                    key="corr_columns"
                )
                
                if selected_columns and len(selected_columns) > 1:
                    # Correlation heatmap
                    corr_matrix = st.session_state.data[selected_columns].corr()
                    
                    fig = px.imshow(
                        corr_matrix,
                        text_auto=True,
                        aspect="auto",
                        color_continuous_scale='RdBu_r',
                        title="Correlation Matrix",
                    )
                    
                    fig.update_layout(
                        height=600,
                        margin=dict(l=40, r=40, t=40, b=40),
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Scatter matrix option
                    if st.checkbox("Show Scatter Matrix", key="show_scatter_matrix"):
                        fig = px.scatter_matrix(
                            st.session_state.data,
                            dimensions=selected_columns,
                            title="Scatter Matrix",
                            opacity=0.7,
                        )
                        
                        fig.update_layout(
                            height=700,
                            margin=dict(l=40, r=40, t=40, b=40),
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Please select at least two columns for correlation analysis.")
            else:
                st.warning("Not enough numeric columns for correlation analysis. Need at least 2 numeric columns.")
        else:
            st.info("Please load data to create visualizations.")
    
    # Segmentation Tab
    with chart_tabs[3]:
        st.subheader("Data Segmentation")
        
        if 'data' in st.session_state and not st.session_state.data.empty:
            # Column selection for segmentation
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                x_column = st.selectbox(
                    "X-Axis",
                    options=st.session_state.data.select_dtypes(include=['number']).columns.tolist(),
                    index=0 if len(st.session_state.data.select_dtypes(include=['number']).columns) > 0 else None,
                    key="seg_x_column"
                )
            
            with col2:
                y_column = st.selectbox(
                    "Y-Axis",
                    options=st.session_state.data.select_dtypes(include=['number']).columns.tolist(),
                    index=min(1, len(st.session_state.data.select_dtypes(include=['number']).columns) - 1) if len(st.session_state.data.select_dtypes(include=['number']).columns) > 1 else None,
                    key="seg_y_column"
                )
            
            with col3:
                category_cols = [None] + st.session_state.data.select_dtypes(include=['object', 'category']).columns.tolist()
                color_column = st.selectbox(
                    "Color By (Optional)",
                    options=category_cols,
                    index=0,
                    key="seg_color_column"
                )
            
            if x_column and y_column:
                # Create the scatter plot
                fig = px.scatter(
                    st.session_state.data,
                    x=x_column,
                    y=y_column,
                    color=color_column if color_column else None,
                    title=f"{y_column} vs {x_column}",
                    opacity=0.7,
                    size_max=10,
                )
                
                fig.update_layout(
                    height=600,
                    xaxis_title=x_column,
                    yaxis_title=y_column,
                    margin=dict(l=40, r=40, t=40, b=40),
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # K-means clustering option
                if st.checkbox("Apply K-means Clustering", key="apply_kmeans"):
                    n_clusters = st.slider("Number of Clusters", min_value=2, max_value=10, value=3, key="n_clusters")
                    
                    # Prepare data for clustering
                    features = st.session_state.data[[x_column, y_column]].dropna()
                    
                    if not features.empty and len(features) > n_clusters:
                        # Apply K-means
                        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                        features['cluster'] = kmeans.fit_predict(features[[x_column, y_column]])
                        
                        # Create the clustered scatter plot
                        fig = px.scatter(
                            features,
                            x=x_column,
                            y=y_column,
                            color='cluster',
                            title=f"K-means Clustering ({n_clusters} clusters)",
                            color_continuous_scale='viridis',
                            opacity=0.7,
                        )
                        
                        # Add cluster centers
                        centers = kmeans.cluster_centers_
                        fig.add_scatter(
                            x=centers[:, 0], 
                            y=centers[:, 1],
                            mode='markers',
                            marker=dict(color='red', size=15, symbol='x'),
                            name='Cluster Centers'
                        )
                        
                        fig.update_layout(
                            height=600,
                            xaxis_title=x_column,
                            yaxis_title=y_column,
                            margin=dict(l=40, r=40, t=40, b=40),
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display cluster information
                        st.subheader("Cluster Information")
                        cluster_info = features.groupby('cluster').mean()
                        
                        st.dataframe(cluster_info)
                    else:
                        st.warning("Not enough data points for clustering with the selected features.")
            else:
                st.warning("Please select both X and Y columns for segmentation analysis.")
        else:
            st.info("Please load data to create visualizations.")

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
    
    # Instructions are now displayed in the main app flow below, so we don't need this duplicate call
    # display_how_to_use()

# Add enhanced main UI layout for a more professional look
if __name__ == "__main__":
    # Initialize session state variables already done at the beginning
    # No need to reinitialize here
    
    # Add the logo to sidebar
    add_logo()
    
    # Main app header with status indicator
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<h1 class="main-header">ProductPulse Analytics</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Advanced data insights for product managers</p>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: right; margin-top: 1rem;">
            <span class="status-indicator status-active"></span> <span style="font-size: 0.9rem; color: #10b981; font-weight: 500;">System Online</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Add custom CSS for improved tab styling with dropdown-like appearance
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 3px;
        background: rgba(248, 249, 250, 0.7);
        padding: 0.75rem;
        border-radius: 0.75rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        background: white;
        border-radius: 0.5rem;
        color: var(--text-color);
        font-weight: 500;
        transition: all 0.3s ease;
        padding: 0 1.5rem;
        border: 1px solid rgba(0,0,0,0.05);
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--gradient);
        color: white;
        font-weight: 600;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(67, 97, 238, 0.15);
    }
    </style>
    """, unsafe_allow_html=True)
        
    # Display how-to section first if no data is loaded yet
    if st.session_state.data is None:
        display_how_to_use()

    # Main navigation tabs with enhanced styling
    tabs = st.tabs([
        "📊 Dashboard", 
        "📈 Trend Analysis", 
        "🔍 Segmentation", 
        "🤖 AI Data Assistant",
        "⚙️ Settings"
    ])
    
    # Dashboard tab
    with tabs[0]:
        # Use existing code but with enhanced styling
        st.markdown("### Interactive Dashboard")
        
        if st.session_state.data is not None:
            # Create metrics row
            st.markdown('<div class="sub-header">Key Metrics</div>', unsafe_allow_html=True)
            
            metric_cols = st.columns(4)
            # Display key metrics in a row
            if len(st.session_state.metrics) > 0:
                for i, metric in enumerate(st.session_state.metrics[:4]):
                    with metric_cols[i % 4]:
                        metric_value = st.session_state.data[metric].mean()
                        metric_delta = st.session_state.data[metric].std() / metric_value * 100 if metric_value != 0 else 0
                        
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">{metric}</div>
                            <div class="metric-value">{format_number(metric_value)}</div>
                            <div class="metric-label">Average {metric}</div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("Please upload data or use a sample dataset to get started.")

    # Trend Analysis tab
    with tabs[1]:
        st.markdown("### Trend Analysis")
        
        if st.session_state.data is not None and len(st.session_state.time_columns) > 0:
            # Allow user to select time column and metric for trend analysis
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                time_col = st.selectbox("Select Time Column", st.session_state.time_columns)
            
            with col2:
                trend_metric = st.selectbox("Select Metric", st.session_state.metrics)
            
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                analyze_btn = st.button("Analyze Trends")
            
            if analyze_btn or st.session_state.refresh_insights:
                with st.spinner("Analyzing trends..."):
                    # Display trend chart
                    st.markdown('<div class="plot-container">', unsafe_allow_html=True)
                    trend_options = ["Moving Average", "Trend Line", "Seasonality", "Outliers"]
                    trend_data, trend_insights = perform_trend_analysis(
                        st.session_state.data, time_col, trend_metric, trend_options
                    )
                    
                    fig = create_trend_plot(trend_data, time_col, trend_metric, trend_options)
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Display insights
                    st.markdown("#### Insights")
                    for insight in trend_insights:
                        st.markdown(f"""
                        <div class="insight-card">
                            {insight}
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("Please upload data with time columns to analyze trends.")

    # Segmentation tab
    with tabs[2]:
        st.markdown("### Data Segmentation")
        
        if st.session_state.data is not None and len(st.session_state.dimensions) > 0:
            # Allow user to select dimension and metric for segmentation
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                segment_by = st.selectbox("Segment By", st.session_state.dimensions)
            
            with col2:
                segment_metric = st.selectbox("Analyze Metric", st.session_state.metrics)
            
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                segment_btn = st.button("Generate Segments")
            
            if segment_btn or st.session_state.refresh_insights:
                with st.spinner("Generating segments..."):
                    # Perform segmentation
                    segment_options = ["Compare to Average", "Detect Outliers"]
                    segmented_data, segment_insights = segment_data(
                        st.session_state.data, segment_by, segment_metric, segment_options
                    )
                    
                    # Display segment chart
                    st.markdown('<div class="plot-container">', unsafe_allow_html=True)
                    fig = px.bar(
                        segmented_data.groupby(segment_by)[segment_metric].mean().reset_index().sort_values(segment_metric, ascending=False),
                        x=segment_by,
                        y=segment_metric,
                        title=f"{segment_metric} by {segment_by}",
                        color=segment_metric,
                        color_continuous_scale="blues"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Display insights
                    st.markdown("#### Insights")
                    for insight in segment_insights:
                        st.markdown(f"""
                        <div class="insight-card">
                            {insight}
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("Please upload data with categorical columns to perform segmentation.")

    # AI Data Assistant tab (renamed from Chat with Data)
    with tabs[3]:
        st.markdown("### AI Data Assistant")
        
        st.markdown("""
        <p style="margin-bottom: 1.5rem;">
            Ask questions about your data in natural language and get AI-powered insights.
        </p>
        """, unsafe_allow_html=True)
        
        if st.session_state.data is not None:
            # Display the chat interface
            with st.container():
                # Chat container with enhanced styling
                st.markdown("""
                <style>
                .chat-message {
                    display: flex;
                    margin-bottom: 1rem;
                }
                .chat-message-content {
                    border-radius: 1rem;
                    padding: 0.75rem 1rem;
                    max-width: 80%;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                }
                .user-message {
                    justify-content: flex-end;
                }
                .user-message .chat-message-content {
                    background-color: #E0F2FE;
                    border-radius: 1rem 1rem 0.25rem 1rem;
                }
                .bot-message {
                    justify-content: flex-start;
                }
                .bot-message .chat-message-content {
                    background-color: #F0F9FF;
                    border-radius: 1rem 1rem 1rem 0.25rem;
                }
                .avatar {
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-right: 0.5rem;
                    flex-shrink: 0;
                }
                .bot-avatar {
                    background: linear-gradient(135deg, #4361ee, #4cc9f0);
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                }
                .thinking {
                    display: flex;
                    align-items: center;
                    margin-bottom: 1rem;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Chat container
                chat_container = st.container()
                with chat_container:
                    # Display chat history
                    for i, chat in enumerate(st.session_state.chat_history):
                        # Make sure chat is a dict and has the expected structure
                        if isinstance(chat, dict):
                            # User messages
                            if chat.get("role") == "user":
                                st.markdown(f"""
                                <div class="chat-message user-message">
                                    <div class="chat-message-content">
                                        <div style="font-weight: 500;">{chat.get("content", "")}</div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            # AI messages
                            elif chat.get("role") == "assistant":
                                st.markdown(f"""
                                <div class="chat-message bot-message">
                                    <div class="avatar bot-avatar">AI</div>
                                    <div class="chat-message-content">
                                        <div style="font-weight: 400;">{chat.get("content", "")}</div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        # Handle legacy format (plain strings)
                        elif isinstance(chat, str):
                            st.markdown(f"""
                            <div class="chat-message bot-message">
                                <div class="avatar bot-avatar">AI</div>
                                <div class="chat-message-content">
                                    <div style="font-weight: 400;">{chat}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Suggestion chips with improved styling
                st.markdown("""
                <style>
                .suggestion-chip-container {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.5rem;
                    margin-bottom: 1rem;
                }
                .suggestion-chip {
                    background-color: #EFF6FF;
                    border: 1px solid #DBEAFE;
                    color: #1E40AF;
                    padding: 0.5rem 0.75rem;
                    border-radius: 1rem;
                    font-size: 0.875rem;
                    cursor: pointer;
                    transition: background-color 0.2s, transform 0.1s;
                    white-space: nowrap;
                }
                .suggestion-chip:hover {
                    background-color: #DBEAFE;
                    transform: translateY(-1px);
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                </style>
                
                <div class="suggestion-chip-container">
                    <div class="suggestion-chip" onclick="document.querySelector('[data-testid=\\'stText-input-chat_input\\'] input').value='Summarize key metrics'; document.querySelector('form[data-testid=\\'stForm\\'] button').click();">
                        Summarize key metrics
                    </div>
                    <div class="suggestion-chip" onclick="document.querySelector('[data-testid=\\'stText-input-chat_input\\'] input').value='Identify patterns in the data'; document.querySelector('form[data-testid=\\'stForm\\'] button').click();">
                        Identify patterns
                    </div>
                    <div class="suggestion-chip" onclick="document.querySelector('[data-testid=\\'stText-input-chat_input\\'] input').value='Suggest improvements based on the data'; document.querySelector('form[data-testid=\\'stForm\\'] button').click();">
                        Suggest improvements
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Chat input form with better styling
                st.markdown("""
                <style>
                .chat-input-container [data-testid="stForm"] {
                    background-color: white;
                    border-radius: 1rem;
                    padding: 0.5rem;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                .chat-input-container input {
                    border: none !important;
                    padding: 0.75rem 1rem !important;
                    font-size: 1rem !important;
                }
                .chat-input-container input:focus {
                    box-shadow: none !important;
                    border: none !important;
                }
                .chat-input-container [data-testid="baseButton-primary"] {
                    height: 100%;
                    border-radius: 0.75rem;
                }
                </style>
                <div class="chat-input-container">
                """, unsafe_allow_html=True)
                
                # Chat input
                with st.form("chat_form", clear_on_submit=True):
                    col1, col2 = st.columns([6, 1])
                    
                    with col1:
                        user_input = st.text_input(
                            "Ask about your data",
                            label_visibility="collapsed",
                            placeholder="Type your question here...",
                            key="chat_input"
                        )
                    
                    # Submit button with proper styling
                    with col2:
                        submit_button = st.form_submit_button(
                            "Send",
                            type="primary",
                            use_container_width=True
                        )
                        
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Show a "thinking" indicator when processing a query
                if st.session_state.get("thinking", False):
                    st.markdown("""
                    <style>
                    @keyframes pulse {
                        0% { opacity: 0.4; }
                        50% { opacity: 0.8; }
                        100% { opacity: 0.4; }
                    }
                    .thinking-dots {
                        display: flex;
                        align-items: center;
                        margin-left: 0.5rem;
                    }
                    .dot {
                        background-color: #CBD5E1;
                        border-radius: 50%;
                        width: 8px;
                        height: 8px;
                        margin-right: 4px;
                        animation: pulse 1.5s infinite;
                    }
                    .dot:nth-child(2) {
                        animation-delay: 0.2s;
                    }
                    .dot:nth-child(3) {
                        animation-delay: 0.4s;
                    }
                    </style>
                    
                    <div class="thinking">
                        <div class="avatar bot-avatar">AI</div>
                        <div style="background-color: #F0F9FF; padding: 0.75rem; border-radius: 1rem 1rem 1rem 0.25rem; max-width: 80%; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                            <div class="thinking-dots">
                                <div class="dot"></div>
                                <div class="dot"></div>
                                <div class="dot"></div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Process the user input
                if submit_button and user_input:
                    # Set thinking state
                    st.session_state.thinking = True
                    st.rerun()

                # If we're thinking and not just after hitting submit, process the query
                if st.session_state.get("thinking", False) and not (submit_button and user_input):
                    # Add user message to chat history
                    st.session_state.last_query = st.session_state.get("last_query", user_input)
                    st.session_state.chat_history.append({"role": "user", "content": st.session_state.last_query})
                    
                    try:
                        # Process the query
                        response = process_query(st.session_state.last_query, st.session_state.data)
                        
                        # Add AI response to chat history
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                        
                    except Exception as e:
                        error_message = f"Error processing query: {str(e)}"
                        st.session_state.chat_history.append({"role": "assistant", "content": error_message})
                    
                    # Reset thinking state
                    st.session_state.thinking = False
                    st.rerun()
        else:
            st.info("Please upload data to chat with it.")

    # Settings tab
    with tabs[4]:
        st.markdown("### Settings")
        
        # API Key Setting
        st.markdown("#### AI Integration Settings")
        with st.expander("Gemini API Configuration", expanded=True):
            current_key = os.environ.get("GEMINI_API_KEY", "")
            masked_key = "•" * len(current_key) if current_key else "Not set"
            
            st.markdown(f"""
            <div style="margin-bottom: 1rem; padding: 1rem; border-radius: 0.5rem; background: {'#D1FAE5' if current_key else '#FEE2E2'}; display: flex; align-items: center;">
                <div style="margin-right: 1rem; width: 24px; height: 24px; border-radius: 50%; background: {'#10B981' if current_key else '#EF4444'}; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                    {'✓' if current_key else '×'}
                </div>
                <div>
                    <strong>API Status:</strong> {' Active' if current_key else ' Not Configured'}
                    <br/>
                    <small style="opacity: 0.8;">{'Using AI-powered advanced analytics' if current_key else 'Using basic rule-based analytics'}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("Enter your Gemini API key to enable advanced AI analytics. You can get a free API key from [Google AI Studio](https://ai.google.dev/).")
            
            api_key = st.text_input("Gemini API Key", type="password", 
                                    placeholder="Enter your API key here", 
                                    help="Your key will be stored for this session only")
            
            if st.button("Save API Key", type="primary") and api_key:
                with st.spinner("Configuring API..."):
                    os.environ["GEMINI_API_KEY"] = api_key
                    try:
                        # Use requests to test the API key
                        import requests
                        test_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                        response = requests.get(test_url)
                        
                        if response.status_code == 200:
                            st.session_state.gemini_configured = True
                            # Set flag to reload API config in the chatbot module
                            success = reload_api_config()
                            st.success("✅ API Key saved successfully! AI features are now enabled.")
                            # Display sample models available
                            models = response.json().get("models", [])
                            if models:
                                model_names = [model.get("name", "").split("/")[-1] for model in models[:3]]
                                st.markdown(f"**Available models**: {', '.join(model_names)}...")
                        else:
                            st.error(f"❌ Invalid API key or API error: {response.status_code}")
                    except Exception as e:
                        st.error(f"Error configuring API: {e}")
                st.rerun()
        
        # Theme settings
        st.markdown("#### Theme Settings")
        theme_cols = st.columns(2)
        
        with theme_cols[0]:
            primary_color = st.color_picker("Primary Color", "#4361ee")
        
        with theme_cols[1]:
            accent_color = st.color_picker("Accent Color", "#4cc9f0")
        
        if st.button("Apply Theme", type="primary"):
            # Apply custom CSS with selected colors
            st.markdown(f"""
            <style>
            :root {{
                --primary-color: {primary_color};
                --accent-color: {accent_color};
                --gradient: linear-gradient(120deg, {primary_color}, {accent_color});
            }}
            </style>
            """, unsafe_allow_html=True)
            st.success("Theme applied successfully!")
            
        # Advanced Settings
        with st.expander("Advanced Settings"):
            st.checkbox("Enable experimental features", value=False, 
                        help="Enable experimental features that are still in development")
            st.checkbox("High-performance mode", value=True,
                        help="Optimizes rendering for better performance on large datasets")
            st.select_slider("Cache size", options=["Small", "Medium", "Large"], value="Medium",
                            help="Controls how much data is cached locally")
            
            if st.button("Clear All Cache"):
                for key in list(st.session_state.keys()):
                    if key not in ['page', 'gemini_configured']:
                        st.session_state.pop(key, None)
                st.success("Cache cleared successfully!")
                st.rerun()
