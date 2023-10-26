#######################33SAMPLE 1
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.providers.google.cloud.transfers.postgres_to_gcs import PostgresToGoogleCloudStorageOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from pyspark.sql import SparkSession
from datetime import datetime
from pyspark.sql.functions import col, when
from pyspark.sql.types import StringType, StructType, StructField

# Define DAG parameters
DAG_ID = "STAGE_Area"
GCP_CONN_ID = "google_cloud_default"
GCS_BUCKET_NAME = "cap_bucket"
POSTGRES_CONN_ID = "google_cloud_sql"
PYSPARK_APP_NAME = "ETLJob"
PYSPARK_APP_PATH = "/path/to/your/pyspark_script.py"  # Replace with the actual path

# Create DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 10, 26),
    'retries': 1,
}

dag = DAG(
    dag_id=DAG_ID,
    default_args=default_args,
    description='ETL DAG for STAGE Area',
    schedule_interval=None,  # Set to your desired schedule
    catchup=False,  # Set to True if you want to run backfill
    tags=["Wizeline", "Capstone"],
)

# Define SparkSession
spark = SparkSession.builder.appName(PYSPARK_APP_NAME).getOrCreate()

# Create Spark task
spark_task = SparkSubmitOperator(
    task_id="spark_task",
    conn_id="spark_default",
    application=PYSPARK_APP_PATH,
    application_args=[
        "--bucket", GCS_BUCKET_NAME,
        "--postgres_conn_id", POSTGRES_CONN_ID
    ],
    dag=dag,
)

# Define the PySpark script in a separate .py file and provide the path above.
# In your PySpark script, load the data from PostgreSQL and perform the transformations.

# Transformation for movie_review.csv
movie_review_df = spark.read.csv("movie_review.csv", header=True)
movie_review_df = movie_review_df.withColumn("positive_review", when(col("review_str").like("%good%"), 1).otherwise(0))
movie_review_df = movie_review_df.withColumn("insert_date", current_timestamp())
movie_review_df = movie_review_df.select("cid", "positive_review", "review_id", "insert_date")

# Transformation for log_reviews.csv
log_reviews_df = spark.read.csv("log_reviews.csv", header=True)
log_reviews_df = log_reviews_df.withColumn("log",
    from_json(col("log"), StructType([
        StructField("logDate", StringType(), True),
        StructField("device", StringType(), True),
        StructField("location", StringType(), True),
        StructField("os", StringType(), True),
        StructField("ipAddress", StringType(), True),
        StructField("phoneNumber", StringType(), True)
    ]))
)
log_reviews_df = log_reviews_df.select("id_review", "log.logDate", "log.device", "log.os", "log.location", "log.ipAddress", "log.phoneNumber")

# Save the transformed DataFrames to Google Cloud Storage
movie_review_df.write.mode("overwrite").csv(f"gs://{GCS_BUCKET_NAME}/classified_movie_review")
log_reviews_df.write.mode("overwrite").csv(f"gs://{GCS_BUCKET_NAME}/log_reviews")

# Create task dependencies
start_task >> spark_task

# You also need to create the necessary connections in Airflow:
# 1. GCP_CONN_ID for Google Cloud (Service Account key file)
# 2. POSTGRES_CONN_ID for PostgreSQL connection

# Additionally, you need to create the PySpark script at the specified path with the necessary transformations.

# Ensure that the necessary libraries are installed in your Airflow environment for PySpark operations.

#################SAMPLE 2

from airflow import DAG
from airflow.providers.google.cloud.operators.postgres_to_gcs import PostgresToGCSOperator
from airflow.providers.google.cloud.operators.gcs import GoogleCloudStorageOperator
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import pyspark.sql.functions as F

# Constants
GCP_CONN_ID = "google_cloud_default"
GCS_BUCKET_NAME = "cap_bucket"
POSTGRES_CONN_ID = "google_cloud_sql"

