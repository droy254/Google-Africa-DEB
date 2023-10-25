from pyspark.sql import SparkSession
from pyspark.ml.feature import Tokenizer, StopWordsRemover
from pyspark.sql.functions import col, when
from pyspark.sql.types import IntegerType, BooleanType
from datetime import datetime

# Initialize a Spark session
spark = SparkSession.builder.appName("MovieReviewTransform").getOrCreate()

# Load the movie_review.csv file from Google Cloud Storage
movie_review_df = spark.read.csv("gs://your_bucket_name/RAW/movie_review.csv", header=True)

# Tokenize the review_str column to create a list of words
tokenizer = Tokenizer(inputCol="review_str", outputCol="review_tokens")
movie_review_df = tokenizer.transform(movie_review_df)

# Optionally, remove stop words using StopWordsRemover
stopwords_remover = StopWordsRemover(inputCol="review_tokens", outputCol="filtered_tokens")
movie_review_df = stopwords_remover.transform(movie_review_df)

# Look for data that contain the word "good" and create a positive_review column
movie_review_df = movie_review_df.withColumn("positive_review", when(col("review_str").like("%good%"), 1).otherwise(0))

# Add an insert_date column with the current timestamp
movie_review_df = movie_review_df.withColumn("insert_date", col("insert_date").cast(IntegerType()))

# Convert boolean positive_review column to integer
movie_review_df = movie_review_df.withColumn("positive_review", col("positive_review").cast(IntegerType()))

# Select the relevant columns for the final output
movie_review_df = movie_review_df.select("customer_id", "positive_review", "review_id")

# Write the transformed data to a new file in the STAGE area
movie_review_df.write.csv("gs://your_bucket_name/STAGE/movie_review_transformed.csv", header=True, mode="overwrite")

# Stop the Spark session
spark.stop()

