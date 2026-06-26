"""
Lambda 함수 3개(collector, writer, publisher) 배포
"""
import boto3
import os
import zipfile
import io

REGION = os.environ.get("AWS_REGION", "us-east-1")
ACCOUNT_ID = boto3.client("sts").get_caller_identity()["Account"]
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "miim-daily-report")
CLOUDFRONT_DOMAIN = os.environ.get("CLOUDFRONT_DOMAIN", "")
ROLE_ARN = os.environ.get("LAMBDA_ROLE_ARN", f"arn:aws:iam::{ACCOUNT_ID}:role/miim-lambda-role")

lam = boto3.client("lambda", region_name=REGION)
iam = boto3.client("iam")

LAMBDA_CONFIGS = [
    {
        "name": "miim-collector",
        "handler": "handler.lambda_handler",
        "source": "lambda/collector/handler.py",
        "timeout": 120,
        "memory": 512,
        "env": {
            "AWS_REGION": REGION,
            "DYNAMODB_PRICES_TABLE": "miim-prices",
        },
        "layers": ["yfinance"],
    },
    {
        "name": "miim-writer",
        "handler": "handler.lambda_handler",
        "source": "lambda/writer/handler.py",
        "timeout": 180,
        "memory": 512,
        "env": {
            "AWS_REGION": REGION,
            "DYNAMODB_PRICES_TABLE": "miim-prices",
            "DYNAMODB_POSTS_TABLE": "miim-posts",
            "ANTHROPIC_SECRET_NAME": "miim/anthropic-api-key",
        },
        "layers": ["anthropic"],
    },
    {
        "name": "miim-publisher",
        "handler": "handler.lambda_handler",
        "source": "lambda/publisher/handler.py",
        "timeout": 60,
        "memory": 256,
        "env": {
            "AWS_REGION": REGION,
            "DYNAMODB_POSTS_TABLE": "miim-posts",
            "S3_BUCKET_NAME": S3_BUCKET,
            "CLOUDFRONT_DOMAIN": CLOUDFRONT_DOMAIN,
        },
        "layers": [],
    },
]


def create_lambda_role():
    trust = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"], "Resource": "*"},
            {"Effect": "Allow", "Action": ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:UpdateItem", "dynamodb:Query"], "Resource": f"arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/miim-*"},
            {"Effect": "Allow", "Action": ["s3:PutObject", "s3:GetObject"], "Resource": f"arn:aws:s3:::{S3_BUCKET}/*"},
            {"Effect": "Allow", "Action": ["secretsmanager:GetSecretValue"], "Resource": f"arn:aws:secretsmanager:{REGION}:{ACCOUNT_ID}:secret:miim/*"},
        ],
    }
    try:
        resp = iam.create_role(RoleName="miim-lambda-role", AssumeRolePolicyDocument=__import__("json").dumps(trust))
        role_arn = resp["Role"]["Arn"]
        iam.put_role_policy(RoleName="miim-lambda-role", PolicyName="miim-policy", PolicyDocument=__import__("json").dumps(policy))
        print(f"[OK] IAM 역할 생성: {role_arn}")
        import time; time.sleep(10)
        return role_arn
    except iam.exceptions.EntityAlreadyExistsException:
        resp = iam.get_role(RoleName="miim-lambda-role")
        return resp["Role"]["Arn"]


def zip_handler(source_path: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(source_path, "handler.py")
    return buf.getvalue()


def deploy_lambda(cfg: dict, role_arn: str):
    zip_bytes = zip_handler(cfg["source"])
    kwargs = dict(
        FunctionName=cfg["name"],
        Runtime="python3.12",
        Role=role_arn,
        Handler=cfg["handler"],
        Code={"ZipFile": zip_bytes},
        Timeout=cfg["timeout"],
        MemorySize=cfg["memory"],
        Environment={"Variables": cfg["env"]},
    )
    try:
        lam.create_function(**kwargs)
        print(f"[OK] Lambda 생성: {cfg['name']}")
    except lam.exceptions.ResourceConflictException:
        lam.update_function_code(FunctionName=cfg["name"], ZipFile=zip_bytes)
        lam.update_function_configuration(
            FunctionName=cfg["name"],
            Timeout=cfg["timeout"],
            MemorySize=cfg["memory"],
            Environment={"Variables": cfg["env"]},
        )
        print(f"[UPDATE] Lambda 업데이트: {cfg['name']}")


if __name__ == "__main__":
    print("=== Lambda 함수 배포 시작 ===")
    role_arn = create_lambda_role()
    for cfg in LAMBDA_CONFIGS:
        deploy_lambda(cfg, role_arn)
    print("=== Lambda 배포 완료 ===")
