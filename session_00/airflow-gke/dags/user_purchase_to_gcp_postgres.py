from airflow import DAG
from airflow.providers.google.cloud.operators.sql import GoogleCloudSqlOperator
from airflow.providers.google.cloud.transfers.drive_to_sql import DriveToSqlOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
from airflow.operators.sql import PostgresOperator

# General constants
DAG_ID = "upload_csv_to_sql"
STABILITY_STATE = "stable"
CLOUD_PROVIDER = "gcp"

# Other constants
GCP_PROJECT_ID = "cap01project"
SQL_INSTANCE_CONNECTION_ID = "postgress_conn"
SQL_DATABASE_NAME = "capdb"
SQL_TABLE_NAME = "user_purchase"
GCS_FILE_NAME = "user_purchase.csv"
START_DATE = days_ago(1)
SCHEDULE_INTERVAL = None  # Define your schedule interval

with DAG(
    dag_id=DAG_ID,
    start_date=START_DATE,
    schedule_interval=SCHEDULE_INTERVAL,
    catchup=False,
    tags=["gcp", "wizeline-deb", "capstone"],
) as dag:
    start_task = DummyOperator(task_id="start_task")

    # Task to create the PostgreSQL table if it doesn't exist
    create_postgres_table = GoogleCloudSqlOperator(
        task_id="create_postgres_table",
        sql=f"""
            CREATE TABLE IF NOT EXISTS {SQL_DATABASE_NAME}.{SQL_TABLE_NAME} (
                invoice_number varchar(10),
                stock_code varchar(20),
                detail varchar(1000),
                quantity int,
                invoice_date timestamp,
                unit_price numeric(8,3),
                customer_id int,
                country varchar(20)
            )
        """,
        instance=SQL_INSTANCE_CONNECTION_ID,
        gcp_conn_id="google_cloud_default",
    )

    # Task to clear the PostgreSQL table before loading data
    clear_postgres_table = PostgresOperator(
        task_id="clear_postgres_table",
        postgres_conn_id=SQL_INSTANCE_CONNECTION_ID,
        sql=f"DELETE FROM {SQL_DATABASE_NAME}.{SQL_TABLE_NAME}",
    )

    # Task to load CSV data from Google Drive to SQL PostgreSQL database
    load_csv_to_sql = DriveToSqlOperator(
        task_id="load_csv_to_sql",
        google_cloud_storage_conn_id="google_cloud_default",
        sql=SQL_INSTANCE_CONNECTION_ID,
        table=f"{SQL_DATABASE_NAME}.{SQL_TABLE_NAME}",
        file_id=GCS_FILE_NAME,
        delimiter=",",
        quotechar='"',
    )

    validate_data = PostgresOperator(
        task_id="validate_data",
        postgres_conn_id=SQL_INSTANCE_CONNECTION_ID,
        sql=f"SELECT COUNT(*) AS total_rows FROM {SQL_DATABASE_NAME}.{SQL_TABLE_NAME}",
    )

    end_task = DummyOperator(task_id="end_task")

    start_task >> create_postgres_table >> clear_postgres_table >> load_csv_to_sql >> validate_data >> end_task
