"""
EventBridge: 매일 08:30 KST(23:30 UTC 전날) Step Functions로 파이프라인 트리거
Lambda 체인: collector → writer → publisher
"""
import boto3
import json
import os

REGION = os.environ.get("AWS_REGION", "us-east-1")
ACCOUNT_ID = boto3.client("sts").get_caller_identity()["Account"]

events = boto3.client("events", region_name=REGION)
lam = boto3.client("lambda", region_name=REGION)
sfn = boto3.client("stepfunctions", region_name=REGION)
iam = boto3.client("iam")


def create_step_function():
    """3개 Lambda를 순차 실행하는 Step Function 상태 머신"""
    definition = {
        "Comment": "MIIM Daily Report Pipeline",
        "StartAt": "Collector",
        "States": {
            "Collector": {
                "Type": "Task",
                "Resource": f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:miim-collector",
                "Next": "Writer",
                "Retry": [{"ErrorEquals": ["States.ALL"], "MaxAttempts": 2, "IntervalSeconds": 30}],
            },
            "Writer": {
                "Type": "Task",
                "Resource": f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:miim-writer",
                "Next": "Publisher",
                "Retry": [{"ErrorEquals": ["States.ALL"], "MaxAttempts": 2, "IntervalSeconds": 30}],
            },
            "Publisher": {
                "Type": "Task",
                "Resource": f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:miim-publisher",
                "End": True,
            },
        },
    }

    # Step Function 실행 역할
    trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "states.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    policy = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "lambda:InvokeFunction", "Resource": f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:miim-*"}]}
    try:
        r = iam.create_role(RoleName="miim-sfn-role", AssumeRolePolicyDocument=json.dumps(trust))
        sfn_role_arn = r["Role"]["Arn"]
        iam.put_role_policy(RoleName="miim-sfn-role", PolicyName="miim-sfn-policy", PolicyDocument=json.dumps(policy))
        import time; time.sleep(10)
    except iam.exceptions.EntityAlreadyExistsException:
        sfn_role_arn = iam.get_role(RoleName="miim-sfn-role")["Role"]["Arn"]

    try:
        resp = sfn.create_state_machine(
            name="miim-daily-pipeline",
            definition=json.dumps(definition),
            roleArn=sfn_role_arn,
        )
        sm_arn = resp["stateMachineArn"]
        print(f"[OK] Step Function 생성: {sm_arn}")
    except sfn.exceptions.StateMachineAlreadyExists:
        sm_arn = f"arn:aws:states:{REGION}:{ACCOUNT_ID}:stateMachine:miim-daily-pipeline"
        print(f"[SKIP] 이미 존재: {sm_arn}")

    return sm_arn


def create_eventbridge_rule(sm_arn: str):
    """EventBridge 역할 생성"""
    trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "scheduler.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    policy = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "states:StartExecution", "Resource": sm_arn}]}
    try:
        r = iam.create_role(RoleName="miim-eventbridge-role", AssumeRolePolicyDocument=json.dumps(trust))
        eb_role_arn = r["Role"]["Arn"]
        iam.put_role_policy(RoleName="miim-eventbridge-role", PolicyName="miim-eb-policy", PolicyDocument=json.dumps(policy))
    except iam.exceptions.EntityAlreadyExistsException:
        eb_role_arn = iam.get_role(RoleName="miim-eventbridge-role")["Role"]["Arn"]

    # EventBridge Scheduler (매일 23:30 UTC = 08:30 KST)
    scheduler = boto3.client("scheduler", region_name=REGION)
    try:
        scheduler.create_schedule(
            Name="miim-daily-0830-kst",
            ScheduleExpression="cron(30 23 * * ? *)",
            ScheduleExpressionTimezone="UTC",
            FlexibleTimeWindow={"Mode": "OFF"},
            Target={
                "Arn": sm_arn,
                "RoleArn": eb_role_arn,
                "Input": json.dumps({}),
            },
        )
        print("[OK] EventBridge 스케줄 생성: 매일 08:30 KST (23:30 UTC)")
    except Exception as e:
        print(f"[WARN] 스케줄 생성 실패: {e}")


if __name__ == "__main__":
    print("=== EventBridge 설정 시작 ===")
    sm_arn = create_step_function()
    create_eventbridge_rule(sm_arn)
    print("=== EventBridge 설정 완료 ===")
