from airflow import DAG
from airflow.providers.google.cloud.transfers.drive_to_gcs import DriveToGCSOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago


DAG_ID = "upload_csv_to_gcs"
GCS_BUCKET_NAME = "capstonebucket01"
GCP_PROJECT_ID = "cap01project"
DRIVE_FOLDER_ID = "13A8GUxwIBJq95f_Lz5ACx33WqVTu6IVQ"  # The Google Drive folder containing the CSV files
START_DATE = days_ago(1)
SCHEDULE_INTERVAL = None  # Set your desired schedule interval


with DAG(
    dag_id=DAG_ID,
    start_date=START_DATE,
    schedule_interval=SCHEDULE_INTERVAL,
    catchup=False,
    tags=["gcp"],
) as dag:


    start_task = DummyOperator(task_id="start_task")

    # Task to transfer "movie_review.csv" from Google Drive to GCS
    upload_movie_review = DriveToGCSOperator(
        task_id="upload_movie_review",
        project_id=GCP_PROJECT_ID,
        bucket_name=GCS_BUCKET_NAME,
        object_name="movie_review.csv",
        folder_id=DRIVE_FOLDER_ID,
        drive_conn_id="google_cloud_default",
        gcs_conn_id="google_cloud_default",
    )

    # Task to transfer "log_reviews.csv" from Google Drive to GCS
    upload_log_reviews = DriveToGCSOperator(
        task_id="upload_log_reviews",
        project_id=GCP_PROJECT_ID,
        bucket_name=GCS_BUCKET_NAME,
        object_name="log_reviews.csv",
        folder_id=DRIVE_FOLDER_ID,
        drive_conn_id="google_cloud_default",
        gcs_conn_id="google_cloud_default",
    )

    end_task = DummyOperator(task_id="end_task")

    start_task >> [upload_movie_review, upload_log_reviews] >> end_task

