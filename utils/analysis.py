import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

def perform_trend_analysis(df, time_column, metric, options=None):
    """
    Perform trend analysis on time series data
    
    Args:
        df (pandas.DataFrame): Input data
        time_column (str): Column containing time data
        metric (str): Metric to analyze
        options (list): Analysis options to include
    
    Returns:
        tuple: (trend_data_df, insights_list)
    """
    # Ensure the data is sorted by time
    df = df.sort_values(by=time_column)
    
    # Group by date if there are multiple entries per date
    if df[time_column].nunique() < len(df):
        trend_data = df.groupby(time_column)[metric].mean().reset_index()
    else:
        trend_data = df[[time_column, metric]].copy()
    
    # Fill any missing values with interpolation
    trend_data[metric] = trend_data[metric].interpolate(method='linear')
    
    # List to store insights
    insights = []
    
    # Calculate moving average if selected
    if options is None or "Moving Average" in options:
        window_size = min(7, len(trend_data) // 3)  # Use 7-day window or 1/3 of data points
        trend_data[f"{metric}_ma"] = trend_data[metric].rolling(window=window_size, center=True).mean()
        
        # Fill in the missing values at the edges
        trend_data[f"{metric}_ma"] = trend_data[f"{metric}_ma"].fillna(trend_data[metric])
        
        # Add insight about moving average
        ma_change = (trend_data[f"{metric}_ma"].iloc[-1] - trend_data[f"{metric}_ma"].iloc[0]) / trend_data[f"{metric}_ma"].iloc[0] * 100
        insights.append(f"Moving Average: {metric} has {'increased' if ma_change > 0 else 'decreased'} by {abs(ma_change):.1f}% over the period.")
    
    # Calculate trend line if selected
    if options is None or "Trend Line" in options:
        # Create a numeric X variable for the regression
        X = np.array(range(len(trend_data))).reshape(-1, 1)
        y = trend_data[metric].values
        
        # Fit a linear regression model
        model = LinearRegression()
        model.fit(X, y)
        
        # Add the trend line to the data
        trend_data[f"{metric}_trend"] = model.predict(X)
        
        # Calculate overall trend
        slope = model.coef_[0]
        total_change = (trend_data[f"{metric}_trend"].iloc[-1] - trend_data[f"{metric}_trend"].iloc[0])
        percent_change = (total_change / trend_data[f"{metric}_trend"].iloc[0]) * 100
        
        # Add insights about the trend
        if abs(percent_change) < 5:
            trend_type = "flat"
        elif percent_change > 0:
            trend_type = "increasing"
        else:
            trend_type = "decreasing"
            
        insights.append(f"Trend: {metric} shows a {trend_type} trend with a {abs(percent_change):.1f}% {'' if percent_change < 0 else 'gain'} over the time period.")
    
    # Calculate seasonality if selected
    if options is not None and "Seasonality" in options:
        # We need at least 2 complete cycles to detect seasonality
        if len(trend_data) >= 14:  # At least 2 weeks of data
            # Simple approach: subtract the trend from the data and look for patterns
            # This is a simplification - for real seasonality analysis, consider more advanced methods
            trend_data[f"{metric}_detrended"] = trend_data[metric] - trend_data[f"{metric}_trend"]
            
            # Check for weekly patterns (most common in product data)
            day_of_week = pd.to_datetime(trend_data[time_column]).dt.dayofweek
            weekday_avg = trend_data.groupby(day_of_week)[f"{metric}_detrended"].mean()
            
            # If there is significant variation by day of week, we consider it seasonal
            weekday_variation = weekday_avg.max() - weekday_avg.min()
            weekday_variation_pct = weekday_variation / trend_data[metric].mean() * 100
            
            if weekday_variation_pct > 10:  # More than 10% variation indicates seasonality
                # Add the seasonal component
                trend_data[f"{metric}_seasonal"] = [weekday_avg[d] for d in day_of_week]
                
                # Add insight about seasonality
                max_day = weekday_avg.idxmax()
                min_day = weekday_avg.idxmin()
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                insights.append(f"Seasonality: {metric} tends to be highest on {days[max_day]} and lowest on {days[min_day]}, with a {weekday_variation_pct:.1f}% variation.")
            else:
                trend_data[f"{metric}_seasonal"] = 0
                insights.append(f"Seasonality: No significant weekly patterns detected in {metric}.")
        else:
            trend_data[f"{metric}_seasonal"] = 0
            insights.append(f"Seasonality: Not enough data to detect seasonal patterns in {metric}.")
    
    # Detect outliers if selected
    if options is not None and "Outliers" in options:
        if f"{metric}_ma" in trend_data.columns:
            # Calculate the residuals from the moving average
            residuals = trend_data[metric] - trend_data[f"{metric}_ma"]
            
            # Calculate the standard deviation of residuals
            std_residuals = residuals.std()
            
            # Mark outliers as points that are more than 2 standard deviations away from the moving average
            trend_data[f"{metric}_outlier"] = ((residuals.abs() > 2 * std_residuals) & 
                                             (trend_data[metric].abs() > 0.01 * trend_data[metric].mean())).astype(int)
            
            # Count outliers
            num_outliers = trend_data[f"{metric}_outlier"].sum()
            
            if num_outliers > 0:
                # Find the most extreme outlier
                max_outlier_idx = residuals.abs().idxmax()
                max_outlier_date = trend_data.loc[max_outlier_idx, time_column]
                max_outlier_value = trend_data.loc[max_outlier_idx, metric]
                expected_value = trend_data.loc[max_outlier_idx, f"{metric}_ma"]
                
                # Add insight about outliers
                insights.append(f"Outliers: Detected {num_outliers} outliers in {metric}. Most significant on {max_outlier_date.strftime('%Y-%m-%d') if hasattr(max_outlier_date, 'strftime') else max_outlier_date} with value {max_outlier_value:.2f} (expected around {expected_value:.2f}).")
            else:
                insights.append(f"Outliers: No significant outliers detected in {metric}.")
        else:
            # If no moving average, use the trend line
            residuals = trend_data[metric] - trend_data[f"{metric}_trend"]
            std_residuals = residuals.std()
            
            trend_data[f"{metric}_outlier"] = ((residuals.abs() > 2.5 * std_residuals) & 
                                             (trend_data[metric].abs() > 0.01 * trend_data[metric].mean())).astype(int)
            
            num_outliers = trend_data[f"{metric}_outlier"].sum()
            
            if num_outliers > 0:
                insights.append(f"Outliers: Detected {num_outliers} outliers in {metric} that deviate significantly from the trend.")
            else:
                insights.append(f"Outliers: No significant outliers detected in {metric}.")
    
    return trend_data, insights

def segment_data(df, segment_by, metric, options=None):
    """
    Perform segmentation analysis
    
    Args:
        df (pandas.DataFrame): Input data
        segment_by (str): Column to segment by
        metric (str): Metric to analyze
        options (list): Analysis options to include
    
    Returns:
        tuple: (segmented_df, insights_list)
    """
    # Copy the data
    segmented_df = df.copy()
    
    # List to store insights
    insights = []
    
    # Group by the segment
    grouped = segmented_df.groupby(segment_by)[metric].agg(['mean', 'median', 'std', 'count']).reset_index()
    
    # Calculate overall statistics
    overall_mean = segmented_df[metric].mean()
    overall_median = segmented_df[metric].median()
    overall_std = segmented_df[metric].std()
    
    # Add insights about the segments
    top_segment = grouped.sort_values('mean', ascending=False).iloc[0]
    bottom_segment = grouped.sort_values('mean', ascending=True).iloc[0]
    
    insights.append(f"Segment Analysis: {top_segment[segment_by]} has the highest average {metric} at {top_segment['mean']:.2f} ({(top_segment['mean']/overall_mean - 1)*100:.1f}% above overall average).")
    insights.append(f"Segment Analysis: {bottom_segment[segment_by]} has the lowest average {metric} at {bottom_segment['mean']:.2f} ({(bottom_segment['mean']/overall_mean - 1)*100:.1f}% compared to overall average).")
    
    # Compare segments to average if selected
    if options is not None and "Compare to Average" in options:
        # Calculate the difference from the overall mean for each segment
        grouped['diff_from_avg'] = grouped['mean'] - overall_mean
        grouped['diff_pct'] = (grouped['mean'] / overall_mean - 1) * 100
        
        # Sort by difference percentage
        grouped = grouped.sort_values('diff_pct', ascending=False)
        
        # Add segments with large differences to insights
        for _, row in grouped.iterrows():
            if abs(row['diff_pct']) > 20:  # More than 20% difference
                direction = "above" if row['diff_pct'] > 0 else "below"
                insights.append(f"Comparison: {row[segment_by]} is {abs(row['diff_pct']):.1f}% {direction} the overall average for {metric}.")
    
    # Detect outliers within segments if selected
    if options is not None and "Detect Outliers" in options:
        # Calculate outliers within each segment
        segmented_df[f"{metric}_outlier"] = 0
        
        # Process each segment
        for segment_value in segmented_df[segment_by].unique():
            mask = segmented_df[segment_by] == segment_value
            segment_data = segmented_df.loc[mask, metric]
            
            if len(segment_data) >= 5:  # Need enough data points
                # Get segment statistics
                segment_mean = segment_data.mean()
                segment_std = segment_data.std()
                
                # Mark outliers
                outliers = (segment_data - segment_mean).abs() > 2 * segment_std
                segmented_df.loc[mask & outliers, f"{metric}_outlier"] = 1
        
        # Count outliers per segment
        outlier_counts = segmented_df.groupby(segment_by)[f"{metric}_outlier"].sum().reset_index()
        outlier_pcts = segmented_df.groupby(segment_by)[f"{metric}_outlier"].mean().reset_index()
        
        # Add insights about segments with high outlier percentages
        for _, row in outlier_pcts.sort_values(f"{metric}_outlier", ascending=False).head(3).iterrows():
            if row[f"{metric}_outlier"] > 0.05:  # More than 5% outliers
                segment_outlier_count = outlier_counts[outlier_counts[segment_by] == row[segment_by]][f"{metric}_outlier"].values[0]
                insights.append(f"Outliers: {row[segment_by]} has a high proportion of outliers ({row[f'{metric}_outlier']*100:.1f}%, {segment_outlier_count} points) for {metric}.")
    
    return segmented_df, insights
