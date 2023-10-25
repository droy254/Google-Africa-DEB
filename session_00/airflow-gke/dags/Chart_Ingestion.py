from airflow import DAG
from airflow.providers.google.cloud.operators.gcs import GCSToLocalFilesystemOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.transfers.sql import PostgresOperator
from datetime import datetime
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.providers.google.cloud.transfers.gcs import GCSDownloadOperator

# Define your DAG
with DAG("data_ingestion_dag", start_date=datetime(2023, 1, 1), schedule_interval=None) as dag:
    
    # Download data from Google Drive into a storage bucket
    download_user_purchase = GCSToLocalFilesystemOperator(
        task_id="download_user_purchase",
        bucket_name="cap_bucket",
        object_name="user_purchase.csv",
        filename="/tmp/user_purchase.csv"
    )
    
    download_movie_reviews = GCSToLocalFilesystemOperator(
        task_id="download_movie_reviews",
        bucket_name="cap_bucket",
        object_name="movie_reviews.csv",
        filename="/tmp/movie_reviews.csv"
    )
    
    download_log_reviews = GCSToLocalFilesystemOperator(
        task_id="download_log_reviews",
        bucket_name="cap_bucket",
        object_name="log_reviews.csv",
        filename="/tmp/log_reviews.csv"
    )
    
    # Create the PostgreSQL table for user_purchase
    create_user_purchase_table = PostgresOperator(
        task_id="create_user_purchase_table",
        sql="""
            CREATE TABLE user_purchase (
                invoice_number VARCHAR(10),
                stock_code VARCHAR(20),
                detail VARCHAR(1000),
                quantity INT,
                invoice_date TIMESTAMP,
                unit_price NUMERIC(8, 3),
                customer_id INT,
                country VARCHAR(20)
            );
        """
    )
    
    # Set up dependencies
    download_user_purchase >> create_user_purchase_table
    download_movie_reviews
    download_log_reviews
    

