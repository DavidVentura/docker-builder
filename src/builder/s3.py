import logging

import boto3
import botocore

from builder import settings

from typing import List

log = logging.getLogger('S3')


class UploadError(Exception):
    pass

def _client():
    config = botocore.client.Config(connect_timeout=3, read_timeout=3, retries={'max_attempts': 0})
    session = boto3.session.Session(profile_name=settings.S3_PROFILE)
    return session.client(service_name='s3', endpoint_url=settings.S3_ENDPOINT, config=config)

def ensure_buckets(buckets: List[str]):
    s3 = _client()
    existing_buckets = [b['Name'] for b in s3.list_buckets()['Buckets']]
    for wanted_bucket in buckets:
        if wanted_bucket not in existing_buckets:
            log.info('Creating bucket <%s>', wanted_bucket)
            s3.create_bucket(Bucket=wanted_bucket)
            log.info('Created bucket <%s>', wanted_bucket)
        else:
            log.info('Bucket <%s> already exists -- no need to create it', wanted_bucket)

def upload_blob(blob: bytes, bucket: str, key: str):
    s3 = _client()
    s3.put_object(Body=blob, Bucket=bucket, Key=key)
