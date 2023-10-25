# Import necessary Airflow modules
from airflow import DAG
from airflow.providers.google.cloud.operators.gcs import GCSToLocalFilesystemOperator, GoogleCloudStorageToGoogleCloudStorageOperator
from airflow.providers.google.cloud.transfers.sql import GCSToBigQueryOperator
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from airflow.operators.dummy_operator import DummyOperator

# Import any other required libraries

# Define default_args for the DAGs
default_args = {
    'owner': 'david_obondo',
    'depends_on_past': False,
    'start_date': days_ago(0),
    'retries': 1,
}

# Define your DAGs
with DAG('data_pipeline', default_args=default_args, schedule_interval=None) as dag:

    # Define a task to download user_purchase.csv from Google Drive
    download_user_purchase = GCSToLocalFilesystemOperator(
        task_id='download_user_purchase',
        bucket_name='cap_bucket',
        object_name='user_purchase.csv',
        filename='/path/to/store/user_purchase.csv',
    )

    # Define a task to upload movie_review.csv and log_reviews.csv to GCS
    upload_movie_reviews = GoogleCloudStorageToGoogleCloudStorageOperator(
        task_id='upload_movie_reviews',
        source_bucket='your_source_bucket',
        source_object='movie_review.csv',
        destination_bucket='your_destination_bucket',
        destination_object='RAW/movie_review.csv',
    )

    upload_log_reviews = GoogleCloudStorageToGoogleCloudStorageOperator(
        task_id='upload_log_reviews',
        source_bucket='your_source_bucket',
        source_object='log_reviews.csv',
        destination_bucket='your_destination_bucket',
        destination_object='RAW/log_reviews.csv',
    )

    # Define a Python task for data transformation (using Spark)
    def transform_data():
        # Your data transformation code using PySpark goes here

    data_transformation = PythonOperator(
        task_id='data_transformation',
        python_callable=transform_data,
    )

    # Define a task to load data into PostgreSQL from GCS
    load_to_postgresql = GCSToBigQueryOperator(
        task_id='load_to_postgresql',
        schema='your_schema',
        table='your_table',
        bucket_name='your_bucket',
        source_objects=['RAW/movie_review.csv', 'RAW/log_reviews.csv'],
        source_format='CSV',
        write_disposition='WRITE_TRUNCATE',
    )

    # Set up the task dependencies
    download_user_purchase >> [upload_movie_reviews, upload_log_reviews]
    [upload_movie_reviews, upload_log_reviews] >> data_transformation
    data_transformation >> load_to_postgresql

# Define another DAG for creating DW schema
with DAG('create_dw_schema', default_args=default_args, schedule_interval=None) as dag:
    
    # Define tasks for creating dimension and fact tables
    create_fact_table = GCSToBigQueryOperator(
        task_id='create_fact_table',
        schema='your_schema',
        table='fact_movie_analytics',
        bucket_name='your_bucket',
        source_objects=['your_fact_data.csv'],
        source_format='CSV',
        write_disposition='WRITE_TRUNCATE',
    )

    create_dim_tables = GCSToBigQueryOperator(
        task_id='create_dim_tables',
        schema='your_schema',
        table='dim_date',
        bucket_name='your_bucket',
        source_objects=['your_dim_data.csv'],
        source_format='CSV',
        write_disposition='WRITE_TRUNCATE',
    )

    # Define IAM roles

    # Set up task dependencies
    create_fact_table >> create_dim_tables

# Define a DAG that orchestrates the entire process
with DAG('data_pipeline_orchestrator', default_args=default_args, schedule_interval=None) as dag:
    start = DummyOperator(task_id='start')
    end = DummyOperator(task_id='end')

    # Set up dependencies between DAGs
    download_user_purchase >> [upload_movie_reviews, upload_log_reviews] >> data_transformation >> load_to_postgresql
    create_fact_table >> create_dim_tables

    start >> download_user_purchase
    [load_to_postgresql, create_dim_tables] >> end

