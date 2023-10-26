#############SAMPLE 2

from airflow import DAG
from airflow.providers.google.cloud.transfers.postgres_to_gcs import PostgresToGoogleCloudStorageOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GoogleCloudStorageToBigQueryOperator
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType
from xml.etree import ElementTree as ET
import pyspark.sql.functions as F

# Constants
GCP_CONN_ID = "google_cloud_default"
GCS_BUCKET_NAME = "cap_bucket"
POSTGRES_CONN_ID = "google_cloud_sql"

# Define the schema for XML parsing
xml_schema = StructType([
    StructField("logDate", StringType(), True),
    StructField("device", StringType(), True),
    StructField("location", StringType(), True),
    StructField("os", StringType(), True),
    StructField("ipAddress", StringType(), True),
    StructField("phoneNumber", StringType(), True)
])

# DAG definition
with DAG(
    dag_id="STAGE_Area",
    schedule_interval=None,  # Set to your desired schedule
    start_date=datetime(2023, 10, 26),
    tags=["Wizeline", "Capstone"],
) as dag:

    # Upload raw_area.user_purchase table from PostgreSQL DB to Google Cloud Bucket
    upload_user_purchase_to_cloud_bucket = PostgresToGoogleCloudStorageOperator(
        task_id="upload_user_purchase_to_cloud_bucket",
        sql="SELECT * FROM raw_area.user_purchase",  # You need to specify the query here
        bucket=GCS_BUCKET_NAME,
        filename="user_purchase",  # Specify the desired filename
    )

    # Create a Spark task for transforming movie_review.csv
    def transform_movie_review():
        # Load the CSV file from GCS
        spark = SparkSession.builder.appName(PYSPARK_APP_NAME).getOrCreate()
        df = spark.read.csv(f"gs://{GCS_BUCKET_NAME}/movie_review.csv", header=True)

        # Transformations
        df = df.withColumn("positive_review", F.when(col("review_str").contains("good"), 1).otherwise(0))
        df = df.withColumn("insert_date", F.current_date())

        # Select the desired columns
        df = df.select("cid", "positive_review", "review_id", "insert_date")

        # Save the transformed data back to GCS
        df.write.csv(f"gs://{GCS_BUCKET_NAME}/classified_movie_review", header=True, mode="overwrite")

    # Create a PythonOperator task to transform movie_review.csv
    transform_movie_review_task = PythonOperator(
        task_id="transform_movie_review",
        python_callable=transform_movie_review,
    )

    # Create a Spark task for transforming log_reviews.csv
    def transform_log_reviews():
        # Load the CSV file from GCS
        df = spark.read.csv(f"gs://{GCS_BUCKET_NAME}/log_reviews.csv", header=True)

        # Transformation for breaking down the XML structure
        df = df.withColumn("parsed_log", from_json(col("log"), xml_schema))

        # Explode the parsed_log column to generate separate columns for each of the parsed fields
        df = df.withColumn("parsed_log", explode(col("parsed_log")))

        # Rename the parsed fields to match the desired column names
        df = df.select(
            col("id_review").alias("log_id"),
            col("parsed_log.logDate").alias("log_date"),
            col("parsed_log.device"),
            col("parsed_log.os"),
            col("parsed_log.location"),
            col("parsed_log.ipAddress").alias("ip"),
            col("parsed_log.phoneNumber").alias("phone_number")
        )

        # Save the transformed data back to GCS
        df.write.csv(f"gs://{GCS_BUCKET_NAME}/log_reviews", header=True, mode="overwrite")

    # Create a PythonOperator task to transform log_reviews.csv
    transform_log_reviews_task = PythonOperator(
        task_id="transform_log_reviews",
        python_callable=transform_log_reviews,
    )

    # Set up task dependencies
    upload_user_purchase_to_cloud_bucket >> transform_movie_review_task >> transform_log_reviews_task

