import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def create_dashboard(df, metrics, dimension=None, chart_type="Bar Chart"):
    """
    Create an interactive visualization based on selected metrics and dimensions
    
    Args:
        df (pandas.DataFrame): The data to visualize
        metrics (list): List of metric columns to include
        dimension (str, optional): Dimension to group by
        chart_type (str): Type of chart to create
    
    Returns:
        plotly.graph_objects.Figure: Interactive visualization
    """
    # Handle the case with no dimension (overall metrics)
    if dimension is None or dimension == "None":
        # For a single metric with no dimension, show simple aggregate stats
        if len(metrics) == 1:
            metric = metrics[0]
            
            if chart_type == "Bar Chart":
                fig = go.Figure(go.Bar(
                    x=["Total"],
                    y=[df[metric].sum()],
                    text=[f"{df[metric].sum():.2f}"],
                    textposition='auto'
                ))
                fig.update_layout(title=f"Total {metric}", xaxis_title="", yaxis_title=metric)
                
            elif chart_type == "Histogram":
                fig = px.histogram(
                    df, x=metric,
                    title=f"Distribution of {metric}"
                )
                
            else:  # Default to statistics
                stats = df[metric].describe()
                fig = go.Figure(data=[
                    go.Bar(
                        x=['Mean', 'Median', 'Min', 'Max'],
                        y=[stats['mean'], df[metric].median(), stats['min'], stats['max']],
                        text=[f"{stats['mean']:.2f}", f"{df[metric].median():.2f}", 
                              f"{stats['min']:.2f}", f"{stats['max']:.2f}"],
                        textposition='auto'
                    )
                ])
                fig.update_layout(title=f"Statistics for {metric}", xaxis_title="Statistic", yaxis_title=metric)
                
        # For multiple metrics with no dimension, compare them
        else:
            if chart_type == "Bar Chart":
                data = []
                for metric in metrics:
                    data.append(go.Bar(
                        name=metric,
                        x=["Total"],
                        y=[df[metric].mean()],
                        text=[f"{df[metric].mean():.2f}"],
                        textposition='auto'
                    ))
                fig = go.Figure(data=data)
                fig.update_layout(title="Average Metrics Comparison", barmode='group')
                
            elif chart_type == "Scatter Plot":
                if len(metrics) >= 2:
                    fig = px.scatter(
                        df, x=metrics[0], y=metrics[1],
                        title=f"{metrics[0]} vs {metrics[1]}"
                    )
                else:
                    fig = go.Figure()
                    fig.update_layout(title="Need at least 2 metrics for scatter plot")
            
            else:  # Default to box plots
                fig = go.Figure()
                for metric in metrics:
                    fig.add_trace(go.Box(
                        y=df[metric],
                        name=metric,
                        boxmean=True
                    ))
                fig.update_layout(title="Distribution Comparison")
    
    # Handle case with dimension (grouped metrics)
    else:
        grouped = df.groupby(dimension).agg({m: 'mean' for m in metrics})
        
        if chart_type == "Bar Chart":
            fig = px.bar(
                grouped.reset_index(), 
                x=dimension, 
                y=metrics,
                barmode='group',
                title=f"Metrics by {dimension}"
            )
            
        elif chart_type == "Line Chart":
            fig = px.line(
                grouped.reset_index(), 
                x=dimension, 
                y=metrics,
                markers=True,
                title=f"Metrics by {dimension}"
            )
            
        elif chart_type == "Pie Chart":
            if len(metrics) == 1:
                metric = metrics[0]
                pie_data = df.groupby(dimension)[metric].sum().reset_index()
                fig = px.pie(
                    pie_data, 
                    values=metric, 
                    names=dimension,
                    title=f"{metric} by {dimension}"
                )
            else:
                # Multiple metrics not supported for pie chart
                # Fall back to bar chart
                fig = px.bar(
                    grouped.reset_index(), 
                    x=dimension, 
                    y=metrics,
                    barmode='group',
                    title=f"Metrics by {dimension} (Multiple metrics not supported for pie chart)"
                )
                
        elif chart_type == "Scatter Plot":
            if len(metrics) >= 2:
                fig = px.scatter(
                    df, 
                    x=metrics[0], 
                    y=metrics[1],
                    color=dimension,
                    title=f"{metrics[0]} vs {metrics[1]} by {dimension}"
                )
            else:
                fig = go.Figure()
                fig.update_layout(title="Need at least 2 metrics for scatter plot")
                
        elif chart_type == "Box Plot":
            fig = go.Figure()
            for metric in metrics:
                for dim_value in df[dimension].unique():
                    sub_df = df[df[dimension] == dim_value]
                    fig.add_trace(go.Box(
                        y=sub_df[metric],
                        name=f"{dim_value} - {metric}",
                        boxmean=True
                    ))
            fig.update_layout(title=f"Distribution by {dimension}")
            
        else:  # Default to bar chart
            fig = px.bar(
                grouped.reset_index(), 
                x=dimension, 
                y=metrics,
                barmode='group',
                title=f"Metrics by {dimension}"
            )
    
    # Common layout updates
    fig.update_layout(
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white"
    )
    
    return fig

