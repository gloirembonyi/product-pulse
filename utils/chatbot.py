import os
import json
import pandas as pd
import numpy as np
import random
import requests
from datetime import datetime

# Global flag for whether to attempt to reload the API config
SHOULD_RELOAD_API = False

# Set up the Gemini API using direct API calls
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
HAS_GEMINI = bool(GEMINI_API_KEY)
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def reload_api_config():
    """Reload the Gemini API configuration with the current environment variable"""
    global HAS_GEMINI, GEMINI_API_KEY
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    HAS_GEMINI = bool(GEMINI_API_KEY)
    return HAS_GEMINI

def call_gemini_api(prompt):
    """Call Gemini API directly using requests"""
    if not GEMINI_API_KEY:
        return None
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                if "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"]:
                    text_parts = [part.get("text", "") for part in result["candidates"][0]["content"]["parts"] if "text" in part]
                    return "\n".join(text_parts)
        
        print(f"API Error: Status {response.status_code}, Response: {response.text[:200]}")
        return None
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def process_query(query, df):
    """
    Process a natural language query about the data using Google's Gemini
    or fallback to a simpler analysis if Gemini is not available
    
    Args:
        query (str): Natural language query from the user
        df (pandas.DataFrame): The dataframe containing the data
    
    Returns:
        str: Response to the query
    """
    # Try to reload the API config if needed (e.g. after setting API key)
    global SHOULD_RELOAD_API
    if SHOULD_RELOAD_API:
        reload_api_config()
        SHOULD_RELOAD_API = False
    
    # Prepare data description
    columns_description = []
    for col in df.columns:
        # Get column type and sample values
        col_type = str(df[col].dtype)
        sample_values = df[col].dropna().sample(min(3, len(df))).tolist()
        
        # Format description
        columns_description.append(f"- {col} ({col_type}): Sample values: {sample_values}")
    
    # Prepare data summary
    data_summary = {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "data_types": {col: str(df[col].dtype) for col in df.columns},
        "numeric_columns_summary": {col: {"mean": float(df[col].mean()), "min": float(df[col].min()), "max": float(df[col].max())} 
                                   for col in df.select_dtypes(include=[np.number]).columns},
        "categorical_columns_unique_values": {col: int(df[col].nunique()) 
                                            for col in df.select_dtypes(include=["object", "category"]).columns}
    }
    
    # Try to infer time columns
    time_columns = [col for col in df.columns if pd.api.types.is_datetime64_dtype(df[col])]
    if time_columns:
        data_summary["time_range"] = {col: {"start": df[col].min().strftime("%Y-%m-%d"), 
                                            "end": df[col].max().strftime("%Y-%m-%d")} 
                                     for col in time_columns}
    
    # Convert any numpy types to Python native types for JSON serialization
    data_summary_str = json.dumps(data_summary, default=str)
    
    # Try to use Gemini API if available
    if HAS_GEMINI:
    # Prepare complete prompt
    prompt = f"""
    You are a data analyst assistant for product managers. You help analyze product analytics data.
    
    The user will ask you questions about their data. Respond with clear, concise insights.
    
    Here is information about the data:
    Number of rows: {len(df)}
    Number of columns: {len(df.columns)}
    
    Columns:
    {chr(10).join(columns_description)}
    
    Data summary: {data_summary_str}
    
    User query: {query}
    
    When answering:
    1. Interpret what analysis they're looking for
    2. Provide a direct answer based on the data
    3. Add 1-2 additional insights if relevant
    4. When suggesting visualizations, be specific about chart type and variables
    5. For trend analysis, note any patterns or anomalies
    
    Keep responses friendly and clear. Avoid technical jargon unless specifically requested.
    """
    
        # Call Gemini API directly
        response_text = call_gemini_api(prompt)
        if response_text:
            return response_text
    
    # FALLBACK: Rule-based data analysis system
    return generate_rule_based_response(query, df, data_summary)

