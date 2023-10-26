from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.providers.google.cloud.operators.postgres import PostgresOperator
from airflow.providers.google.cloud.operators.gcs import GoogleCloudStorageOperator

# Define DAG parameters
DAG_ID = "RAW_Area"
SCHEDULE_INTERVAL = "@once"
POSTGRES_CONN_ID = "google_cloud_sql"
GCS_CONN_ID = "google_cloud_default"
GCS_BUCKET_NAME = "cap_bucket"

# Define Google Drive file paths
USER_PURCHASE_CSV_PATH = "https://drive.google.com/uc?export=download&id=1w7WdZWmoUTJ0m86CCoRqZ8NDj7_U69qP"
LOG_REVIEWS_CSV_PATH = "https://drive.google.com/uc?export=download&id=1CuXwQfpsiXddKm1yQOZVpoUk4Kf9o-U4"
MOVIE_REVIEW_CSV_PATH = "https://drive.google.com/uc?export=download&id=1iFZOCsvkBt5nYsqhx_CXwdFz3J3Ttlqo"

# Create DAG
with DAG(
    dag_id=DAG_ID,
    schedule_interval=SCHEDULE_INTERVAL,
    start_date=datetime(2023, 10, 26),
    tags=["Wizeline", "Capstone"],
) as dag:

    # Start workflow
    start_workflow = DummyOperator(task_id="start_workflow")

    # Create PostgreSQL table
    create_table_entity = PostgresOperator(
        task_id="create_table_entity",
        postgres_conn_id=POSTGRES_CONN_ID,
        sql=f"""
            CREATE SCHEMA raw_area;
            CREATE TABLE raw_area.user_purchase (
                invoice_number varchar(10),
                stock_code varchar(20),
                detail varchar(1000),
                quantity int,
                invoice_date timestamp,
                unit_price numeric(8,3),
                customer_id int,
                country varchar(20)
            );
        """,
    )

    # Clear PostgreSQL table
    clear_table = PostgresOperator(
        task_id="clear_table",
        postgres_conn_id=POSTGRES_CONN_ID,
        sql=f"TRUNCATE TABLE raw_area.user_purchase",
    )

    # Continue process
    continue_process = DummyOperator(task_id="continue_process")

    # Ingest user_purchase.csv from Google Drive to PostgreSQL
    # Alternative sql = f"COPY raw_area.user_purchase FROM '{USER_PURCHASE_CSV_PATH}' CSV DELIMITER ',' HEADER"
    upload_user_purchase_to_postgres = PostgresOperator(
        task_id="upload_user_purchase_to_postgres",
        postgres_conn_id=POSTGRES_CONN_ID,
        sql=f"COPY {POSTGRES_CONN_ID}.raw_area.user_purchase FROM {USER_PURCHASE_CSV_PATH} DELIMITER ','",
    )

    # Ingest log_reviews.csv from Google Drive to Cloud Bucket
    upload_log_reviews_to_cloud_bucket = GoogleCloudStorageOperator(
        task_id="upload_log_reviews_to_cloud_bucket",
        google_cloud_conn_id=GCS_CONN_ID,
        bucket=GCS_BUCKET_NAME,
        object="log_reviews.csv", 
        source=LOG_REVIEWS_CSV_PATH,
    )

    # Ingest movie_review.csv from Google Drive to Cloud Bucket
    upload_movie_review_to_cloud_bucket = GoogleCloudStorageOperator(
        task_id="upload_movie_review_to_cloud_bucket",
        google_cloud_conn_id=GCS_CONN_ID,
        bucket=GCS_BUCKET_NAME,
        object="movie_review.csv", 
        source=MOVIE_REVIEW_CSV_PATH,
    )

    # Set task dependencies
    start_workflow >> create_table_entity >> clear_table >> [
        upload_user_purchase_to_postgres,
        upload_log_reviews_to_cloud_bucket,
        upload_movie_review_to_cloud_bucket,
    ]


