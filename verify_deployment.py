"""
배포 완료 조건 체크리스트 검증
"""
import boto3
import os

REGION = os.environ.get("AWS_REGION", "us-east-1")
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "miim-daily-report")


def check(label: str, fn):
    try:
        result = fn()
        status = "[✓]" if result else "[✗]"
        print(f"  {status} {label}")
        return bool(result)
    except Exception as e:
        print(f"  [✗] {label}: {e}")
        return False


def verify():
    print("=== MIIM 배포 완료 조건 체크리스트 ===\n")
    dynamodb = boto3.client("dynamodb", region_name=REGION)
    lam = boto3.client("lambda", region_name=REGION)
    s3 = boto3.client("s3", region_name=REGION)
    sm = boto3.client("secretsmanager", region_name=REGION)

    tables = lambda: [t for t in dynamodb.list_tables()["TableNames"] if "miim" in t]
    lambdas = lambda: [f["FunctionName"] for f in lam.list_functions()["Functions"] if "miim" in f["FunctionName"]]

    results = [
        check("DynamoDB miim-prices 테이블", lambda: "miim-prices" in tables()),
        check("DynamoDB miim-posts 테이블", lambda: "miim-posts" in tables()),
        check("S3 버킷 존재", lambda: S3_BUCKET in [b["Name"] for b in s3.list_buckets()["Buckets"]]),
        check("miim-collector Lambda", lambda: "miim-collector" in lambdas()),
        check("miim-writer Lambda", lambda: "miim-writer" in lambdas()),
        check("miim-publisher Lambda", lambda: "miim-publisher" in lambdas()),
        check("Secrets Manager API 키", lambda: sm.describe_secret(SecretId="miim/anthropic-api-key")),
    ]

    passed = sum(results)
    total = len(results)
    print(f"\n결과: {passed}/{total} 통과")
    if passed == total:
        print("🎉 모든 조건 충족! MIIM 시스템 배포 완료.")
    else:
        print("⚠️  일부 조건 미충족. 위 단계를 재확인하세요.")


if __name__ == "__main__":
    verify()
