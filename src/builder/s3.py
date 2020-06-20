import boto3

class UploadError(Exception):
    pass

def ensure_bucket(bucket: str):
    s3 = boto3.client('s3')
    pass

def upload_blob(blob: bytes, bucket: str, key: str):
    s3 = boto3.client('s3')
    s3.put_object(Body=blob, Bucket=bucket, Key=key)
