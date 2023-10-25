# Import the necessary libraries
import airflow
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.google_cloud import GoogleCloudStorageToBigQueryOperator

# Define the DAG
dag = DAG(
    dag_id="data_ingestion",
    schedule_interval="@daily",
    start_date=airflow.utils.dates.days_ago(1),
)

# Define the tasks
def ingest_user_purchase_data():
    """Ingests the user_purchase.csv file from Google Drive into the PostgreSQL database."""

    # Create a PostgreSQL connection
    conn = airflow.providers.postgres.operators.postgres.PostgresHook(
        postgres_conn_id=SQL_INSTANCE_CONNECTION_ID
    )

    # Create the PostgreSQL database table if it doesn't exist
    conn.run(
        f"""
        CREATE TABLE IF NOT EXISTS {SQL_DATABASE_NAME}.user_purchase (
            invoice_number varchar(10),
            stock_code varchar(20),
            detail varchar(1000),
            quantity int,
            invoice_date timestamp,
            unit_price numeric(8,3),
            customer_id int,
            country varchar(20)
        );
        """
    )

    # Copy the user_purchase.csv file from Google Drive to the PostgreSQL database
    conn.copy_expert(
        f"COPY {SQL_DATABASE_NAME}.user_purchase FROM STDIN WITH CSV HEADER",
        open("/tmp/user_purchase.csv", "rb"),
    )

def ingest_movie_review_data():
    """Ingests the movie_review.csv file from Google Drive into the Cloud Storage bucket."""

    # Copy the movie_review.csv file from Google Drive to the Cloud Storage bucket
    GoogleCloudStorageToBigQueryOperator(
        task_id="ingest_movie_review_data",
        bucket="cap_bucket",
        source_objects=["movie_review.csv"],
        destination_dataset="capdb",
        destination_table="movie_review",
    ).execute(dag)

def ingest_log_reviews_data():
    """Ingests the log_reviews.csv file from Google Drive into the Cloud Storage bucket."""

    # Copy the log_reviews.csv file from Google Drive to the Cloud Storage bucket
    GoogleCloudStorageToBigQueryOperator(
        task_id="ingest_log_reviews_data",
        bucket="cap_bucket",
        source_objects=["log_reviews.csv"],
        destination_dataset="capdb",
        destination_table="log_reviews",
    ).execute(dag)

# Set the task dependencies
ingest_user_purchase_data >> ingest_movie_review_data
ingest_user_purchase_data >> ingest_log_reviews_data
