from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime

# Define your DAG
with DAG("data_transformation_dag", start_date=datetime(2023, 1, 1), schedule_interval=None) as dag:

    # Submit Spark job for movie_review.csv transformation
    movie_review_transformation = SparkSubmitOperator(
        task_id="movie_review_transformation",
        application="your_spark_job.py",  # Specify your Spark job file
        application_args=["movie_reviews.csv"],
        packages="org.apache.spark:spark-avro_2.12:3.1.1",
        conn_id="spark_default"
    )

    # Submit Spark job for log_reviews.csv transformation
    log_review_transformation = SparkSubmitOperator(
        task_id="log_review_transformation",
        application="your_spark_job.py",  # Specify your Spark job file
        application_args=["log_reviews.csv"],
        packages="org.apache.spark:spark-avro_2.12:3.1.1",
        conn_id="spark_default"
    )

    # Set up dependencies
    movie_review_transformation >> log_review_transformation