def generate_rule_based_response(query, df, data_summary):
    """
    Generate responses based on basic rules when Gemini API is not available
    
    Args:
        query (str): User's query
        df (pandas.DataFrame): Dataframe
        data_summary (dict): Data summary
    
    Returns:
        str: Response to the query
    """
    query = query.lower()
    
    # Identify numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Basic summary stats
    if any(word in query for word in ["summary", "overview", "describe", "summarize"]):
        response = f"Here's a summary of your data:\n\n"
        response += f"• Dataset has {len(df)} rows and {len(df.columns)} columns\n"
        if numeric_cols:
            response += f"• Numeric columns: {', '.join(numeric_cols[:5])}"
            if len(numeric_cols) > 5:
                response += f" and {len(numeric_cols) - 5} more"
            response += "\n"
        
        # Add summary of a few numeric columns
        for col in numeric_cols[:3]:
            response += f"• {col}: avg={df[col].mean():.2f}, min={df[col].min():.2f}, max={df[col].max():.2f}\n"
        
        return response
    
    # Average/mean queries
    if any(word in query for word in ["average", "mean", "avg"]):
        for col in numeric_cols:
            if col.lower() in query:
                avg_val = df[col].mean()
                return f"The average {col} is {avg_val:.2f}. This is based on {len(df)} data points."
        
        # If specific column not mentioned, return averages for main numeric columns
        response = "Here are the averages for key metrics:\n\n"
        for col in numeric_cols[:5]:
            response += f"• Average {col}: {df[col].mean():.2f}\n"
        return response
    
    # Maximum queries
    if any(word in query for word in ["maximum", "max", "highest", "top"]):
        for col in numeric_cols:
            if col.lower() in query:
                max_val = df[col].max()
                max_row = df.loc[df[col].idxmax()]
                response = f"The maximum {col} is {max_val:.2f}."
                
                # Add context from the row with max value
                for other_col in df.columns[:3]:
                    if other_col != col:
                        response += f"\nCorresponding {other_col}: {max_row[other_col]}"
                        
                return response
        
        # If specific column not mentioned
        response = "Here are the maximum values for key metrics:\n\n"
        for col in numeric_cols[:5]:
            response += f"• Maximum {col}: {df[col].max():.2f}\n"
        return response
    
    # Minimum queries
    if any(word in query for word in ["minimum", "min", "lowest", "bottom"]):
        for col in numeric_cols:
            if col.lower() in query:
                min_val = df[col].min()
                min_row = df.loc[df[col].idxmin()]
                response = f"The minimum {col} is {min_val:.2f}."
                
                # Add context from the row with min value
                for other_col in df.columns[:3]:
                    if other_col != col:
                        response += f"\nCorresponding {other_col}: {min_row[other_col]}"
                        
                return response
        
        # If specific column not mentioned
        response = "Here are the minimum values for key metrics:\n\n"
        for col in numeric_cols[:5]:
            response += f"• Minimum {col}: {df[col].min():.2f}\n"
        return response
    
    # Correlation/relationship queries
    if any(word in query for word in ["correlation", "relationship", "related", "correlate"]):
        if len(numeric_cols) >= 2:
            # Get correlation between main numeric columns
            corr = df[numeric_cols].corr().round(2)
            
            # Find strongest correlation
            strongest_corr = 0
            col1, col2 = None, None
            
            for i in range(len(numeric_cols)):
                for j in range(i+1, len(numeric_cols)):
                    if abs(corr.iloc[i, j]) > abs(strongest_corr):
                        strongest_corr = corr.iloc[i, j]
                        col1, col2 = numeric_cols[i], numeric_cols[j]
            
            response = f"Analyzing relationships between metrics:\n\n"
            
            if col1 and col2:
                corr_desc = "positive" if strongest_corr > 0 else "negative"
                strength = "strong" if abs(strongest_corr) > 0.7 else "moderate" if abs(strongest_corr) > 0.3 else "weak"
                
                response += f"• The strongest relationship is between {col1} and {col2}, with a {strength} {corr_desc} correlation of {strongest_corr}.\n"
                response += f"• This suggests that as {col1} {'increases' if strongest_corr > 0 else 'decreases'}, {col2} tends to {'increase' if strongest_corr > 0 else 'decrease'} as well.\n"
            
            # Add a few more correlations
            for i in range(min(3, len(numeric_cols))):
                for j in range(i+1, min(4, len(numeric_cols))):
                    if numeric_cols[i] != col1 or numeric_cols[j] != col2:  # Skip the strongest one we already reported
                        corr_val = corr.loc[numeric_cols[i], numeric_cols[j]]
                        if abs(corr_val) > 0.2:  # Only report if there's at least some correlation
                            corr_desc = "positive" if corr_val > 0 else "negative"
                            strength = "strong" if abs(corr_val) > 0.7 else "moderate" if abs(corr_val) > 0.3 else "weak"
                            response += f"• There is a {strength} {corr_desc} correlation ({corr_val}) between {numeric_cols[i]} and {numeric_cols[j]}.\n"
            
            return response
        else:
            return "Not enough numeric columns to analyze correlations. Need at least two numeric columns."
    
    # Trends and patterns
    if any(word in query for word in ["trend", "pattern", "over time", "change"]):
        time_cols = [col for col in df.columns if any(time_word in col.lower() for time_word in ["date", "time", "day", "month", "year"])]
        
        if time_cols and numeric_cols:
            time_col = time_cols[0]
            metric_col = numeric_cols[0]
            
            # Check if we can parse the time column
            try:
                if not pd.api.types.is_datetime64_dtype(df[time_col]):
                    df[time_col] = pd.to_datetime(df[time_col])
                
                # Sort by time
                df_sorted = df.sort_values(by=time_col)
                
                # Calculate basic trend
                first_value = df_sorted[metric_col].iloc[0]
                last_value = df_sorted[metric_col].iloc[-1]
                change = last_value - first_value
                percent_change = (change / first_value * 100) if first_value != 0 else 0
                
                # Determine trend direction
                if percent_change > 5:
                    trend = "increasing"
                elif percent_change < -5:
                    trend = "decreasing"
                else:
                    trend = "stable"
                
                response = f"Analyzing trends in {metric_col} over time:\n\n"
                response += f"• The overall trend is {trend} with a {abs(percent_change):.1f}% {'increase' if percent_change > 0 else 'decrease'} over the entire period.\n"
                response += f"• Starting value: {first_value:.2f}, Ending value: {last_value:.2f}\n"
                
                # Check for seasonality if enough data points
                if len(df) > 20:
                    response += f"• To detect seasonality patterns, consider using the Trend Analysis tab with the {time_col} column.\n"
                
                return response
            except:
                pass
    
    # Distribution analysis
    if any(word in query for word in ["distribution", "histogram", "spread"]):
        for col in numeric_cols:
            if col.lower() in query:
                mean = df[col].mean()
                median = df[col].median()
                std = df[col].std()
                skew = mean - median
                
                response = f"Distribution analysis of {col}:\n\n"
                response += f"• Mean: {mean:.2f}, Median: {median:.2f}\n"
                response += f"• Standard Deviation: {std:.2f}\n"
                
                if abs(skew) > 0.1 * std:
                    skew_direction = "right" if skew > 0 else "left"
                    response += f"• The distribution is skewed to the {skew_direction} (mean {'>' if skew > 0 else '<'} median).\n"
                else:
                    response += f"• The distribution appears to be approximately symmetric.\n"
                
                # Quartile information
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                
                response += f"• 25% of values are below {q1:.2f}, 75% are below {q3:.2f}\n"
                response += f"• The middle 50% of values fall between {q1:.2f} and {q3:.2f} (IQR: {iqr:.2f})\n"
                
                return response
        
        # If no specific column was mentioned
        response = "Here are distribution insights for key metrics:\n\n"
        for col in numeric_cols[:3]:
            mean = df[col].mean()
            median = df[col].median()
            response += f"• {col}: mean={mean:.2f}, median={median:.2f}, std={df[col].std():.2f}\n"
        
        return response
    
    # Insight generation (generic fallback)
    insights = []
    
    # Size of dataset
    insights.append(f"Your dataset contains {len(df)} records with {len(df.columns)} variables.")
    
    # Key metric insights
    for col in numeric_cols[:3]:
        mean_val = df[col].mean()
        max_val = df[col].max()
        min_val = df[col].min()
        insights.append(f"The average {col} is {mean_val:.2f}, ranging from {min_val:.2f} to {max_val:.2f}.")
    
    # Categorical insights
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    if cat_cols:
        col = cat_cols[0]
        top_vals = df[col].value_counts().nlargest(3)
        insights.append(f"Top values for {col}: " + ", ".join([f"{v} ({c} occurrences)" for v, c in top_vals.items()]))
    
    # Add generic insights based on column names
    metric_keywords = {
        "revenue": "Revenue metrics suggest monitoring sales performance closely.",
        "sale": "Analyzing sales patterns may reveal opportunities for growth.",
        "conversion": "Conversion metrics are critical for optimizing your marketing funnel.",
        "retention": "User retention appears to be a key metric in your dataset.",
        "churn": "Monitoring churn rates can help identify areas for improving user satisfaction.",
        "engagement": "User engagement metrics show how users interact with your product.",
        "session": "Session data can provide insights into user behavior patterns.",
        "user": "User-related metrics form the foundation of your product analytics."
    }
    
    for keyword, insight in metric_keywords.items():
        for col in df.columns:
            if keyword in col.lower() and insight not in insights:
                insights.append(insight)
                break
    
    return "\n\n".join(insights[:5])  # Return top 5 insights