# DAG definition
with DAG(
    dag_id="STAGE Area",
    schedule_interval="@once",
    start_date=datetime(2023, 10, 26),
    tags=["Wizeline", "Capstone"],
) as dag:

    # Upload raw_area.user_purchase table from PostgreSQL DB to Google Cloud Bucket
    upload_user_purchase_to_cloud_bucket = PostgresToGCSOperator(
        task_id="upload_user_purchase_to_cloud_bucket",
        postgres_conn_id=POSTGRES_CONN_ID,
        bucket=GCS_BUCKET_NAME,
        table="raw_area.user_purchase",
        destination_object_name="user_purchase",
    )

    # Transform movie_review.csv in Google Cloud Bucket and save it as classified_movie_review
    def transform_movie_review(bucket_name, source_file, destination_file):
        """
        Transform movie_review.csv in Google Cloud Bucket and save it as classified_movie_review
        """

        # Read the movie_review.csv file from Google Cloud Bucket
        spark = pyspark.sql.SparkSession.builder.getOrCreate()
        df = spark.read.csv(f"gs://{bucket_name}/{source_file}", header=True)

        # Add a column called positive_review to indicate whether the review is positive or not
        df = df.withColumn(
            "positive_review",
            F.when(F.col("review_str").contains("good"), 1).otherwise(0),
        )

        # Add a column called insert_date to indicate when the job was run
        df = df.withColumn("insert_date", F.current_date())

        # Save the transformed data to Google Cloud Bucket
        df.write.csv(f"gs://{bucket_name}/{destination_file}", header=True, mode="overwrite")

    # Create a PythonOperator task to transform the movie_review.csv file
    transform_movie_review = PythonOperator(
        task_id="transform_movie_review",
        python_callable=transform_movie_review,
        op_kwargs={"bucket_name": GCS_BUCKET_NAME, "source_file": "movie_review.csv", "destination_file": "classified_movie_review"},
    )

    # Transform log_reviews.csv in Google Cloud Bucket and save it as log_reviews
    def transform_log_reviews(bucket_name, source_file, destination_file):
        """
        Transform log_reviews.csv in Google Cloud Bucket and save it as log_reviews
        """

        # Read the log_reviews.csv file from Google Cloud Bucket
        spark = pyspark.sql.SparkSession.builder.getOrCreate()
        df = spark.read.csv(f"gs://{bucket_name}/{source_file}", header=True)

        # Break down the log column using any xml library to bring out the columns: [log_date, device, os, location, ip, phone_number]
        from xml.etree import ElementTree as ET

        def parse_log(xml_string):
            root = ET.fromstring(xml_string)
            log_date = root.find("logDate").text
            device = root.find("device").text
            os = root.find("os").text
            location = root.find("location").text
            ip = root.find("ipAddress").text
            phone_number = root.find("phoneNumber").text
            return log_date, device, os, location, ip, phone_number

        df = df.withColumn("parsed_log", F.udf(parse_log, F.StringType())(F.col("log")))

        # Explode the parsed_log column to generate separate columns for each of the parsed fields
        df = df.explode("parsed_log")
        
        # Rename the parsed fields to the desired column names
	df = df.select(
	    F.col("parsed_log")[0].alias("log_date"),
	    F.col("parsed_log")[1].alias("device"),
	    F.col("parsed_log")[2].alias("os"),
	    F.col("parsed_log")[3].alias("location"),
	    F.col("parsed_log")[4].alias("ip"),
	    F.col("parsed_log")[5].alias("phone_number"),
	)

	# Generate a log_id column from the id_review column
	df = df.withColumn("log_id", F.monotonically_increasing_id())

	# Save the transformed data to Google Cloud Bucket
	df.write.csv(f"gs://{bucket_name}/{destination_file}", header=True, mode="overwrite")



###################SAMPLE 3

from airflow import DAG
from airflow.providers.google.cloud.operators.postgres_to_gcs import PostgresToGCSOperator
from airflow.providers.google.cloud.operators.gcs import GoogleCloudStorageToBigQueryOperator  # Updated import
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import pyspark.sql.functions as F

# Constants
GCP_CONN_ID = "google_cloud_default"
GCS_BUCKET_NAME = "cap_bucket"
POSTGRES_CONN_ID = "google_cloud_sql"

# DAG definition
with DAG(
    dag_id="STAGE_Area",
    schedule_interval=None,  # Set to your desired schedule
    start_date=datetime(2023, 10, 26),
    tags=["Wizeline", "Capstone"],
) as dag:

    # Upload raw_area.user_purchase table from PostgreSQL DB to Google Cloud Bucket
    upload_user_purchase_to_cloud_bucket = PostgresToGCSOperator(
        task_id="upload_user_purchase_to_cloud_bucket",
        sql="SELECT * FROM raw_area.user_purchase",  # You need to specify the query here
        bucket=GCS_BUCKET_NAME,
        filename="user_purchase.csv",  # Specify the desired filename
    )

    # Transform movie_review.csv in Google Cloud Bucket and save it as classified_movie_review
    def transform_movie_review(bucket_name, source_file, destination_file):
        """
        Transform movie_review.csv in Google Cloud Bucket and save it as classified_movie_review
        """

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

    # Create a PythonOperator task to transform the movie_review.csv file
    transform_movie_review = PythonOperator(
        task_id="transform_movie_review",
        python_callable=transform_movie_review,
        op_kwargs={"bucket_name": GCS_BUCKET_NAME, "source_file": "movie_review.csv", "destination_file": "classified_movie_review.csv"},
    )

    # Transform log_reviews.csv in Google Cloud Bucket and save it as log_reviews
    def transform_log_reviews(bucket_name, source_file, destination_file):
        """
        Transform log_reviews.csv in Google Cloud Bucket and save it as log_reviews
        """

        # Load the CSV file from GCS
        df = spark.read.csv(f"gs://{bucket_name}/{source_file}", header=True)

        # Transformation for breaking down the XML structure
        # Implement your XML parsing logic here

        # Save the transformed data back to GCS
        df.write.csv(f"gs://{bucket_name}/{destination_file}", header=True, mode="overwrite")

    # Create a PythonOperator task to transform the log_reviews.csv file
    transform_log_reviews = PythonOperator(
        task_id="transform_log_reviews",
        python_callable=transform_log_reviews,
        op_kwargs={"bucket_name": GCS_BUCKET_NAME, "source_file": "log_reviews.csv", "destination_file": "log_reviews.csv"},
    )

    # Set up task dependencies
    upload_user_purchase_to_cloud_bucket >> transform_movie_review >> transform_log_reviews

    # You need to provide the actual transformation logic for parsing the XML structure in `transform_log_reviews`.

