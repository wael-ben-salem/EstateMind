import os
from datetime import datetime, timezone
import boto3

MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BUCKET = "tayara-raw"
LOCAL_FILE = "/opt/spark_app/data/TayaraDataDetailed.json"


def main():
    session = boto3.session.Session()
    s3 = session.client(
        service_name="s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    key = f"raw/tayara/scrape_date={today}/TayaraDataDetailed.json"

    s3.upload_file(LOCAL_FILE, BUCKET, key)
    print(f"Uploaded to s3://{BUCKET}/{key}")


if __name__ == "__main__":
    main()