def generate_insights(df):
    """
    Generate automatic insights from the data using Google's Gemini
    or fallback to a simpler analysis if Gemini is not available
    
    Args:
        df (pandas.DataFrame): The dataframe containing the data
    
    Returns:
        list: List of insight strings
    """
    # Try to reload the API config if needed
    global SHOULD_RELOAD_API
    if SHOULD_RELOAD_API:
        reload_api_config()
        SHOULD_RELOAD_API = False
        
    # Prepare data summary
    data_summary = {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "data_types": {col: str(df[col].dtype) for col in df.columns},
    }
    
    # Add sample of data
    data_sample = df.head(5).to_dict(orient="records")
    
    # Convert any numpy types to Python native types for JSON serialization
    data_summary_str = json.dumps(data_summary, default=str)
    data_sample_str = json.dumps(data_sample, default=str)
    
    # Try to use Gemini API if available
    if HAS_GEMINI:
    # Prepare prompt
    prompt = f"""
    You are a data analyst assistant for product managers. You help analyze product analytics data.
    
    Based on the following data summary and sample, generate 3-5 key insights. 
    
    Data summary: {data_summary_str}
    
    Sample data: {data_sample_str}
    
    Focus on:
    1. Patterns in the data that might be relevant to product managers
    2. Potential areas of concern or opportunity
    3. Interesting relationships between variables
    4. Suggestions for further analysis
    
    Format your response as a bulleted list of insights, with each bullet starting with "- ".
    """
    
        # Call Gemini API directly
        response_text = call_gemini_api(prompt)
        if response_text:
            # Extract the insights from the response
            insights = [line.strip().replace("- ", "") for line in response_text.split("\n") if line.strip().startswith("- ")]
        
        # If no insights were extracted with the bullet format, try to extract sentences
        if not insights:
                insights = [sentence.strip() for sentence in response_text.split(".") if sentence.strip()]
            if len(insights) > 5:
                insights = insights[:5]  # Limit to 5 insights
                
        return insights
    
    # FALLBACK: Generate basic insights
    return generate_rule_based_insights(df)

