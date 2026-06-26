"""
Lambda Publisher: HTML을 S3에 업로드 → CloudFront URL로 퍼블릭 배포
"""
import os
import boto3
from datetime import datetime, timezone

s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))
dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))
posts_table = dynamodb.Table(os.environ.get("DYNAMODB_POSTS_TABLE", "miim-posts"))

S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "miim-daily-report")
CLOUDFRONT_DOMAIN = os.environ.get("CLOUDFRONT_DOMAIN", "")


def upload_to_s3(html_content: str, date_str: str) -> dict:
    daily_key = f"reports/{date_str}/index.html"
    latest_key = "index.html"

    for key in [daily_key, latest_key]:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=html_content.encode("utf-8"),
            ContentType="text/html; charset=utf-8",
            CacheControl="max-age=3600" if key == latest_key else "max-age=86400",
        )
        print(f"S3 업로드 완료: s3://{S3_BUCKET}/{key}")

    daily_url = f"https://{CLOUDFRONT_DOMAIN}/reports/{date_str}/index.html" if CLOUDFRONT_DOMAIN else f"https://{S3_BUCKET}.s3.amazonaws.com/{daily_key}"
    latest_url = f"https://{CLOUDFRONT_DOMAIN}/index.html" if CLOUDFRONT_DOMAIN else f"https://{S3_BUCKET}.s3.amazonaws.com/{latest_key}"

    return {"daily_url": daily_url, "latest_url": latest_url, "daily_key": daily_key}


def lambda_handler(event, context):
    date_str = event.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    html_content = event.get("html_content", "")

    if not html_content:
        return {"statusCode": 400, "error": "html_content 없음"}

    urls = upload_to_s3(html_content, date_str)

    posts_table.update_item(
        Key={"date": date_str},
        UpdateExpression="SET #s = :s, daily_url = :du, latest_url = :lu, published_at = :pa",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": "published",
            ":du": urls["daily_url"],
            ":lu": urls["latest_url"],
            ":pa": datetime.now(timezone.utc).isoformat(),
        },
    )

    print(f"배포 완료: {urls['latest_url']}")
    return {
        "statusCode": 200,
        "date": date_str,
        "daily_url": urls["daily_url"],
        "latest_url": urls["latest_url"],
        "message": "MIIM 리포트 배포 완료",
    }
