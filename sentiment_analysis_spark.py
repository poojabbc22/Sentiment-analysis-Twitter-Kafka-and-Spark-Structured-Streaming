from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql import functions as F
from textblob import TextBlob
from pyspark.streaming.kafka import KafkaUtils
from pyspark.sql.functions import explode
from pyspark.sql.functions import split


from pyspark.sql.types import TimestampType, StringType, StructType, StructField
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json,col

def preprocessing(lines):
    words = df1.select(explode(split(df1.text, " ")).alias("word"))
    # words = lines.select(explode(split(lines.value, "t_end")).alias("word"))
    words = words.na.replace('', None)
    words = words.na.drop()
    words = words.withColumn('word', F.regexp_replace('word', r'http\S+', ''))
    words = words.withColumn('word', F.regexp_replace('word', '@\w+', ''))
    words = words.withColumn('word', F.regexp_replace('word', '#', ''))
    words = words.withColumn('word', F.regexp_replace('word', 'RT', ''))
    words = words.withColumn('word', F.regexp_replace('word', ':', ''))
    return words

# text classification
def polarity_detection(text):
    return TextBlob(text).sentiment.polarity
def subjectivity_detection(text):
    return TextBlob(text).sentiment.subjectivity
def text_classification(words):
    # polarity detection
    polarity_detection_udf = udf(polarity_detection, StringType())
    words = words.withColumn("polarity", polarity_detection_udf("word"))
    # subjectivity detection
    subjectivity_detection_udf = udf(subjectivity_detection, StringType())
    words = words.withColumn("subjectivity", subjectivity_detection_udf("word"))
    return words

if __name__ == "__main__":
    # create Spark session
    spark = SparkSession.builder.appName("TwitterSentimentAnalysis").getOrCreate()
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "twitter") \
        .load()

    mySchema = StructType([StructField("text", StringType(), True)])
    values = df.select(from_json(df.value.cast("string"), mySchema).alias("test"))
    df1 = values.select("test.*")
    # words = df1.select(explode(split(df1.text, " ")).alias("word"))
    # read the tweet data from socket
    # lines = spark.readStream.format("socket").option("host", "0.0.0.0").option("port", 5555).load()
    # Preprocess the data
    words = preprocessing(df1)
    # text classification to define polarity and subjectivity
    words = text_classification(words)

    words = words.repartition(1)
    query = words.writeStream.queryName("all_tweets")\
        .outputMode("append").format("console")\
    .start()

    query.awaitTermination()

    # option("path", "./parc") \
    #     .option("checkpointLocation", "./check") \
    #     .trigger(processingTime='60 seconds').start()