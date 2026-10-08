# 출처와 취급 방침

이 디렉터리의 파일은 Google Drive 노트북
`BSM_AI_Research_GCP_v0_3.ipynb` (파일 ID `1suGjY7tdhlEubNDB-pK38LVl3w5r2ixS`)
의 `FILES` 딕셔너리에서 **원문 그대로** 추출한 것입니다. 손으로 고치지 않았습니다.

- `quote()` 의 `gemini-2.5-flash` 하드코딩은 **여기서 고치지 않습니다.**
  배포 직전 9단계(`scripts/gcp_deploy` 의 `step09_patch_model_lock`)에서
  빌드 사본에만 패치를 적용합니다. 패치 위치를 한 곳에 모아 감사할 수 있게 하려는 것입니다.
- 원본 노트북이 바뀌면 9단계가 `quote() 원문을 찾지 못했습니다` 로 멈춥니다.
  그때 이 디렉터리를 다시 받아 맞추세요.
