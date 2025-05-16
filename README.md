# ProductPulse Analytics

ProductPulse Analytics is a powerful dashboard for product managers to analyze and visualize product data using interactive charts, trend analysis, segmentation, and AI-powered insights.

## Features

- **Interactive Dashboard**: Visualize key metrics with customizable charts
- **Trend Analysis**: Identify patterns, seasonality, and anomalies in your metrics over time
- **User Segmentation**: Compare different user groups to discover what drives performance
- **AI Data Assistant**: Ask questions about your data in natural language
- **PostgreSQL Integration**: Cloud database storage with Neon PostgreSQL

## Getting Started

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. Clone this repository or download the project files
2. Install required packages:

```bash
pip install streamlit pandas numpy plotly scikit-learn psycopg2-binary sqlalchemy
```

### Running the Application

#### Windows Users

Simply double-click the `start_productpulse.bat` file to launch the application.

#### All Users

Run the following command in your terminal:

```bash
python start_app.py
```

This will:
1. Start the Streamlit server on port 5000
2. Open your web browser to access the dashboard
3. Connect to the Neon PostgreSQL database

You can also run Streamlit directly:

```bash
streamlit run app.py --server.port=5000
```

## Accessing the Dashboard

The dashboard is available at:
- Primary URL: http://localhost:5000

## Database Connection

The application is configured to use a Neon PostgreSQL database with the following connection string:

```
postgresql://neondb_owner:npg_E3By5fYHDgak@ep-silent-fog-a48gwvbn-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
```

## Using the Dashboard

1. Upload your CSV data or use the sample dataset
2. Explore the interactive dashboard to visualize key metrics
3. Analyze trends over time to identify patterns and anomalies
4. Segment your data to compare different user groups
5. Ask questions to the AI assistant for deeper insights
6. Save your analyses for future reference

## Troubleshooting

If you encounter any issues:

1. Ensure all required packages are installed
2. Check that port 5000 is not being used by another application
3. Verify your internet connection for database access
4. Run the test_db_connection.py script to verify database connectivity

```bash
python test_db_connection.py
``` 