
###################SAMPLE 1

from airflow import DAG
from airflow.providers.google.cloud.operators.postgres_to_gcs import PostgresToGCSOperator
from airflow.providers.google.cloud.operators.gcs import GoogleCloudStorageToBigQueryOperator
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql import functions as F

# Constants
GCP_CONN_ID = "google_cloud_default"
GCS_BUCKET_NAME = "cap_bucket"
POSTGRES_CONN_ID = "google_cloud_sql"

# Create a Spark session
spark = SparkSession.builder.appName("my_app").getOrCreate()

# Define the parse_log function
def parse_log(log_data):
    # Implement the logic to parse XML data here
    # Example: You can use libraries like BeautifulSoup for XML parsing
    pass

# DAG definition
with DAG(
    dag_id="STAGE_Area",
    schedule_interval='@once',  
    start_date=datetime(2023, 10, 26),
    tags=["Wizeline", "Capstone"],
) as dag:

    # Upload raw_area.user_purchase table from PostgreSQL DB to Google Cloud Bucket
    upload_user_purchase_to_cloud_bucket = PostgresToGCSOperator(
        task_id="upload_user_purchase_to_cloud_bucket",
        sql="SELECT * FROM raw_area.user_purchase",
        bucket=GCS_BUCKET_NAME,
        filename="user_purchase.csv",
        postgres_conn_id=POSTGRES_CONN_ID,
        google_cloud_storage_conn_id=GCP_CONN_ID
    )

    # Create a PythonOperator task to transform the movie_review.csv file
    def transform_movie_review(bucket_name, source_file, destination_file):
        # Load the CSV file from GCS
        df = spark.read.csv(f"gs://{bucket_name}/{source_file}", header=True)

        # Transformations
        df = df.withColumn(
            "positive_review",
            F.when(F.col("review_str").contains("good"), 1).otherwise(0),
        )
        df = df.withColumn("insert_date", F.current_date())

        # Select the desired columns
        df = df.select("cid", "positive_review", "review_id", "insert_date")

        # Save the transformed data back to GCS
        df.write.csv(f"gs://{bucket_name}/{destination_file}", header=True, mode="overwrite")

    transform_movie_review_task = PythonOperator(
        task_id="transform_movie_review",
        python_callable=transform_movie_review,
        op_kwargs={"bucket_name": GCS_BUCKET_NAME, "source_file": "movie_review.csv", "destination_file": "classified_movie_review.csv"},
    )

    # Create a PythonOperator task to transform the log_reviews.csv file
    def transform_log_reviews(bucket_name, source_file, destination_file):
        # Load the CSV file from GCS
        df = spark.read.csv(f"gs://{bucket_name}/{source_file}", header=True)

        # Create a UDF to parse the XML structure in the log column
        parse_log_udf = udf(parse_log)

        # Explode the log column to generate separate columns for each of the parsed fields
        df = df.withColumn("parsed_log", parse_log_udf(F.col("log")))

        # Rename the parsed fields to the desired column names
        df = df.select(
            F.col("id_review").alias("log_id"),
            F.col("parsed_log.log_date").alias("log_date"),
            F.col("parsed_log.device").alias("device"),
            F.col("parsed_log.os").alias("os"),
            F.col("parsed_log.location").alias("location"),
            F.col("parsed_log.browser").alias("browser"),
            F.col("parsed_log.ip").alias("ip"),
            F.col("parsed_log.phone_number").alias("phone_number"),
        )

        # Save the transformed data back to GCS
        df.write.csv(f"gs://{bucket_name}/{destination_file}", header=True, mode="overwrite")

    transform_log_reviews_task = PythonOperator(
        task_id="transform_log_reviews",
        python_callable=transform_log_reviews,
        op_kwargs={"bucket_name": GCS_BUCKET_NAME, "source_file": "log_reviews.csv", "destination_file": "log_reviews.csv"},
    )

    # Set up task dependencies
    upload_user_purchase_to_cloud_bucket >> transform_movie_review_task >> transform_log_reviews_task




