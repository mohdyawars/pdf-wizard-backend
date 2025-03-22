import boto3
import io
from django.conf import settings
from botocore.exceptions import NoCredentialsError, ClientError


S3_BUCKET = settings.AWS_STORAGE_BUCKET_NAME
AWS_REGION = settings.AWS_S3_REGION_NAME
AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY

# Intiate S3 Client
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


def get_file_from_s3(file_key):
    """
    Fetch a file from S3 and return its bytes
    :param file_key: The S3 file key (path in bucket)
    :return: File bytes or None if an error occurs
    """

    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=file_key)
        file_stream = response["Body"].read()
        return io.BytesIO(file_stream)
    except NoCredentialsError:
        raise Exception("AWS credentials not configured properly")
    except ClientError as e:
        raise Exception(f"Failed to fetch file from S3: {str(e)}")