def create_trend_plot(trend_data, time_column, metric, options):
    """
    Create an interactive time series visualization with trend components
    
    Args:
        trend_data (pandas.DataFrame): The data with trend components
        time_column (str): Column representing time
        metric (str): Metric to visualize
        options (list): List of trend components to include
    
    Returns:
        plotly.graph_objects.Figure: Interactive trend visualization
    """
    fig = go.Figure()
    
    # Add the original data
    fig.add_trace(go.Scatter(
        x=trend_data[time_column],
        y=trend_data[metric],
        mode='markers+lines',
        name=metric,
        line=dict(width=1),
        marker=dict(size=6)
    ))
    
    # Add moving average if selected
    if "Moving Average" in options and f"{metric}_ma" in trend_data.columns:
        fig.add_trace(go.Scatter(
            x=trend_data[time_column],
            y=trend_data[f"{metric}_ma"],
            mode='lines',
            name=f"{metric} (7-day MA)",
            line=dict(width=3, color='red')
        ))
    
    # Add trend line if selected
    if "Trend Line" in options and f"{metric}_trend" in trend_data.columns:
        fig.add_trace(go.Scatter(
            x=trend_data[time_column],
            y=trend_data[f"{metric}_trend"],
            mode='lines',
            name=f"{metric} (Trend)",
            line=dict(width=3, dash='dash', color='green')
        ))
    
    # Add seasonality component if selected
    if "Seasonality" in options and f"{metric}_seasonal" in trend_data.columns:
        fig.add_trace(go.Scatter(
            x=trend_data[time_column],
            y=trend_data[f"{metric}_seasonal"] + trend_data[f"{metric}_trend"],
            mode='lines',
            name=f"{metric} (Seasonality)",
            line=dict(width=2, color='purple')
        ))
    
    # Highlight outliers if selected
    if "Outliers" in options and f"{metric}_outlier" in trend_data.columns:
        outliers = trend_data[trend_data[f"{metric}_outlier"] == 1]
        if not outliers.empty:
            fig.add_trace(go.Scatter(
                x=outliers[time_column],
                y=outliers[metric],
                mode='markers',
                name='Outliers',
                marker=dict(
                    size=10,
                    color='red',
                    symbol='circle-open',
                    line=dict(width=2)
                )
            ))
    
    # Update layout
    fig.update_layout(
        title=f"Trend Analysis: {metric} Over Time",
        xaxis_title=time_column,
        yaxis_title=metric,
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white"
    )
    
    return fig

