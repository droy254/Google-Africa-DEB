from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime

# Define your DAG
with DAG("data_warehouse_setup_dag", start_date=datetime(2023, 1, 1), schedule_interval=None) as dag:

    # Create dim tables
    create_dim_date_table = PostgresOperator(
        task_id="create_dim_date_table",
        sql="""
            CREATE TABLE dim_date (
                id_dim_date SERIAL PRIMARY KEY,
                log_date DATE,
                day VARCHAR(10),
                month VARCHAR(10),
                year VARCHAR(4),
                season VARCHAR(10)
            );
        """
    )

    create_dim_devices_table = PostgresOperator(
        task_id="create_dim_devices_table",
        sql="""
            CREATE TABLE dim_devices (
                id_dim_devices SERIAL PRIMARY KEY,
                device VARCHAR(50)
            );
        """
    )

    create_dim_location_table = PostgresOperator(
        task_id="create_dim_location_table",
        sql="""
            CREATE TABLE dim_location (
                id_dim_location SERIAL PRIMARY KEY,
                location VARCHAR(100)
            );
        """
    )

    create_dim_os_table = PostgresOperator(
        task_id="create_dim_os_table",
        sql="""
            CREATE TABLE dim_os (
                id_dim_os SERIAL PRIMARY KEY,
                os VARCHAR(50)
            );
        """
    )

    create_dim_browser_table = PostgresOperator(
        task_id="create_dim_browser_table",
        sql="""
            CREATE TABLE dim_browser (
                id_dim_browser SERIAL PRIMARY KEY,
                browser VARCHAR(50)
            );
        """
    )

    # Create fact table
    create_fact_movie_analytics_table = PostgresOperator(
        task_id="create_fact_movie_analytics_table",
        sql="""
            CREATE TABLE fact_movie_analytics (
                customerid INTEGER,
                id_dim_devices INTEGER,
                id_dim_location INTEGER,
                id_dim_os INTEGER,
                id_dim_browser INTEGER,
                amount_spent DECIMAL(18, 5),
                review_score INTEGER,
                review_count INTEGER,
                insert_date DATE
            );
        """
    )

    # Set up dependencies
    [
        create_dim_date_table, create_dim_devices_table, create_dim_location_table,
        create_dim_os_table, create_dim_browser_table, create_fact_movie_analytics_table
    ]

