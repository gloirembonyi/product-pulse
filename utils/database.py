import os
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Table, MetaData, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Get the database URL from environment variables or use a default SQLite database
DATABASE_URL = os.environ.get("DATABASE_URL") or "sqlite:///productpulse.db"

# Set up SQLAlchemy but handle connection errors gracefully
try:
    # Create SQLAlchemy engine and session
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create metadata object
    metadata = MetaData()

    # Define tables
    datasets = Table(
        'datasets', 
        metadata, 
        Column('id', Integer, primary_key=True),
        Column('name', String, nullable=False, unique=True),
        Column('description', String),
        Column('created_at', DateTime, default=datetime.now),
        Column('last_modified', DateTime, default=datetime.now, onupdate=datetime.now),
        Column('rows', Integer),
        Column('columns', Integer)
    )

    # Table for storing column metadata
    columns = Table(
        'columns',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('dataset_id', Integer),
        Column('name', String, nullable=False),
        Column('data_type', String),
        Column('is_metric', Boolean, default=False),
        Column('is_dimension', Boolean, default=False),
        Column('is_time', Boolean, default=False)
    )

    # Table for storing saved analysis
    saved_analysis = Table(
        'saved_analysis',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('dataset_id', Integer),
        Column('name', String, nullable=False),
        Column('description', String),
        Column('created_at', DateTime, default=datetime.now),
        Column('analysis_type', String),  # 'dashboard', 'trend', 'segment', etc.
        Column('configuration', String),  # JSON string with analysis parameters
        Column('insights', String)  # JSON string with generated insights
    )

    # Create all tables if they don't exist
    metadata.create_all(engine)
except Exception as e:
    print(f"Database connection error: {e}")
    # Set up fallback in-memory mode
    try:
        DATABASE_URL = "sqlite:///:memory:"
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        metadata = MetaData()
        
        # Redefine tables for in-memory database
        datasets = Table(
            'datasets', 
            metadata, 
            Column('id', Integer, primary_key=True),
            Column('name', String, nullable=False, unique=True),
            Column('description', String),
            Column('created_at', DateTime, default=datetime.now),
            Column('last_modified', DateTime, default=datetime.now, onupdate=datetime.now),
            Column('rows', Integer),
            Column('columns', Integer)
        )

        columns = Table(
            'columns',
            metadata,
            Column('id', Integer, primary_key=True),
            Column('dataset_id', Integer),
            Column('name', String, nullable=False),
            Column('data_type', String),
            Column('is_metric', Boolean, default=False),
            Column('is_dimension', Boolean, default=False),
            Column('is_time', Boolean, default=False)
        )

        saved_analysis = Table(
            'saved_analysis',
            metadata,
            Column('id', Integer, primary_key=True),
            Column('dataset_id', Integer),
            Column('name', String, nullable=False),
            Column('description', String),
            Column('created_at', DateTime, default=datetime.now),
            Column('analysis_type', String),
            Column('configuration', String),
            Column('insights', String)
        )
        
        # Create all tables in memory
        metadata.create_all(engine)
        print("Using in-memory database as fallback")
    except Exception as e:
        print(f"Failed to set up in-memory database: {e}")

def save_dataset(df, name, description=""):
    """
    Save a dataset to the database
    
    Args:
        df (pandas.DataFrame): The DataFrame to save
        name (str): Name for the dataset
        description (str): Description of the dataset
        
    Returns:
        int: ID of the saved dataset
    """
    try:
        # Check if dataset with this name already exists
        stmt = select(datasets).where(datasets.c.name == name)
        result = session.execute(stmt).fetchone()
        
        if result:
            # Update existing dataset
            dataset_id = result[0]
            session.execute(
                datasets.update().where(datasets.c.id == dataset_id).values(
                    last_modified=datetime.now(),
                    rows=len(df),
                    columns=len(df.columns),
                    description=description
                )
            )
            
            # Delete existing column metadata
            session.execute(
                columns.delete().where(columns.c.dataset_id == dataset_id)
            )
        else:
            # Insert new dataset
            result = session.execute(
                datasets.insert().values(
                    name=name,
                    description=description,
                    rows=len(df),
                    columns=len(df.columns)
                )
            )
            dataset_id = result.inserted_primary_key[0]
        
        # Save column metadata
        for col_name in df.columns:
            # Determine column type
            col_type = str(df[col_name].dtype)
            is_metric = pd.api.types.is_numeric_dtype(df[col_name]) and df[col_name].nunique() > 10
            is_dimension = not is_metric
            is_time = pd.api.types.is_datetime64_dtype(df[col_name])
            
            session.execute(
                columns.insert().values(
                    dataset_id=dataset_id,
                    name=col_name,
                    data_type=col_type,
                    is_metric=is_metric,
                    is_dimension=is_dimension,
                    is_time=is_time
                )
            )
        
        # Save the actual data to a table with the dataset name
        # Create a safe table name (remove special characters)
        table_name = f"data_{dataset_id}"
        
        # Write DataFrame to SQL table
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        
        session.commit()
        return dataset_id
        
    except Exception as e:
        session.rollback()
        print(f"Error saving dataset: {e}")
        return None

def get_saved_datasets():
    """
    Get a list of all saved datasets
    
    Returns:
        pandas.DataFrame: DataFrame with dataset information
    """
    try:
        stmt = select(datasets).order_by(datasets.c.last_modified.desc())
        results = session.execute(stmt).fetchall()
        
        if results:
            return pd.DataFrame(results, columns=datasets.c.keys())
        else:
            return pd.DataFrame(columns=datasets.c.keys())
            
    except Exception as e:
        print(f"Error fetching saved datasets: {e}")
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=['id', 'name', 'description', 'created_at', 'last_modified', 'rows', 'columns'])

