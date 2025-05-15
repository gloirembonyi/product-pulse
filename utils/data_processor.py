import pandas as pd
import numpy as np

def clean_data(df):
    """
    Clean and prepare the dataset
    
    Args:
        df (pandas.DataFrame): The input dataframe
    
    Returns:
        pandas.DataFrame: Cleaned dataframe
    """
    # Make a copy to avoid modifying the original
    cleaned_df = df.copy()
    
    # Drop duplicates
    cleaned_df = cleaned_df.drop_duplicates()
    
    # Convert date columns to datetime
    for col in cleaned_df.columns:
        # Check if the column name suggests it's a date
        if any(date_hint in col.lower() for date_hint in ['date', 'time', 'day', 'month', 'year']):
            try:
                cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce')
            except:
                pass
    
    # Handle missing values
    for col in cleaned_df.columns:
        # If numeric column with < 10% missing, fill with median
        if pd.api.types.is_numeric_dtype(cleaned_df[col]) and cleaned_df[col].isna().mean() < 0.1:
            cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].median())
        # If categorical with < 10% missing, fill with mode
        elif pd.api.types.is_object_dtype(cleaned_df[col]) and cleaned_df[col].isna().mean() < 0.1:
            cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].mode()[0] if not cleaned_df[col].mode().empty else "Unknown")
    
    return cleaned_df

def detect_data_type(df):
    """
    Detect column types and categorize them
    
    Args:
        df (pandas.DataFrame): The input dataframe
    
    Returns:
        tuple: (data_types_dict, metrics, dimensions, time_columns)
    """
    data_types = {}
    metrics = []
    dimensions = []
    time_columns = []
    
    for col in df.columns:
        # Check if it's a datetime column
        if pd.api.types.is_datetime64_dtype(df[col]):
            data_types[col] = 'datetime'
            time_columns.append(col)
        # Check if it's numeric
        elif pd.api.types.is_numeric_dtype(df[col]):
            # If low cardinality (few unique values), treat as dimension
            if df[col].nunique() < 10 or (df[col].nunique() / len(df) < 0.05):
                data_types[col] = 'dimension'
                dimensions.append(col)
            else:
                data_types[col] = 'metric'
                metrics.append(col)
        # Otherwise treat as dimension (categorical)
        else:
            data_types[col] = 'dimension'
            dimensions.append(col)
    
    return data_types, metrics, dimensions, time_columns

def prepare_sample_data():
    """
    Create a sample product analytics dataset
    
    Returns:
        tuple: (dataframe, data_types, metrics, dimensions, time_columns)
    """
    # Set seed for reproducibility
    np.random.seed(42)
    
    # Create date range for the last 90 days
    dates = pd.date_range(end=pd.Timestamp.now(), periods=90, freq='D')
    
    # Create common product analytics metrics
    n_rows = 1000
    
    data = {
        'date': np.random.choice(dates, n_rows),
        'user_id': np.random.randint(1, 201, n_rows),
        'session_id': [f"s-{i}" for i in np.random.randint(1, 5001, n_rows)],
        'device_type': np.random.choice(['desktop', 'mobile', 'tablet'], n_rows, p=[0.6, 0.3, 0.1]),
        'country': np.random.choice(['US', 'UK', 'CA', 'DE', 'FR', 'JP', 'AU', 'BR', 'IN'], n_rows),
        'acquisition_channel': np.random.choice(['organic', 'paid_search', 'social', 'email', 'referral'], n_rows),
        'session_duration': np.random.gamma(2, 180, n_rows),  # in seconds
        'pages_viewed': np.random.poisson(4, n_rows),
        'features_used': np.random.poisson(2, n_rows),
        'conversion': np.random.choice([0, 1], n_rows, p=[0.85, 0.15]),
        'purchase_value': np.random.exponential(50, n_rows) * np.random.choice([0, 1], n_rows, p=[0.85, 0.15]),
        'satisfaction_score': np.random.choice([1, 2, 3, 4, 5], n_rows, p=[0.05, 0.1, 0.2, 0.4, 0.25]),
        'user_type': np.random.choice(['new', 'returning'], n_rows, p=[0.3, 0.7]),
    }
    
    # Create the DataFrame
    df = pd.DataFrame(data)
    
    # Add some time trends
    trend_factor = np.linspace(0.8, 1.2, 90)  # increasing trend over time
    date_indices = pd.Series(df['date']).dt.dayofyear - pd.Series(df['date']).dt.dayofyear.min()
    
    # Apply trends to metrics
    df['session_duration'] = df['session_duration'] * trend_factor[date_indices.values]
    df['purchase_value'] = df['purchase_value'] * trend_factor[date_indices.values]
    
    # Weekly seasonality for sessions
    day_of_week = pd.Series(df['date']).dt.dayofweek
    weekday_factor = np.ones(n_rows)
    weekday_factor[day_of_week == 5] = 0.7  # Saturday
    weekday_factor[day_of_week == 6] = 0.6  # Sunday
    df['session_duration'] = df['session_duration'] * weekday_factor
    
    # Fix data types
    df['date'] = pd.to_datetime(df['date'])
    df['user_id'] = df['user_id'].astype(int)
    df['pages_viewed'] = df['pages_viewed'].astype(int)
    df['features_used'] = df['features_used'].astype(int)
    df['conversion'] = df['conversion'].astype(int)
    df['satisfaction_score'] = df['satisfaction_score'].astype(int)
    
    # Detect column types
    data_types, metrics, dimensions, time_columns = detect_data_type(df)
    
    return df, data_types, metrics, dimensions, time_columns
