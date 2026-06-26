"""
AWS 인프라 배포: DynamoDB 테이블 2개 + S3 버킷 + CloudFront 생성
"""
import boto3
import json
import time
import os

REGION = os.environ.get("AWS_REGION", "us-east-1")
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "miim-daily-report")

dynamodb = boto3.client("dynamodb", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
cloudfront = boto3.client("cloudfront", region_name="us-east-1")


def create_dynamodb_tables():
    tables = [
        {
            "TableName": "miim-prices",
            "KeySchema": [{"AttributeName": "date", "KeyType": "HASH"}],
            "AttributeDefinitions": [{"AttributeName": "date", "AttributeType": "S"}],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": "miim-posts",
            "KeySchema": [{"AttributeName": "date", "KeyType": "HASH"}],
            "AttributeDefinitions": [{"AttributeName": "date", "AttributeType": "S"}],
            "BillingMode": "PAY_PER_REQUEST",
        },
    ]
    for tbl in tables:
        try:
            dynamodb.create_table(**tbl)
            print(f"[OK] DynamoDB 테이블 생성: {tbl['TableName']}")
        except dynamodb.exceptions.ResourceInUseException:
            print(f"[SKIP] 이미 존재: {tbl['TableName']}")


def create_s3_bucket():
    try:
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=S3_BUCKET)
        else:
            s3.create_bucket(
                Bucket=S3_BUCKET,
                CreateBucketConfiguration={"LocationConstraint": REGION},
            )
        print(f"[OK] S3 버킷 생성: {S3_BUCKET}")
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"[SKIP] 이미 존재: {S3_BUCKET}")

    # 퍼블릭 액세스 차단 해제 (CloudFront OAC 사용 시 불필요하나 정적 웹용)
    s3.put_public_access_block(
        Bucket=S3_BUCKET,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": False,
            "IgnorePublicAcls": False,
            "BlockPublicPolicy": False,
            "RestrictPublicBuckets": False,
        },
    )

    # 버킷 정책 설정 (퍼블릭 읽기)
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{S3_BUCKET}/*",
        }],
    }
    s3.put_bucket_policy(Bucket=S3_BUCKET, Policy=json.dumps(policy))

    # 정적 웹호스팅 활성화
    s3.put_bucket_website(
        Bucket=S3_BUCKET,
        WebsiteConfiguration={
            "IndexDocument": {"Suffix": "index.html"},
            "ErrorDocument": {"Key": "index.html"},
        },
    )
    print(f"[OK] S3 정적 웹호스팅 활성화")


def create_cloudfront_distribution():
    origin_domain = f"{S3_BUCKET}.s3-website-{REGION}.amazonaws.com"
    try:
        resp = cloudfront.create_distribution(
            DistributionConfig={
                "CallerReference": f"miim-{int(time.time())}",
                "Comment": "MIIM Daily Report CDN",
                "DefaultRootObject": "index.html",
                "Origins": {
                    "Quantity": 1,
                    "Items": [{
                        "Id": "miim-s3-origin",
                        "DomainName": origin_domain,
                        "CustomOriginConfig": {
                            "HTTPPort": 80,
                            "HTTPSPort": 443,
                            "OriginProtocolPolicy": "http-only",
                        },
                    }],
                },
                "DefaultCacheBehavior": {
                    "TargetOriginId": "miim-s3-origin",
                    "ViewerProtocolPolicy": "redirect-to-https",
                    "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",  # CachingOptimized
                    "Compress": True,
                    "AllowedMethods": {"Quantity": 2, "Items": ["HEAD", "GET"], "CachedMethods": {"Quantity": 2, "Items": ["HEAD", "GET"]}},
                },
                "Enabled": True,
                "PriceClass": "PriceClass_200",
                "HttpVersion": "http2",
            }
        )
        domain = resp["Distribution"]["DomainName"]
        dist_id = resp["Distribution"]["Id"]
        print(f"[OK] CloudFront 배포 생성: https://{domain}")
        print(f"     배포 ID: {dist_id}")
        return domain
    except Exception as e:
        print(f"[WARN] CloudFront 생성 실패: {e}")
        return None


if __name__ == "__main__":
    print("=== MIIM 인프라 배포 시작 ===")
    create_dynamodb_tables()
    create_s3_bucket()
    create_cloudfront_distribution()
    print("=== 배포 완료 ===")