def load_dataset(dataset_id):
    """
    Load a dataset from the database
    
    Args:
        dataset_id (int): ID of the dataset to load
        
    Returns:
        tuple: (DataFrame, column_data)
    """
    try:
        # Get dataset info
        stmt = select(datasets).where(datasets.c.id == dataset_id)
        dataset_info = session.execute(stmt).fetchone()
        
        if not dataset_info:
            raise ValueError(f"Dataset with ID {dataset_id} not found")
        
        # Get column data
        stmt = select(columns).where(columns.c.dataset_id == dataset_id)
        column_data = session.execute(stmt).fetchall()
        column_df = pd.DataFrame(column_data, columns=columns.c.keys())
        
        # Load the actual data
        table_name = f"data_{dataset_id}"
        df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
        
        # Convert datetime columns
        for col_name in df.columns:
            col_info = column_df[column_df['name'] == col_name]
            if not col_info.empty and col_info.iloc[0]['is_time']:
                df[col_name] = pd.to_datetime(df[col_name])
        
        return df, column_df
        
    except Exception as e:
        print(f"Error loading dataset: {e}")
        # Return empty DataFrame and columns
        empty_df = pd.DataFrame()
        empty_columns = pd.DataFrame(columns=['id', 'dataset_id', 'name', 'data_type', 'is_metric', 'is_dimension', 'is_time'])
        return empty_df, empty_columns

def delete_dataset(dataset_id):
    """
    Delete a dataset from the database
    
    Args:
        dataset_id (int): ID of the dataset to delete
        
    Returns:
        bool: True if successful
    """
    try:
        # Delete column metadata
        session.execute(
            columns.delete().where(columns.c.dataset_id == dataset_id)
        )
        
        # Delete dataset entry
        session.execute(
            datasets.delete().where(datasets.c.id == dataset_id)
        )
        
        # Delete the data table
        table_name = f"data_{dataset_id}"
        session.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        session.commit()
        return True
        
    except Exception as e:
        session.rollback()
        print(f"Error deleting dataset: {e}")
        return False

def save_analysis(dataset_id, name, analysis_type, configuration, insights, description=""):
    """
    Save an analysis configuration
    
    Args:
        dataset_id (int): ID of the dataset
        name (str): Name for the analysis
        analysis_type (str): Type of analysis
        configuration (dict): Analysis configuration
        insights (list): List of insights
        description (str): Description of the analysis
        
    Returns:
        int: ID of the saved analysis
    """
    try:
        # Convert configuration and insights to JSON strings
        import json
        config_json = json.dumps(configuration)
        insights_json = json.dumps(insights)
        
        # Check if analysis with this name already exists
        stmt = select(saved_analysis).where(
            (saved_analysis.c.dataset_id == dataset_id) & 
            (saved_analysis.c.name == name)
        )
        result = session.execute(stmt).fetchone()
        
        if result:
            # Update existing analysis
            analysis_id = result[0]
            session.execute(
                saved_analysis.update().where(saved_analysis.c.id == analysis_id).values(
                    created_at=datetime.now(),
                    analysis_type=analysis_type,
                    configuration=config_json,
                    insights=insights_json,
                    description=description
                )
            )
        else:
            # Insert new analysis
            result = session.execute(
                saved_analysis.insert().values(
                    dataset_id=dataset_id,
                    name=name,
                    description=description,
                    analysis_type=analysis_type,
                    configuration=config_json,
                    insights=insights_json
                )
            )
            analysis_id = result.inserted_primary_key[0]
        
        session.commit()
        return analysis_id
        
    except Exception as e:
        session.rollback()
        print(f"Error saving analysis: {e}")
        return None

def get_saved_analyses(dataset_id=None):
    """
    Get saved analyses
    
    Args:
        dataset_id (int, optional): Filter by dataset ID
        
    Returns:
        pandas.DataFrame: DataFrame with analysis information
    """
    try:
        if dataset_id:
            stmt = select(saved_analysis).where(saved_analysis.c.dataset_id == dataset_id)
        else:
            stmt = select(saved_analysis)
            
        results = session.execute(stmt).fetchall()
        
        if results:
            return pd.DataFrame(results, columns=saved_analysis.c.keys())
        else:
            return pd.DataFrame(columns=saved_analysis.c.keys())
            
    except Exception as e:
        print(f"Error fetching saved analyses: {e}")
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=['id', 'dataset_id', 'name', 'description', 'created_at', 
                                     'analysis_type', 'configuration', 'insights'])

def load_analysis(analysis_id):
    """
    Load an analysis
    
    Args:
        analysis_id (int): ID of the analysis to load
        
    Returns:
        tuple: (analysis_info, configuration, insights)
    """
    try:
        # Get analysis info
        stmt = select(saved_analysis).where(saved_analysis.c.id == analysis_id)
        analysis_info = session.execute(stmt).fetchone()
        
        if not analysis_info:
            raise ValueError(f"Analysis with ID {analysis_id} not found")
        
        # Convert JSON strings back to Python objects
        import json
        configuration = json.loads(analysis_info['configuration'])
        insights = json.loads(analysis_info['insights'])
        
        return analysis_info, configuration, insights
        
    except Exception as e:
        print(f"Error loading analysis: {e}")
        # Return empty analysis
        return {}, {}, []

def delete_analysis(analysis_id):
    """
    Delete an analysis from the database
    
    Args:
        analysis_id (int): ID of the analysis to delete
        
    Returns:
        bool: True if successful
    """
    try:
        # Delete analysis entry
        session.execute(
            saved_analysis.delete().where(saved_analysis.c.id == analysis_id)
        )
        
        session.commit()
        return True
        
    except Exception as e:
        session.rollback()
        print(f"Error deleting analysis: {e}")
        return False