def generate_rule_based_insights(df):
    """Generate insights without using Gemini API"""
    insights = []
    
    # Dataset size insight
    insights.append(f"Your dataset contains {len(df)} records with {len(df.columns)} variables, providing a solid base for product analytics.")
    
    # Numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Categorical columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Time columns (guessing based on name)
    potential_time_cols = [col for col in df.columns if any(time_word in col.lower() 
                                                         for time_word in ["date", "time", "day", "month", "year"])]
    
    # Add insight about data composition
    insights.append(f"The data contains {len(numeric_cols)} numeric metrics, {len(categorical_cols)} categorical dimensions, and {len(potential_time_cols)} potential time-related columns.")
    
    # Add insights for specific metrics if they exist
    metric_keywords = {
        "revenue": "Revenue metrics can be analyzed to identify your most profitable segments.",
        "sale": "Sales data enables trend analysis to identify seasonality and growth patterns.",
        "conversion": "Conversion rates should be monitored to optimize your marketing and sales funnel.",
        "retention": "User retention is a key indicator of product satisfaction and should be tracked over time.",
        "churn": "Analyzing churn factors can help reduce customer attrition and increase lifetime value.",
        "engagement": "Engagement metrics reveal how users interact with your product features.",
        "session": "Session metrics like duration and frequency indicate user interest and product stickiness.",
        "user": "User-centric metrics form the foundation for understanding your customer base."
    }
    
    for keyword, insight in metric_keywords.items():
        for col in df.columns:
            if keyword in col.lower() and insight not in insights:
                insights.append(insight)
                break
    
    # Add correlation insights if we have multiple numeric columns
    if len(numeric_cols) >= 2:
        # Get correlation between main numeric columns
        try:
            corr = df[numeric_cols].corr().round(2)
            
            # Find strongest correlation
            strongest_corr = 0
            col1, col2 = None, None
            
            for i in range(len(numeric_cols)):
                for j in range(i+1, len(numeric_cols)):
                    if abs(corr.iloc[i, j]) > abs(strongest_corr):
                        strongest_corr = corr.iloc[i, j]
                        col1, col2 = numeric_cols[i], numeric_cols[j]
            
            if col1 and col2 and abs(strongest_corr) > 0.5:
                corr_desc = "positive" if strongest_corr > 0 else "negative"
                strength = "strong" if abs(strongest_corr) > 0.7 else "moderate"
                
                insights.append(f"There is a {strength} {corr_desc} correlation ({strongest_corr}) between {col1} and {col2}, suggesting they move {'together' if strongest_corr > 0 else 'in opposite directions'}.")
        except:
            pass
    
    # Add time-based insight if we have potential time columns
    if potential_time_cols:
        insights.append("Consider using the Trend Analysis tab to explore how metrics change over time and identify patterns.")
    
    # Add segmentation insight if we have categorical columns
    if categorical_cols:
        segment_col = categorical_cols[0]
        insights.append(f"Using the Segmentation tab to analyze metrics by {segment_col} may reveal valuable differences between customer groups.")
    
    # Add recommendation based on columns
    custom_recommendations = [
        "Regular monitoring of these metrics in a dashboard can help track product performance and make data-driven decisions.",
        "Consider setting up alerts for significant changes in key metrics to quickly identify issues or opportunities.",
        "Use cohort analysis to understand how user behavior evolves over time after product changes.",
        "Comparing metrics across different segments can uncover opportunities for targeted improvements."
    ]
    
    insights.append(random.choice(custom_recommendations))
    
    # Return only up to 5 insights
    return insights[:5]
