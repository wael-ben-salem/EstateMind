FROM apache/airflow:3.1.0

USER root

RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    curl \
    procps \
    bash \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

RUN mkdir -p /opt/airflow/jars && \
    curl -L -o /opt/airflow/jars/hadoop-aws-3.3.4.jar \
      https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    curl -L -o /opt/airflow/jars/aws-java-sdk-bundle-1.12.262.jar \
      https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar

USER airflow

RUN pip install --no-cache-dir \
    pyspark==3.5.8 \
    sqlalchemy \
    psycopg2-binary \
    pandas \
    scrapy \
    boto3 \
    openai \
    scikit-learn \
    joblib \
    xgboost