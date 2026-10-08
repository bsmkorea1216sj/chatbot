#!/usr/bin/env python3
"""BSM AI 리서치 단계별 실행기 (코랩 없이 GCP REST 직접 호출).

  python run.py --list              단계 목록
  python run.py --step 1            1단계만 실행
  python run.py --step 3 --step 4   여러 단계 순서대로
  python run.py --from 8 --to 11    구간 실행
  python run.py --all               1~13 실행 (14단계 원가 측정은 따로)
"""
import argparse
import sys
import traceback

import conf
import steps

STEPS = [
    (1, "인증 확인", steps.step01_auth),
    (2, "설정 점검", steps.step02_config),
    (3, "API 활성화", steps.step03_enable_apis),
    (4, "Firestore + 작업 큐", steps.step04_firestore_and_queue),
    (5, "서비스 계정과 IAM", steps.step05_service_accounts),
    (6, "Secret Manager", steps.step06_secrets),
    (7, "Firebase 웹 구성", steps.step07_firebase_config),
    (8, "빌드 사본 준비", steps.step08_stage_source),
    (9, "모델 잠금 패치", steps.step09_patch_model_lock),
    (10, "단위 테스트", steps.step10_tests),
    (11, "무료 체험 예산 시드", steps.step11_seed_trial_pool),
    (12, "Cloud Run 배포", steps.step12_deploy),
    (13, "스모크 테스트", steps.step13_smoke),
    (14, "원가 측정", steps.step14_measure_cost),
]
BY_NUM = {n: (label, fn) for n, label, fn in STEPS}


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--step", type=int, action="append", default=[])
    ap.add_argument("--from", dest="start", type=int)
    ap.add_argument("--to", dest="end", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list:
        print(f"대상 프로젝트 {conf.PROJECT_ID} | 리전 {conf.REGION}\n")
        for num, label, _ in STEPS:
            print(f"  {num:>2}. {label}")
        print("\n14단계는 실제 모델 호출로 비용이 발생합니다. 따로 실행하세요.")
        return 0

    if args.all:
        wanted = list(range(1, 14))
    elif args.start or args.end:
        wanted = list(range(args.start or 1, (args.end or 13) + 1))
    else:
        wanted = args.step
    if not wanted:
        ap.print_help()
        return 2

    unknown = [n for n in wanted if n not in BY_NUM]
    if unknown:
        print(f"없는 단계: {unknown}", file=sys.stderr)
        return 2

    for num in wanted:
        label, fn = BY_NUM[num]
        print(f"\n=== {num}단계 · {label} " + "=" * max(0, 52 - len(label)), flush=True)
        try:
            fn()
        except Exception as exc:
            print(f"\n  실패: {type(exc).__name__}: {exc}", file=sys.stderr)
            traceback.print_exc(limit=3)
            print(f"\n{num}단계에서 멈췄습니다. 원인을 고친 뒤 --step {num} 로 다시 실행하세요.",
                  file=sys.stderr)
            return 1
    print(f"\n완료: {wanted}단계")
    if conf.state().get("service_url"):
        print(f"서비스 주소: {conf.state()['service_url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