def create_distribution_plot(segment_data, segment_by, metric, options):
    """
    Create visualizations for data segmentation analysis
    
    Args:
        segment_data (pandas.DataFrame): The data with segmentation
        segment_by (str): Dimension used for segmentation
        metric (str): Metric being analyzed
        options (list): Analysis options selected
    
    Returns:
        plotly.graph_objects.Figure: Interactive segmentation visualization
    """
    # If value distribution is selected
    if "Value Distribution" in options:
        # Group the data by segment
        grouped = segment_data.groupby(segment_by).agg({
            metric: ['mean', 'median', 'std', 'count']
        }).reset_index()
        
        grouped.columns = [segment_by, f"{metric}_mean", f"{metric}_median", f"{metric}_std", "count"]
        
        # Sort by the mean value
        grouped = grouped.sort_values(by=f"{metric}_mean", ascending=False)
        
        # Create the figure
        fig = go.Figure()
        
        # Add bars for the mean values
        fig.add_trace(go.Bar(
            x=grouped[segment_by],
            y=grouped[f"{metric}_mean"],
            name=f"Average {metric}",
            error_y=dict(
                type="data",
                array=grouped[f"{metric}_std"],
                visible=True
            ),
            text=grouped["count"],
            textposition="auto",
            hovertemplate="%{x}<br>Mean: %{y:.2f}<br>Count: %{text}<extra></extra>"
        ))
        
        # Add markers for the median values
        fig.add_trace(go.Scatter(
            x=grouped[segment_by],
            y=grouped[f"{metric}_median"],
            mode="markers",
            name=f"Median {metric}",
            marker=dict(size=8, color="red"),
            hovertemplate="%{x}<br>Median: %{y:.2f}<extra></extra>"
        ))
        
        # If compare to average is selected
        if "Compare to Average" in options:
            overall_avg = segment_data[metric].mean()
            
            fig.add_shape(
                type="line",
                x0=-0.5,
                y0=overall_avg,
                x1=len(grouped) - 0.5,
                y1=overall_avg,
                line=dict(
                    color="green",
                    width=2,
                    dash="dash",
                )
            )
            
            fig.add_annotation(
                x=len(grouped) - 0.5,
                y=overall_avg,
                text=f"Overall Average: {overall_avg:.2f}",
                showarrow=False,
                yshift=10,
                bgcolor="rgba(255, 255, 255, 0.8)"
            )
        
        # If detect outliers is selected
        if "Detect Outliers" in options and f"{metric}_outlier" in segment_data.columns:
            # Get segments with high proportion of outliers
            outlier_pct = segment_data.groupby(segment_by)[f"{metric}_outlier"].mean().reset_index()
            outlier_pct = outlier_pct.sort_values(by=f"{metric}_outlier", ascending=False)
            
            # Add outlier information to hover
            hover_text = [f"{row[segment_by]}<br>Outlier %: {row[f'{metric}_outlier']*100:.1f}%" 
                          for _, row in outlier_pct.iterrows()]
            
            # Add trace for outlier percentage
            fig.add_trace(go.Scatter(
                x=outlier_pct[segment_by],
                y=outlier_pct[f"{metric}_outlier"] * max(grouped[f"{metric}_mean"]),  # Scale to fit
                mode="markers",
                name="Outlier %",
                marker=dict(
                    size=outlier_pct[f"{metric}_outlier"] * 50 + 5,  # Size proportional to outlier %
                    color="rgba(255, 165, 0, 0.5)",
                    symbol="circle"
                ),
                text=hover_text,
                hoverinfo="text",
                yaxis="y2"
            ))
            
            # Add second y-axis for outlier percentage
            fig.update_layout(
                yaxis2=dict(
                    title="Outlier %",
                    titlefont=dict(color="orange"),
                    tickfont=dict(color="orange"),
                    overlaying="y",
                    side="right",
                    showgrid=False,
                    range=[0, 1]
                )
            )
    
    else:
        # Default to a simple bar chart comparing the metric across segments
        fig = px.bar(
            segment_data.groupby(segment_by)[metric].mean().reset_index(),
            x=segment_by,
            y=metric,
            title=f"Average {metric} by {segment_by}"
        )
    
    # Update layout
    fig.update_layout(
        title=f"{metric} Distribution by {segment_by}",
        xaxis_title=segment_by,
        yaxis_title=metric,
        height=500,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig
