import os
from airflow import DAG
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateEmptyTableOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from datetime import datetime

# Constants
GCP_CONN_ID = "google_cloud_default"
GCS_BUCKET_NAME = "cap_bucket"
PROJECT_ID = "deb-capstone"
SCHEMA = "cap_warehouse"
GCS_PATH = f"gs://{GCS_BUCKET_NAME}/"
FACT_TABLE = "fact_movie_analytics"

# Define your DAG
with DAG(
    dag_id="DW_Area",
    schedule_interval='@once', 
    start_date=datetime(2023, 10, 26),
    tags=["Wizeline", "Capstone"],
) as dag:
    # Define your operators
    # Define a DummyOperator to start the DAG
    start_task = DummyOperator(task_id="start_task")

    # Create Fact Table
    fact_table_create = BigQueryCreateEmptyTableOperator(
        task_id="fact_table_create",
        dataset_id=SCHEMA,
        table_id=FACT_TABLE,
        project_id=PROJECT_ID,
        schema=[
            {"name": "customerid", "type": "INTEGER"},
            {"name": "id_dim_devices", "type": "INTEGER"},
            {"name": "id_dim_location", "type": "INTEGER"},
            {"name": "id_dim_os", "type": "INTEGER"},
            {"name": "id_dim_browser", "type": "INTEGER"},
            {"name": "amount_spent", "type": "FLOAT"},
            {"name": "review_score", "type": "INTEGER"},
            {"name": "review_count", "type": "INTEGER"},
            {"name": "insert_date", "type": "DATE"},
        ],
        labels={"dag_id": dag.dag_id},
    )

    # Load Fact Table: Load "user_purchase.csv" from GCS to BigQuery
    fact_table_load = GCSToBigQueryOperator(
        task_id="fact_table_load",
        bucket_name=GCS_BUCKET_NAME,
        source_objects=["user_purchase"],
        destination_project_dataset_table=f"{PROJECT_ID}:{SCHEMA}.{FACT_TABLE}",
        skip_leading_rows=1,
        source_format="CSV",
        field_delimiter=",",
        write_disposition="WRITE_TRUNCATE",
    )

    # Define a function to create dimension tables
    def create_dim_table(dim_table, schema):
        create_dim_table_task = BigQueryCreateEmptyTableOperator(
            task_id=f"create_{dim_table}_table",
            dataset_id=SCHEMA,
            table_id=dim_table,
            project_id=PROJECT_ID,
            schema=schema,
        )
        return create_dim_table_task

    # Dimension tables schema
    dim_table_schemas = {
        "dim_date": [
            {"name": "id_dim_date", "type": "INTEGER"},
            {"name": "log_date", "type": "DATE"},
            {"name": "day", "type": "STRING"},
            {"name": "month", "type": "STRING"},
            {"name": "year", "type": "STRING"},
            {"name": "season", "type": "STRING"},
        ],
        "dim_devices": [
            {"name": "id_dim_devices", "type": "INTEGER"},
            {"name": "device", "type": "STRING"},
        ],
        "dim_location": [
            {"name": "id_dim_location", "type": "INTEGER"},
            {"name": "location", "type": "STRING"},
        ],
        "dim_os": [
            {"name": "id_dim_os", "type": "INTEGER"},
            {"name": "os", "type": "STRING"},
        ],
        "dim_browser": [
            {"name": "id_dim_browser", "type": "INTEGER"},
            {"name": "browser", "type": "STRING"},
        ],
    }

    # Create dimension tables
    create_dim_tasks = {}
    for dim_table, schema in dim_table_schemas.items():
        create_dim_tasks[dim_table] = create_dim_table(dim_table, schema)

    # Set up task dependencies for creating dimension tables
    for create_dim_task in create_dim_tasks.values():
        start_task >> create_dim_task

    # Set up task dependencies for Fact Table
    start_task >> fact_table_create >> fact_table_load

    # Define DummyOperator to end the DAG
    end_task = DummyOperator(task_id="end_task")

    # Set up final task dependencies
    [create_dim_task for create_dim_task in create_dim_tasks.values()] >> end_task

    # Define relations between the fact and dimension tables
    def define_relation(fact_table, fact_column, dim_table):
        sql_query = f"""
        CREATE OR REPLACE TABLE `{PROJECT_ID}.{SCHEMA}.{fact_table}`
        AS
        SELECT
            f.*,
            d.id_dim_{dim_table} AS {fact_column}
        FROM
            `{PROJECT_ID}.{SCHEMA}.{fact_table}` f
        JOIN
            `{PROJECT_ID}.{SCHEMA}.{dim_table}` d
        ON
            f.{fact_column} = d.id_dim_{dim_table}
        """
        return sql_query

    # Add tasks to define relations
    for dim_table in dim_table_schemas.keys():
        relation_task = PythonOperator(
            task_id=f"define_{dim_table}_relation",
            python_callable=define_relation,
            op_args=[FACT_TABLE, f"id_dim_{dim_table}", dim_table],
        )
        create_dim_tasks[dim_table] >> relation_task >> fact_table_load

    # Set up final task dependencies
    [create_dim_task for create_dim_task in create_dim_tasks.values()] >> end_task


