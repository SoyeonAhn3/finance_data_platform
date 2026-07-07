# credentials/

이 폴더에 **GCP 서비스계정 JSON 키**를 넣습니다.

## 넣는 방법

1. GCP 콘솔 → 서비스 계정 → 키 탭 → **키 추가 → JSON** 으로 내려받은 파일을
2. 이 폴더에 `service_account.json` 이라는 이름으로 저장

```
credentials/
├── README.md            ← 이 파일 (git 에 올라감)
└── service_account.json ← 실제 키 (git 에서 자동 제외됨, 절대 커밋 금지)
```

3. 프로젝트 루트 `.env` 에 경로를 적습니다:

```
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service_account.json
```

## ⚠️ 보안

- `service_account.json` 은 **비밀번호와 같습니다.** 유출 시 남이 내 BigQuery 를 씁니다.
- `.gitignore` 가 이 폴더의 키 파일을 자동 제외하므로 실수로 커밋될 걱정은 없습니다
  (단, 이 `README.md` 만 예외로 추적됩니다).
