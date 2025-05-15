import os
import json
import pandas as pd
import numpy as np
import google.generativeai as genai

# Set up the Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def process_query(query, df):
    """
    Process a natural language query about the data using Google's Gemini
    
    Args:
        query (str): Natural language query from the user
        df (pandas.DataFrame): The dataframe containing the data
    
    Returns:
        str: Response to the query
    """
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
    
    # Call Gemini API
    try:
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        return response.text
    
    except Exception as e:
        return f"Sorry, I couldn't process your query. Error: {str(e)}"

def generate_insights(df):
    """
    Generate automatic insights from the data using Google's Gemini
    
    Args:
        df (pandas.DataFrame): The dataframe containing the data
    
    Returns:
        list: List of insight strings
    """
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
    
    # Call Gemini API
    try:
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Extract the insights
        insights_text = response.text
        
        # Split into list of insights
        insights = [line.strip().replace("- ", "") for line in insights_text.split("\n") if line.strip().startswith("- ")]
        
        # If no insights were extracted with the bullet format, try to extract sentences
        if not insights:
            insights = [sentence.strip() for sentence in insights_text.split(".") if sentence.strip()]
            if len(insights) > 5:
                insights = insights[:5]  # Limit to 5 insights
                
        return insights
    
    except Exception as e:
        return [f"Could not generate automatic insights. Error: {str(e)}"]
