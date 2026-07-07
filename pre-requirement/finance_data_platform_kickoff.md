---
project: finance_data_platform
created: 2026-05-12
last_skill: design-impl-spec
---

# Project Kickoff — finance_data_platform

> 금융 데이터를 BigQuery 기반으로 수집·적재·모델링하고, Power BI 대시보드와 자연어 질의 AI를 제공하는 End-to-End 데이터 분석 플랫폼

---

## 1. 프로젝트 프로필

### 기본 정보

| 항목 | 내용 |
|---|---|
| 프로젝트명 | finance_data_platform |
| 유형 | 데이터 파이프라인 + BI 대시보드 + AI 프로젝트 |
| 목적 | 데이터 엔지니어링 및 분석 학습 (초중급 단계 목표) |
| 주요 사용자 | 본인 (학습용) |
| 데이터 소스 | ETF 보유종목 IVV/QQQ (S&P500+Nasdaq100 구성종목 명단), yfinance (주가), FRED API (경제지표), Alpha Vantage (기술지표), 공공데이터포털/KRX (한국 주가) — 전부 무료 |
| 결과 형태 | MVP: Power BI 대시보드 / v2: 자연어 질의 AI 답변 화면 |

### 핵심 기능

| # | 기능 | MVP 포함 |
|---|---|---|
| 0 | 유니버스 수집 (ETF 보유종목 IVV/QQQ → S&P500+Nasdaq100 구성종목 명단) | ✅ |
| 1 | API 데이터 수집 (yfinance, FRED) | ✅ |
| 1-1 | API 데이터 수집 (Alpha Vantage, KRX) | ❌ (v2) (평가 후 조정됨) |
| 2 | BigQuery 적재 (raw 레이어) | ✅ |
| 3 | Star Schema 모델링 + Mart View | ✅ |
| 4 | Power BI 대시보드 (KPI 시각화) | ✅ |
| 5 | 자연어 질의 AI (Text-to-SQL — Claude/OpenAI API) | ❌ (v2) (평가 후 조정됨) |

### 채택된 AI 제안

| # | 아이디어 | 분류 |
|---|---|---|
| 1 | 데이터 품질 검증 (수집 후 자동 검증 — 결측값, 이상치, 중복 체크) | MVP |
| 2 | 파이프라인 실행 로그 (수집/적재 단계별 성공/실패/건수 기록) | MVP |
| 3 | 데이터 사전 (테이블/컬럼 설명, 계산식, 데이터 소스 매핑 문서) | MVP |

### 기술 스택

| 레이어 | 기술 | 선택 이유 |
|---|---|---|
| 데이터 수집 | Python (yfinance, fredapi, requests) | 무료 API 연동, 학습 접근성 |
| 데이터 웨어하우스 | BigQuery | 영구 무료티어/서버리스/GCP 생태계, Star Schema 지원 |
| 데이터 모델링 | Star Schema (Fact/Dim/Mart) | 분석 최적화, 업계 표준 패턴 |
| 시각화 | Power BI | 대시보드 표준, BigQuery 네이티브 커넥터 |
| AI 질의 (v2) | Claude/OpenAI API (Text-to-SQL) | 자연어 → SQL 변환, 결과 해석 (평가 후 조정됨) |
| 오케스트레이션 | Python 스크립트 (배치) + GitHub Actions 스케줄 | 학습용, 단순 구조 + 무료 CI 스케줄링 |

### KPI 후보

| # | KPI | 설명 |
|---|---|---|
| 1 | 수익률 | 종목/기간별 수익률 |
| 2 | 변동성 | 가격 변동 폭 |
| 3 | 거래량 추이 | 시계열 거래량 |
| 4 | 섹터별 비교 | 업종간 성과 비교 |
| 5 | 포트폴리오 성과 | AI 추천 포트폴리오 (범위 외 — 별도 프로젝트) |

### 제약사항

| 유형 | 내용 |
|---|---|
| 비용 | API 비용 최소화 — 무료 API 우선 사용 |
| 난이도 | 초중급 수준에 맞는 난이도 유지 |
| 환경 | BigQuery 영구 무료티어 (월 1TB 쿼리 + 10GB 저장) |
| 키 관리 | API 키는 .env 파일로 관리 (FRED, Alpha Vantage 등) |
| 데이터 한계 | 동적 유니버스는 "현재 구성종목"만 분석 → 생존 편향(과거 편출·상폐 종목 누락) 감수 (학습용) |

---

## 2. 시스템 아키텍처

### 파이프라인 흐름

```
[유니버스 수집(ETF)] → [API 소스] → [Python 수집] → [BigQuery raw] → [Star Schema 변환] → [Mart View] → [Power BI / AI 질의]
```

| 단계 | 설명 | 도구/서비스 |
|---|---|---|
| 1 | 유니버스 수집 — ETF 보유종목(IVV/QQQ)에서 S&P500+Nasdaq100 구성종목 명단 수집 | Python (universe_collector) |
| 2 | 외부 API에서 금융 데이터 수집 | Python (yfinance, fredapi, requests) |
| 3 | raw 데이터셋에 원본 적재 | google-cloud-bigquery (+ pandas-gbq, db-dtypes) |
| 4 | Star Schema로 Fact/Dim 테이블 변환 | BigQuery SQL (CREATE TABLE AS SELECT) |
| 5 | 부서별 Mart View 생성 | BigQuery SQL (CREATE VIEW) |
| 6 | 대시보드 시각화 | Power BI + BigQuery 커넥터 |
| 7 | 자연어 질의 → SQL 생성 → 실행 → 해석 (v2) | Claude/OpenAI API + Python (평가 후 조정됨) |

### 외부 서비스 의존성

| 서비스 | 용도 | 필수 여부 |
|---|---|---|
| ETF 보유종목 (IVV/QQQ) | S&P500+Nasdaq100 구성종목 명단 수집 (dim_symbol 소스) | 필수 |
| yfinance | 미국 주가 데이터 | 필수 |
| FRED API | 경제지표 (금리, 인플레이션 등) | 필수 |
| Alpha Vantage | 기술지표 (RSI, MACD 등) | 선택 |
| 공공데이터포털/KRX | 한국 주가 데이터 | 선택 |
| BigQuery | 데이터 웨어하우스 | 필수 |
| Power BI | 시각화 대시보드 | 필수 |
| GitHub Actions | 파이프라인 스케줄링 (cron + 수동 실행) | 선택 |
| Claude/OpenAI API | Text-to-SQL AI 질의 (v2) | 선택 (평가 후 조정됨) |

---

## 3. 데이터 구조

> raw 레이어에 `raw_universe`(S&P500+Nasdaq100 구성종목 명단 — ETF 보유종목 IVV/QQQ에서 매 실행 수집)가 있으며 `dim_symbol`의 소스입니다. 상세 raw/운영 엔티티는 §11 및 docs/data_dictionary.md 참조.

### Star Schema 설계

#### fact_daily_price (일별 주가 Fact)

| 컬럼 | 타입 | 설명 |
|---|---|---|
| date_key | INT64 | dim_date FK |
| symbol_key | INT64 | dim_symbol FK |
| open_price | NUMERIC | 시가 |
| high_price | NUMERIC | 고가 |
| low_price | NUMERIC | 저가 |
| close_price | NUMERIC | 종가 |
| adj_close | NUMERIC | 수정 종가 |
| volume | INT64 | 거래량 |

#### fact_economic_indicator (경제지표 Fact)

| 컬럼 | 타입 | 설명 |
|---|---|---|
| date_key | INT64 | dim_date FK |
| indicator_key | INT64 | dim_indicator FK |
| value | NUMERIC | 지표 값 |

#### dim_date (날짜 Dimension)

| 컬럼 | 타입 | 설명 |
|---|---|---|
| date_key | INT64 | PK (YYYYMMDD) |
| full_date | DATE | 전체 날짜 |
| year | INT64 | 연도 |
| quarter | INT64 | 분기 |
| month | INT64 | 월 |
| day_of_week | STRING | 요일 |
| is_trading_day | BOOL | 거래일 여부 |

#### dim_symbol (종목 Dimension)

> 소스: `raw_universe` (구성종목 명단). raw_daily_price가 아니라 유니버스 명단에서 생성 → 승인 명단(allowlist) 역할로 명단 밖 종목이 fact에서 걸러짐.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| symbol_key | INT64 | PK |
| ticker | STRING | 종목 코드 |
| company_name | STRING | 회사명 |
| sector | STRING | 섹터 |
| market | STRING | 시장 (US/KR) |

#### dim_indicator (경제지표 Dimension)

| 컬럼 | 타입 | 설명 |
|---|---|---|
| indicator_key | INT64 | PK |
| indicator_code | STRING | 지표 코드 (예: FEDFUNDS) |
| indicator_name | STRING | 지표명 |
| source | STRING | 출처 (FRED/Alpha Vantage) |
| unit | STRING | 단위 (%, 포인트 등) |

### Mart View

| View | 설명 | 주요 지표 |
|---|---|---|
| mart_performance | 종목별 수익률 분석 | 일간/주간/월간 수익률, 누적 수익률 |
| mart_risk | 리스크 분석 | 변동성, 최대 낙폭, 베타 |
| mart_macro | 매크로 연계 분석 | 금리-주가 상관관계, 경제지표 영향도 |

### 볼륨 & 갱신 주기

| 항목 | 내용 |
|---|---|
| 규모 | 학습용 — 수천~수만 건 |
| 처리 방식 | 배치 (일 1회 또는 수동 실행) |
| 보관 기간 | 제한 없음 (학습 데이터) |
| BigQuery 사양 | 서버리스 (on-demand, 무료티어 내 처리) |

---

## 4. 실패 시나리오 / 엣지케이스

| # | 시나리오 | 심각도 | 비고 |
|---|---|---|---|
| 1 | API 호출 실패 (서버 다운/Rate Limit) | 중 | 에러 로그 기록, 해당 API 건너뜀 (자동 재시도 없음 — FR-010) |
| 2 | 데이터 품질 문제 (결측값, 비거래일, 종목 코드 변경) | 중 | 품질 검증 단계에서 탐지 (채택 아이디어 #1) |
| 3 | BigQuery 쿼리 쿼터/무료티어 한도 초과 | 낮 | 무료티어 한도(월 1TB 쿼리) 모니터링 + 조기 경고 |
| 4 | Text-to-SQL 오류 (잘못된 SQL 생성) (v2) | 중 | SQL 검증 단계 + 사용자 확인 (평가 후 조정됨) |
| 5 | 스키마 변경 시 Mart View 깨짐 | 낮 | 데이터 사전으로 변경 영향 추적 (채택 아이디어 #3) |

---

## 5. 누락/모순 점검 결과

| # | 유형 | 내용 | 상태 | 해결 방법 |
|---|---|---|---|---|
| 1 | 모순 | 기술 스택 "AI 질의" 행에 v2 표기 누락 | ✅ 해결 | v2 표기 추가 |
| 2 | 모순 | 실패 시나리오 #4 Text-to-SQL이 v2 미표기 | ✅ 해결 | v2 표기 추가 |
| 3 | 누락 | API 키 관리 방법 미정의 | ✅ 해결 | .env 파일로 관리 (제약사항에 추가) |

점검 일시: 2026-05-07

---

## 6. 개발 착수 체크리스트

> 아래 항목을 모두 확인하면 개발을 시작할 수 있습니다.

### 환경 구성
- [ ] Python 3.x 설치 확인
- [ ] 필수 패키지 설치 가능 확인 (yfinance, fredapi, requests, google-cloud-bigquery, pandas-gbq, db-dtypes)
- [ ] Power BI Desktop 설치 확인
- [ ] python-dotenv 설치 (.env 파일 관리용)

### 데이터 & 접근
- [ ] FRED API 키 발급
- [ ] Alpha Vantage API 키 발급
- [ ] yfinance로 샘플 데이터 수집 테스트
- [ ] 공공데이터포털/KRX 접근 방법 확인

### 외부 서비스
- [ ] GCP 프로젝트 생성 + BigQuery API 활성화 + 서비스계정 키(JSON) 발급
- [ ] BigQuery 연결 테스트 (google-cloud-bigquery)
- [ ] Power BI에서 BigQuery 커넥터 연결 테스트
- [ ] GitHub Actions Secrets(FRED_API_KEY, 서비스계정 JSON) 및 워크플로 설정

### 설계 확정
- [ ] Star Schema 테이블 구조 최종 확정 (Fact 2, Dim 3, Mart 3)
- [ ] MVP 범위 확정: 핵심 4기능 + 채택 3기능 (Text-to-SQL은 v2)
- [ ] 데이터 품질 검증 규칙 정의 (결측값, 이상치, 중복 기준)

### 프로젝트 설정
- [ ] Git 저장소 초기화
- [ ] 프로젝트 폴더 구조 생성
- [ ] .env 파일 생성 및 .gitignore에 추가
- [ ] 기본 스킬 세팅 (/kickoff-skills)

생성일: 2026-05-07

---

## 7. 정직한 평가

### 종합 판정: 🟡 조건부 적합

| # | 평가 차원 | 판정 | 한 줄 피드백 |
|---|---|---|---|
| 1 | 차별화 | 🟡 | End-to-End 범위 자체가 차별점이지만, 개별 기술 조합은 표준 패턴에 가까움 |
| 2 | AI 적절성 | 🟢 | Text-to-SQL은 LLM 기반으로 적절하며, v2 이동은 합리적 판단 |
| 3 | 시장 유효성 | 🟢 | BigQuery + Star Schema + Power BI는 6개월 후에도 현역 기술 |
| 4 | 완성도 기대치 | 🟢 | MVP 축소(AI 제외) + 단계별 구축으로 실현 가능성 높아짐 |
| 5 | 학습 비용 | 비활성 | 비활성 (kickoff-context 미실행) |
| 6 | 보안 적절성 | 비활성 | 비활성 (학습용 + 본인 사용) |

### 🟡 상세

#### 차별화 — 🟡 조건부

**현재 상태**: BigQuery + Star Schema + Power BI는 데이터 엔지니어링 학습에서 흔한 조합
**개선 제안**: 금융 도메인 특화 요소(한미 교차 분석, 매크로-주가 상관관계) 또는 v2의 Text-to-SQL을 차별 포인트로 활용

### 사용자 결정

- 선택: 조정
- 조정 내용: Text-to-SQL AI를 MVP에서 v2로 이동, MVP는 데이터 파이프라인 + BI에 집중

평가일: 2026-05-07

---

## 8. 완료 조건 (Definition of Done)

> 아래 조건을 모두 만족하면 이 프로젝트는 "완료"입니다.

### 기능 동작 기준
- [ ] yfinance, FRED API에서 데이터를 수집하여 BigQuery raw 데이터셋에 적재가 완료된다
- [ ] raw 데이터셋에서 Star Schema(Fact 2, Dim 3)로 변환이 에러 없이 완료된다
- [ ] Mart View 3개(performance, risk, macro)가 정상 쿼리되고 결과를 반환한다
- [ ] Power BI 대시보드에서 Mart View 데이터가 차트로 표시된다

### 품질 기준
- [ ] 수집 데이터에 대해 결측값/이상치/중복 검증이 자동 실행되고 결과가 로그에 기록된다
- [ ] 파이프라인 각 단계(수집/적재/변환)의 성공/실패/건수가 실행 로그에 기록된다
- [ ] BigQuery 적재 건수가 API 수집 건수와 일치한다

### 문서화 기준
- [ ] README에 프로젝트 설명, 실행 방법, 환경 설정(.env) 방법이 포함되어 있다
- [ ] 데이터 사전(테이블/컬럼 설명, 계산식, 소스 매핑)이 문서화되어 있다

생성일: 2026-05-07

---

## 9. 요구사항 정의

### 9-1. 기능 요구사항 (Functional Requirements)

| ID | 기능 | 설명 | 우선순위 | 출처 |
|---|---|---|---|---|
| FR-012 | 유니버스 수집 (구성종목 명단) | ETF 보유종목(IVV=S&P500, QQQ=Nasdaq100)에서 구성종목 명단(ticker+회사명+섹터)을 매 실행 수집해 `raw_universe`에 적재한다. 소스 pluggable(etf_holdings 기본/api/wikipedia) + 실패 시 캐시 폴백. `dim_symbol`의 소스 | 필수 | 동적 유니버스 |
| FR-001 | API 데이터 수집 (미국 주가) | yfinance API로 미국 종목 일별 OHLCV 데이터를 수집한다 | 필수 | 기능#1 |
| FR-002 | API 데이터 수집 (경제지표) | FRED API로 금리, 인플레이션 등 경제지표를 수집한다 | 필수 | 기능#1 |
| FR-003 | API 데이터 수집 (기술지표) | Alpha Vantage API로 RSI, MACD 등 기술지표를 수집한다 | 선택 | 기능#1 |
| FR-004 | BigQuery 적재 | 수집된 원본 데이터를 BigQuery raw 데이터셋에 적재한다 | 필수 | 기능#2 |
| FR-005 | Star Schema 변환 | raw 데이터셋에서 Fact 2개(daily_price, economic_indicator) + Dim 3개(date, symbol, indicator)로 변환한다 | 필수 | 기능#3 |
| FR-006 | Mart View 생성 | performance, risk, macro 3개 Mart View를 생성하여 분석용 데이터를 제공한다 | 필수 | 기능#3 |
| FR-007 | Power BI 대시보드 | Mart View 데이터를 Power BI에서 차트로 시각화하고 날짜/종목 필터를 제공한다 | 필수 | 기능#4 |
| FR-008 | 자연어 질의 AI | 자연어 입력을 SQL로 변환하여 BigQuery에서 실행하고 결과를 해석한다 | 선택 (v2) | 기능#5 |
| FR-009 | 데이터 품질 검증 | 수집 후 결측값/이상치/중복을 자동 검증하고, 실패 시 경고 로그를 남기며 적재를 계속한다 | 필수 | 제안#1 |
| FR-010 | 파이프라인 실행 로그 | 수집/적재/변환 각 단계의 성공/실패/건수를 로그에 기록한다 (실패 시 로그만, 자동 재시도 없음) | 필수 | 제안#2 |
| FR-011 | 데이터 사전 | 테이블/컬럼 설명, 계산식, 데이터 소스 매핑을 문서화한다 | 필수 | 제안#3 |

### 9-2. 비기능 요구사항 (Non-Functional Requirements)

| ID | 카테고리 | 항목 | 목표 메트릭 | 우선순위 |
|---|---|---|---|---|
| NFR-001 | 성능 | 배치 수집 시간 | MVP 범위(yfinance + FRED) 전체 수집 30분 이내 완료 | 중간 |
| NFR-002 | 성능 | Mart View 쿼리 응답 | 단일 쿼리 10초 이내 (BigQuery on-demand) | 중간 |
| NFR-003 | 유지보수성 | 코드 구조 | 수집/적재/변환/시각화 모듈 분리 | 중간 |
| NFR-004 | 유지보수성 | 로깅 | 구조화된 로깅 (타임스탬프, 단계, 상태, 건수) | 중간 |
| NFR-005 | 유지보수성 | 문서화 | README (실행 방법, 환경 설정) + 데이터 사전 | 중간 |
| NFR-006 | 데이터 품질 | 정확성 | 수집 데이터와 소스 API 응답의 값 일치율 100% | 높음 |
| NFR-007 | 데이터 품질 | 완전성 | 필수 필드 누락률 0% (raw는 nullable로 수용, 완전성은 fact NOT NULL + 승인 명단 종목 수집 0건 시 completeness 경고[IR-008]로 보장) | 높음 |
| NFR-008 | 데이터 품질 | 일관성 | BigQuery 적재 건수 = API 수집 건수 (불일치 시 경고) | 높음 |
| NFR-009 | 데이터 품질 | 적시성 | 배치 실행 후 1시간 이내 최신 데이터 반영 | 낮음 |

**비활성 카테고리:**

| 카테고리 | 비활성 사유 |
|---|---|
| 보안 | 학습용 + 본인 사용 프로젝트로, 외부 사용자 없어 보안 요구사항 해당 없음 |
| 확장성 | 학습 목적 프로젝트로 확장 요구사항 해당 없음 |
| 가용성 | 학습 목적 프로젝트로 가용성 SLA 불필요 |
| 호환성 | 데이터 파이프라인/BI 유형으로 멀티 플랫폼 호환 요구사항 없음 |

### 9-3. 사용자 흐름 (User Flows)

#### 주요 흐름 1: 데이터 수집 → 적재 → 변환

1. 사용자가 파이프라인을 실행한다 (`python src/main.py`)
2. yfinance/FRED/Alpha Vantage API에서 데이터를 수집한다
3. 데이터 품질 검증을 실행한다 (결측값, 이상치, 중복 체크)
4. 검증 결과를 로그에 기록한다 (성공/경고)
5. BigQuery raw 데이터셋에 원본 데이터를 적재한다
6. 적재 건수를 로그에 기록한다
7. Star Schema 변환 SQL을 실행한다 (Fact/Dim 테이블 갱신)
8. Mart View가 자동으로 최신 데이터를 반영한다

#### 주요 흐름 2: 대시보드 조회

1. 사용자가 Power BI를 열고 BigQuery에 연결한다
2. 대시보드에서 KPI(수익률, 변동성, 거래량 등)를 확인한다
3. 날짜 필터로 기간을 조정한다
4. 종목 필터로 특정 종목을 선택한다

#### 대안 흐름

- **선택 데이터 소스 미사용 시**: Alpha Vantage 수집을 건너뛰고 yfinance + FRED만으로 진행
- **BigQuery 무료티어 한도 근접 시**: 수집까지만 실행하고 적재는 쿼터 리셋(월간) 후 재시도

#### 예외 흐름

- **API 호출 실패 (Rate Limit/서버 다운)**: 에러 로그 기록, 해당 API 건너뜀, 수동 재실행 안내
- **데이터 품질 검증 실패**: 경고 로그 기록, 적재는 계속 진행
- **BigQuery 연결 실패**: 에러 로그 기록, 수집 데이터는 로컬 CSV로 임시 저장 안내

### 9-4. 제약사항 보강

| 유형 | 내용 | 근거 |
|---|---|---|
| 비용 | 무료 API만 사용, BigQuery 영구 무료티어(월 1TB 쿼리 + 10GB 저장) 범위 내 운영 | 섹션 1 제약사항 |
| 난이도 | 초중급 수준 유지 — 복잡한 오케스트레이션(Airflow 등) 도입 금지 | 섹션 1 제약사항 |
| API Rate Limit | yfinance: 무제한 (비공식), FRED: 120회/분, Alpha Vantage: 5회/분 | 섹션 2 외부 서비스 |
| 데이터 규모 | 100+ 종목 × 5년+ (수만~수십만 건) — BigQuery 무료티어로 처리 가능 범위 | 인터뷰 결과 |
| 키 관리 | API 키는 .env 파일로 관리, Git에 커밋 금지 | 섹션 1 제약사항 |

## 10. 시스템 아키텍처 (상세)

### 10-1. 시스템 구조 (System Structure)

```
[External APIs]           [Python Application]              [BigQuery DW]             [Serving]

┌─────────────┐     ┌───────────────────────────┐
│ ETF IVV/QQQ │◄────│    main.py (Orchestrator)  │
│  yfinance   │◄────│  ┌─────────────────────┐  │     ┌──────────────┐
│  FRED API   │◄────│  │  Universe Collector │──┼────→│ raw_universe │──→ dim_symbol
│  Alpha Vant.│◄────│  └─────────────────────┘  │     └──────────────┘
│  KRX       │◄────│  ┌─────────┐ ┌─────────┐  │     ┌──────────────┐
└─────────────┘     │  │Collector│→│Validator │  │     │              │
                    │  └────┬────┘ └────┬────┘  │     │  raw         │
                    │       │           │       │     │  (staging)   │
                    │  ┌────▼───────────▼────┐  │     └──────┬───────┘
                    │  │      Loader         │──┼────→       │
                    │  └─────────────────────┘  │     ┌──────▼───────┐
                    │  ┌─────────────────────┐  │     │ Star Schema  │
                    │  │    Transformer      │──┼────→│ Fact / Dim   │
                    │  └─────────────────────┘  │     └──────┬───────┘
                    │  ┌─────────────────────┐  │     ┌──────▼───────┐     ┌──────────┐
                    │  │   Mart Manager      │──┼────→│  Mart View   │────→│ Power BI │
                    │  └─────────────────────┘  │     └──────────────┘     │Dashboard │
                    │  ┌─────────────────────┐  │                          └──────────┘
                    │  │  Pipeline Logger    │  │
                    │  └─────────────────────┘  │
                    └───────────────────────────┘
```

#### 컴포넌트 설명

| 컴포넌트 | 역할 | 기술 | 입력 | 출력 |
|---|---|---|---|---|
| Orchestrator | 파이프라인 전체 실행 관리 | Python (main.py) | CLI 실행 | 파이프라인 완료 로그 |
| Universe Collector | ETF 보유종목(IVV/QQQ)에서 S&P500+Nasdaq100 구성종목 명단 수집 → raw_universe 적재 (dim_symbol 소스), 실패 시 캐시 폴백 | Python (requests, pandas) | ETF 보유종목 CSV | raw_universe 테이블 |
| Collector | 외부 API에서 금융 데이터 수집 | Python (yfinance, fredapi, requests) | API 엔드포인트, 종목 목록 (raw_universe) | DataFrame (원본 데이터) |
| Validator | 수집 데이터 품질 검증 (결측/이상치/중복) | Python (pandas) | DataFrame | 검증 결과 (pass/warn) + 로그 |
| Loader | BigQuery raw 데이터셋에 Full Refresh 적재 | google-cloud-bigquery (WRITE_TRUNCATE load job) | DataFrame | raw 테이블 |
| Transformer | raw → Star Schema 변환 (BigQuery 내부) | BigQuery SQL (CTAS) | raw 테이블 | Fact 2 + Dim 3 테이블 |
| Mart Manager | 분석용 Mart View 생성/갱신 | BigQuery SQL (CREATE VIEW) | Fact/Dim 테이블 | Mart View 3개 |
| Pipeline Logger | 각 단계 성공/실패/건수 기록 | Python (logging) | 각 단계 상태 | 구조화된 로그 파일 |
| Power BI Dashboard | Mart View 데이터 시각화 | Power BI + BigQuery Connector | Mart View | 대시보드 차트 |
| Text-to-SQL (v2) | 자연어 → SQL 질의 → 결과 해석 | Claude/OpenAI API + Python | 자연어 질문 | SQL 결과 + 해석 |

#### 컴포넌트 간 통신

| 소스 | 대상 | 방식 | 프로토콜 |
|---|---|---|---|
| Orchestrator | Universe Collector → Collector → Validator → Loader → Transformer | 동기 순차 호출 | Python 함수 호출 |
| Universe Collector | ETF 보유종목 (IVV/QQQ CSV) | 동기 HTTP | REST/CSV (HTTPS) |
| Universe Collector | BigQuery raw_universe | 동기 | google-cloud-bigquery (WRITE_TRUNCATE load job) |
| Collector | External APIs | 동기 HTTP | REST API (HTTPS) |
| Loader | BigQuery raw 데이터셋 | 동기 | google-cloud-bigquery (WRITE_TRUNCATE load job) |
| Transformer | BigQuery Star Schema | 동기 | BigQuery SQL (CTAS) |
| Mart Manager | BigQuery Mart | 동기 | BigQuery SQL (CREATE VIEW) |
| Power BI | BigQuery Mart View | 동기 | Power BI BigQuery Connector |
| Pipeline Logger | 콘솔/파일 | 동기 | Python logging (실시간) |
| Pipeline Logger | BigQuery (execution_log, quality_log) | 동기 | load job (배치 완료 후 요약 적재) |

### 10-2. 기술 선택 근거 (Tech Selection Rationale)

| 레이어 | 선택 기술 | 비교 대안 | 선택 이유 |
|---|---|---|---|
| 데이터 수집 | Python (yfinance, fredapi, requests) | Node.js, Go | 금융 데이터 API 라이브러리가 Python에 집중 (yfinance, fredapi 등), 초중급 학습 접근성 우수 |
| 데이터 웨어하우스 | BigQuery | PostgreSQL, Redshift | 서버리스 클라우드 DW, 영구 무료티어(월 1TB 쿼리 + 10GB 저장)로 비용 부담 없이 학습 지속 가능, GCP 생태계·GitHub Actions 궁합, Star Schema + Mart View 네이티브 지원 |
| 데이터 모델링 | Star Schema (Fact/Dim) | 3NF, Data Vault | 분석 최적화 표준 패턴, BI 도구와 궁합 우수, 초중급에서 학습 가치 가장 높은 패턴 |
| 시각화 | Power BI Desktop | Tableau, Metabase, Superset | BigQuery 네이티브 커넥터, 무료 Desktop 버전 사용 가능, 대시보드 업계 표준 |
| 오케스트레이션 | Python 스크립트 (main.py) | Airflow, Prefect, Dagster | 학습용에 오케스트레이터 과도 (제약사항: 초중급 수준), 일 1회 배치에 script로 충분 |
| AI 질의 (v2) | Claude/OpenAI API | Llama, 로컬 LLM | Text-to-SQL 최적화 성능, API 방식으로 GPU 인프라 불필요, 비용 대비 품질 우수 |

### 10-3. 배포 구성 (Deployment)

> 파이프라인은 로컬 실행과 GitHub Actions 스케줄 실행을 모두 지원합니다. BigQuery가 서버리스이므로 별도 서버 인프라 없이 CI에서 `main.py`를 실행합니다.

| 항목 | 구성 | 비고 |
|---|---|---|
| 실행 환경 | GitHub Actions (`ubuntu-latest` runner) | 인프라 0, 무료 CI |
| 트리거 | `schedule` (cron, 예: 평일 미국장 마감 후) + `workflow_dispatch` (수동 버튼) | cron 지연 허용 (NFR-009 적시성 낮음) |
| 실행 대상 | `python src/main.py` (수집→검증→적재→변환) | Power BI는 자동화 대상 아님 (수동 조회) |
| 워크플로 파일 | `.github/workflows/pipeline.yml` | — |
| 키 관리 | GitHub Secrets — `FRED_API_KEY`, 서비스계정 JSON(`GOOGLE_APPLICATION_CREDENTIALS`용) 주입 | 리포지토리 Secrets에 저장, 로그 마스킹 |
| 오케스트레이터 | Airflow 등 미도입 (ADR-002/006, 초중급 유지) | GitHub Actions로 스케줄링만 확보 |

### 10-4. 횡단 관심사 (Cross-cutting Concerns)

| 관심사 | 접근법 | 비고 |
|---|---|---|
| 로깅 | Python logging 모듈 + 구조화된 포맷 (타임스탬프, 단계, 상태, 건수) | NFR-004 연계 |
| 에러 처리 | 단계별 try-except + 로그 기록 + 다음 단계 계속 진행 | FR-010 + 섹션 4 시나리오 반영 |
| 설정 관리 | .env 파일 + python-dotenv, 종목 목록 등은 config.yaml. BigQuery 인증은 서비스계정 JSON(`GOOGLE_APPLICATION_CREDENTIALS`). CI 실행 시 키는 GitHub Secrets로 주입 | 섹션 1 제약사항 (키 관리) |
| 테스트 전략 | 단위 테스트 (데이터 검증 로직, 변환 로직) + 수동 통합 테스트 | NFR-003 유지보수성, 학습 수준에 맞게 최소화 |

### 10-5. 아키텍처 결정 기록 (ADR)

#### ADR-001: ELT 패턴 선택

**상태**: 채택
**맥락**: BigQuery에 데이터를 적재하는 방식으로 ETL과 ELT 중 선택 필요
**결정**: ELT — raw 데이터를 BigQuery에 먼저 적재하고, BigQuery SQL로 Star Schema 변환
**근거**: BigQuery 서버리스 컴퓨팅을 활용한 SQL 기반 변환이 효율적, Python 수집 코드와 SQL 변환 코드의 역할 분리가 명확, 섹션 2 기존 파이프라인 흐름과 일치
**결과**: 수집(Python) ↔ 변환(SQL) 역할 분리, 클라우드 DW 활용 패턴 학습에 적합

#### ADR-002: Python 스크립트 오케스트레이션

**상태**: 채택
**맥락**: 파이프라인 실행 관리 도구로 Airflow/Prefect 등 전문 오케스트레이터 도입 여부
**결정**: Python 스크립트(main.py) 단일 진입점으로 순차 실행
**근거**: Airflow/Prefect는 초중급 학습 난이도 제약에 부적합 (섹션 1 제약사항), 일 1회 배치 규모에 과도, 모듈 분리(NFR-003)는 Python 패키지 구조로 달성 가능
**결과**: 배포/스케줄링 복잡도 최소화, 오케스트레이터 학습은 이후 별도 프로젝트로 분리 가능

#### ADR-003: Full Refresh 적재 방식

**상태**: 채택 (BigQuery 반영 갱신)
**맥락**: BigQuery raw 데이터셋 적재 시 기존 데이터 처리 방식 (Full Refresh vs Incremental)
**결정**: Full Refresh — `WRITE_TRUNCATE` load job (매 실행 통째로 교체)
**근거**: 학습용 소규모 데이터(수만 건)로 전체 재적재 부담 미미, 중복 체크 로직 불필요로 코드 단순화, 디버깅 시 전체 데이터 상태 일관성 보장. 행 단위 `INSERT`는 BigQuery 안티패턴(쿼터·비용·스트리밍 버퍼)이며, `WRITE_TRUNCATE` load job은 무료이고 테이블을 원자적으로 교체함
**결과**: 매 실행 시 동일한 결과 보장, load job은 BigQuery 무료티어 내에서 비용 없이 수행

#### ADR-004: BigQuery 채택

**상태**: 채택
**맥락**: 데이터 웨어하우스 선택. 학습용이라 비용·크레딧 만료 압박 없이 지속 가능한 플랫폼이 필요
**결정**: BigQuery를 데이터 웨어하우스로 채택
**근거**: 영구 무료티어(월 1TB 쿼리 + 10GB 저장)로 비용·크레딧 만료 압박이 없음, 서버리스라 컴퓨트 관리가 불필요, GCP 생태계 및 GitHub Actions와의 궁합이 좋음, Power BI 네이티브 커넥터 지원
**결과**: 서버리스로 운영 부담 최소화, 무료티어 한도 내에서 학습 지속 가능

#### ADR-005: FARM_FINGERPRINT 대리키

**상태**: 채택
**맥락**: BigQuery에는 AUTOINCREMENT/시퀀스가 없어 dim의 정수 대리키를 자동 생성할 수 없음
**결정**: 대리키(symbol_key, indicator_key)를 `FARM_FINGERPRINT(정규화된 자연키)`(INT64)로 생성, 이벤트 로그 ID(log_id, check_id)는 `GENERATE_UUID()`(STRING)로 생성
**근거**: `FARM_FINGERPRINT`는 결정적 해시라 Full Refresh로 매 실행 dim을 재생성해도 동일한 키가 나옴 → dim/fact 간 키 일관성이 보장되고 시퀀스 상태 조율이 불필요, 자연키가 없는 로그는 UUID로 유일성 확보
**결과**: 정수 대리키를 유지하며 star schema 패턴 학습, 상세 정의는 `docs/data_dictionary.md` 참조

#### ADR-006: GitHub Actions 스케줄링

**상태**: 채택
**맥락**: 일 배치 스케줄이 필요하나 Airflow 등 전문 오케스트레이터는 초중급 제약(ADR-002)에 과함
**결정**: GitHub Actions `schedule`(cron) + `workflow_dispatch`(수동 실행)로 `main.py`(수집→검증→적재→변환)를 실행
**근거**: 무료이고 별도 인프라가 0, GitHub Secrets로 키 관리 가능, Full Refresh의 stateless 특성과 궁합이 좋음(매 실행 통째 교체라 상태 이월 불필요), CI 학습 가치 확보
**결과**: 스케줄링을 확보(cron 지연은 NFR-009 적시성 낮음이라 허용), Power BI 시각화는 자동화 대상에서 제외

#### ADR-007: 동적 유니버스 (ETF 보유종목)

**상태**: 채택
**맥락**: 분석 대상이 S&P 500 + Nasdaq-100(합쳐 수백 종목)인데, 구성종목을 손으로 나열·관리하면 지수 편출입·상장폐지마다 수동 갱신이 필요해 유지가 불가능하고 명단 오류가 누적됨
**결정**: 구성종목을 손으로 나열하지 않고 매 실행마다 ETF 보유종목(IVV=S&P500, QQQ=Nasdaq100)에서 명단을 수집해 `raw_universe`에 적재하고 이를 `dim_symbol`의 소스로 삼는다. 소스는 교체 가능(`etf_holdings` 기본 / `api` / `wikipedia`)하며, 수집 실패 시 직전 성공 명단으로 캐시 폴백
**근거**: 지수 편출입·상장폐지가 매 실행 재수집으로 자동 반영되어 수동 명단관리가 사라짐, 운용사(BlackRock/Invesco)가 매일 공시하는 실제 보유 명세라 권위 있고 신뢰 가능, 무료·API 키 불필요, 섹터(GICS)까지 포함되어 dim_symbol 메타데이터 확보 (Wikipedia는 커뮤니티 편집·비공식이라 배제)
**결과**: 수동 종목 명단 관리가 제거되고 편출입/상폐가 자동 처리됨, 대신 "현재 구성종목"만 분석하므로 생존 편향(survivorship bias)은 학습용으로 감수. 상세는 `docs/data_dictionary.md` 8장 참조

---

## 11. 데이터 모델

> 섹션 3(기초 Star Schema)을 기반으로, BigQuery 타입으로 확장하고 운영 엔티티를 추가한다.
> 상세 정의는 docs/data_dictionary.md 참조

### 11-1. 엔티티 정의 (Entity Definition)

#### Raw Layer

> raw는 "일단 다 받는다"가 원칙 — API가 주는 컬럼(symbol/date/indicator_code 등)은 모두 nullable, Python이 채우는 `source`/`collected_at`만 NOT NULL. (NOT NULL이면 null 한 줄에 `WRITE_TRUNCATE` 배치 전체가 실패하므로, 더러운 데이터는 raw가 흡수하고 정제는 fact 단계에서 수행.)

##### raw_universe

> S&P500+Nasdaq100 구성종목 명단 (ETF 보유종목 IVV/QQQ에서 매 실행 수집). **`dim_symbol`의 소스.** 수집 실패 시 직전 성공 명단으로 캐시 폴백.

| 필드 | 타입 | 제약 | 설명 |
|---|---|---|---|
| ticker | STRING | | 종목 코드 |
| company_name | STRING | | 회사명 |
| sector | STRING | | 섹터 (GICS) |
| market | STRING | | 시장 (US) |
| index_source | STRING | | 출처 지수 (SP500 / NASDAQ100) |
| weight | NUMERIC | | ETF 내 비중 (참고용) |
| source | STRING | NOT NULL | 데이터 소스 (IVV/QQQ) |
| collected_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP() | 수집 시각 |

##### raw_daily_price

| 필드 | 타입 | 제약 | 설명 |
|---|---|---|---|
| symbol | STRING | | 종목 코드 (raw는 nullable) |
| date | DATE | | 거래일 (raw는 nullable) |
| open | NUMERIC | | 시가 |
| high | NUMERIC | | 고가 |
| low | NUMERIC | | 저가 |
| close | NUMERIC | | 종가 |
| adj_close | NUMERIC | | 수정 종가 |
| volume | INT64 | | 거래량 |
| source | STRING | NOT NULL | 데이터 소스 (yfinance/KRX) |
| collected_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP() | 수집 시각 |

##### raw_economic_indicator

| 필드 | 타입 | 제약 | 설명 |
|---|---|---|---|
| indicator_code | STRING | | 지표 코드 (raw는 nullable, 예: FEDFUNDS) |
| date | DATE | | 기준일 (raw는 nullable) |
| value | NUMERIC | | 지표 값 |
| source | STRING | NOT NULL | 데이터 소스 (FRED) |
| collected_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP() | 수집 시각 |

##### raw_technical_indicator (선택 — Alpha Vantage)

| 필드 | 타입 | 제약 | 설명 |
|---|---|---|---|
| symbol | STRING | NOT NULL | 종목 코드 |
| date | DATE | NOT NULL | 기준일 |
| indicator_type | STRING | NOT NULL | 지표 유형 (RSI/MACD 등) |
| value | NUMERIC | | 지표 값 |
| source | STRING | NOT NULL | 데이터 소스 (Alpha Vantage) |
| collected_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP() | 수집 시각 |

#### Star Schema Layer

##### fact_daily_price

| 필드 | 타입 | 제약 | 설명 |
|---|---|---|---|
| date_key | INT64 | FK → dim_date (NOT ENFORCED), NOT NULL | 날짜 키 (YYYYMMDD) |
| symbol_key | INT64 | FK → dim_symbol (NOT ENFORCED), NOT NULL | 종목 키 |
| open_price | NUMERIC | | 시가 |
| high_price | NUMERIC | | 고가 |
| low_price | NUMERIC | | 저가 |
| close_price | NUMERIC | | 종가 |
| adj_close | NUMERIC | | 수정 종가 |
| volume | INT64 | | 거래량 |
| loaded_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP() | 적재 시각 |

##### fact_economic_indicator

| 필드 | 타입 | 제약 | 설명 |
|---|---|---|---|
| date_key | INT64 | FK → dim_date (NOT ENFORCED), NOT NULL | 날짜 키 |
| indicator_key | INT64 | FK → dim_indicator (NOT ENFORCED), NOT NULL | 지표 키 |
| value | NUMERIC | NOT NULL | 지표 값 |
| loaded_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP() | 적재 시각 |

##### dim_date

| 필드 | 타입 | 제약 | 설명 |
|---|---|---|---|
| date_key | INT64 | PK (NOT ENFORCED) | 고유 키 (YYYYMMDD) |
| full_date | DATE | NOT NULL (UNIQUE 미지원 → DISTINCT로 보장) | 전체 날짜 |
| year | INT64 | NOT NULL | 연도 |
| quarter | INT64 | NOT NULL | 분기 |
| month | INT64 | NOT NULL | 월 |
| day_of_week | STRING | NOT NULL | 요일 |
| is_trading_day | BOOL | NOT NULL | 거래일 여부 |

##### dim_symbol

> **소스: `raw_universe`** (S&P500+Nasdaq100 구성종목 명단). raw_daily_price가 아니라 유니버스 명단에서 생성 → **승인 명단(allowlist)** 역할로 명단 밖 종목이 fact inner JOIN에서 걸러짐. 처리: `WHERE ticker IS NOT NULL` → 정규화(UPPER/TRIM) → DISTINCT(두 지수 중복 합침) → `FARM_FINGERPRINT`.

| 필드 | 타입 | 제약 | 설명 |
|---|---|---|---|
| symbol_key | INT64 | PK (NOT ENFORCED) | 고유 키 (`FARM_FINGERPRINT(ticker)`) |
| ticker | STRING | NOT NULL | 종목 코드 (정규화됨, DISTINCT로 유일성 보장) |
| company_name | STRING | | 회사명 |
| sector | STRING | | 섹터 |
| market | STRING | NOT NULL | 시장 (US/KR) |

##### dim_indicator

> 소스: `config/symbols.yaml`의 `indicators` 목록 (손으로 관리하는 seed — 지표는 적고 안정적).

| 필드 | 타입 | 제약 | 설명 |
|---|---|---|---|
| indicator_key | INT64 | PK (NOT ENFORCED) | 고유 키 (`FARM_FINGERPRINT(indicator_code)`) |
| indicator_code | STRING | NOT NULL | 지표 코드 (DISTINCT로 유일성 보장) |
| indicator_name | STRING | NOT NULL | 지표명 |
| source | STRING | NOT NULL | 출처 (FRED/Alpha Vantage) |
| unit | STRING | | 단위 (%, 포인트 등) |

#### Operations Layer

##### pipeline_execution_log

| 필드 | 타입 | 제약 | 설명 |
|---|---|---|---|
| log_id | STRING | PK (NOT ENFORCED), DEFAULT `GENERATE_UUID()` | 고유 ID |
| execution_id | STRING | NOT NULL | 실행 ID (UUID) |
| stage | STRING | NOT NULL | 단계 (universe/collect/validate/load/transform) |
| status | STRING | NOT NULL | 상태 (success/failure/warning) |
| record_count | INT64 | | 처리 건수 |
| error_message | STRING | | 에러 메시지 |
| started_at | TIMESTAMP | NOT NULL | 시작 시각 |
| ended_at | TIMESTAMP | | 종료 시각 |

##### data_quality_log

| 필드 | 타입 | 제약 | 설명 |
|---|---|---|---|
| check_id | STRING | PK (NOT ENFORCED), DEFAULT `GENERATE_UUID()` | 고유 ID |
| execution_id | STRING | NOT NULL | 실행 ID (pipeline_execution_log 연계) |
| check_type | STRING | NOT NULL | 검증 유형 (missing/outlier/duplicate/completeness/universe) |
| target_table | STRING | NOT NULL | 대상 테이블 |
| target_field | STRING | | 대상 필드 |
| result | STRING | NOT NULL | 결과 (pass/warn/fail) |
| detail | STRING | | 상세 내용 |
| checked_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP() | 검증 시각 |

#### Mart Layer (View)

| View | 기반 테이블 | 주요 계산 |
|---|---|---|
| mart_performance | fact_daily_price + dim_symbol + dim_date | LAG()로 일간/주간/월간 수익률, 누적 수익률 |
| mart_risk | fact_daily_price + dim_symbol | STDDEV()로 변동성, 최대 낙폭, 베타 계산 |
| mart_macro | fact_economic_indicator + fact_daily_price + dim_date | CORR()로 금리-주가 상관관계, 경제지표 영향도 |

### 11-2. 관계 (Relationships)

| 소스 | 대상 | 관계 | 설명 |
|---|---|---|---|
| dim_symbol | raw_universe | 파생 | dim_symbol이 raw_universe(구성종목 명단)에서 생성됨 (ticker 기준 DISTINCT) |
| fact_daily_price | dim_date | N:1 | date_key FK — 하나의 날짜에 여러 종목 |
| fact_daily_price | dim_symbol | N:1 | symbol_key FK — 하나의 종목에 여러 날짜 |
| fact_economic_indicator | dim_date | N:1 | date_key FK |
| fact_economic_indicator | dim_indicator | N:1 | indicator_key FK |
| data_quality_log | pipeline_execution_log | N:1 | execution_id 연계 — 한 실행에 여러 검증 |

### 11-3. 정합성 규칙 (Integrity Rules)

| ID | 규칙 | 대상 | 검증 시점 |
|---|---|---|---|
| IR-001 | 필수 필드 NOT NULL | fact_daily_price.date_key, symbol_key | 적재 시 |
| IR-002 | 날짜-종목 복합 유니크 (UNIQUE 미지원 → QUALIFY ROW_NUMBER 중복제거) | fact_daily_price (date_key + symbol_key) | 변환 시 |
| IR-003 | 날짜-지표 복합 유니크 (UNIQUE 미지원 → QUALIFY ROW_NUMBER 중복제거) | fact_economic_indicator (date_key + indicator_key) | 변환 시 |
| IR-004 | FK 참조 무결성 (inner JOIN, NOT ENFORCED) — dim이 유니버스/seed 명단에서 생성되어 명단 밖 종목·null이 실제로 걸러짐 | fact → dim 테이블 모든 FK | 변환 시 |
| IR-005 | 수집-적재 건수 일치 | raw 테이블 건수 = API 수집 건수 | 배치 완료 시 (NFR-008) |
| IR-006 | 가격 양수 검증 | raw_daily_price.close > 0 | 수집 시 (FR-009) |
| IR-007 | date_key 형식 검증 | dim_date.date_key: YYYYMMDD 8자리 정수 | 적재 시 |
| IR-008 | 승인 종목 완전성 | 명단(dim_symbol) 종목의 수집 0건 → 상폐 의심 completeness 경고 | 검증 시 (FR-009) |

### 11-4. 데이터 생명주기 (Data Lifecycle)

| 데이터 | 생성 시점 | 갱신 주기 | 보관 기간 | 삭제 정책 |
|---|---|---|---|---|
| raw_universe | 배치 유니버스 수집 시 | Full Refresh (매 실행 재수집 → 편출입/상폐 자동 반영) | 최신 명단 유지 | WRITE_TRUNCATE (수집 실패 시 직전 명단 유지 — 캐시 폴백) |
| raw_* 테이블 | 배치 수집 시 | Full Refresh (매 실행) | 전체 재적재 (API가 전체 이력 제공, 별도 보관 정책 불필요) | WRITE_TRUNCATE load job |
| fact_* 테이블 | Star Schema 변환 시 | CTAS 재생성 (매 실행) | 영구 보관 | CREATE OR REPLACE TABLE AS SELECT로 재생성 |
| dim_* 테이블 | 초기 세팅 + 변환 시 | 신규 종목/지표 추가 시 | 영구 보관 | 삭제 없음 (누적) |
| mart_* View | View 생성 시 | 조회 시 (View는 기반 테이블을 조회 시점에 읽음) | — | View이므로 별도 정책 불필요 |
| pipeline_execution_log | 파이프라인 실행 시 | 매 실행마다 load job (append) | 영구 보관 | 삭제 없음 (누적) |
| data_quality_log | 품질 검증 시 | 매 실행마다 load job (append) | 영구 보관 | 삭제 없음 (누적) |

### 11-5. 마이그레이션/진화 전략

> 학습 목적 프로젝트로 정식 마이그레이션 도구(Alembic, Flyway 등)는 비활성합니다.
> 스키마 변경 시 BigQuery SQL 스크립트를 직접 실행하여 관리합니다.

**초기화 전략**: `setup.sql` 스크립트로 전체 스키마 생성 (CREATE OR REPLACE)

---

## 12. AI 워크플로우

> v2 기능 (Text-to-SQL 자연어 질의). LLM 기반 프롬프트 엔지니어링 패턴.

**워크플로우:**
```
자연어 질문 → 입력 검증 → 스키마 컨텍스트 조립 → LLM (SQL 생성) → SQL 검증 → BigQuery 실행 → LLM (결과 해석) → 응답
                                                      ↓ (실패 시)
                                                 폴백 처리
```

### 12-1. AI 입출력 정의 (AI I/O Definition)

| ID | 기능 | 입력 | 출력 | 입력 검증 | 출력 후처리 |
|---|---|---|---|---|---|
| AI-IO-001 | Text-to-SQL 변환 | 자연어 질문 (string, max 500자) | BigQuery Standard SQL 쿼리 (string) | 빈 문자열 체크, 길이 제한 | SQL 파싱 검증, SELECT만 허용 (DML/DDL 차단) |
| AI-IO-002 | 결과 해석 | SQL 쿼리 + 실행 결과 (JSON, max 50행) | 자연어 해석 (string, 한국어) | 결과 행 수 제한 (50행, 토큰 초과 방지) | 없음 |

### 12-2. 프롬프트 설계 (Prompt Design)

#### 프롬프트 1: Text-to-SQL 변환

| 항목 | 내용 |
|---|---|
| 목적 | 자연어 금융 데이터 질문을 BigQuery Standard SQL로 변환 |
| 시스템 프롬프트 | BigQuery Standard SQL 전문가 역할. Star Schema 구조(Fact 2, Dim 3, Mart 3)를 이해하고, SELECT 문만 생성. 한국어/영어 질문 모두 처리. DML/DDL 절대 생성 금지 |
| 사용자 프롬프트 템플릿 | `스키마:\n{schema_info}\n\n질문: {user_question}\n\n위 스키마를 기반으로 BigQuery Standard SQL을 생성하세요.` |
| 출력 형식 | SQL (코드 블록) |
| 예상 토큰 | 입력: ~800 / 출력: ~200 |
| 온도 | 0.0 (결정적 SQL 생성) |

#### 프롬프트 2: 결과 해석

| 항목 | 내용 |
|---|---|
| 목적 | SQL 실행 결과를 한국어로 해석하여 인사이트 제공 |
| 시스템 프롬프트 | 금융 데이터 분석가 역할. 숫자는 천 단위 구분, 퍼센트 변환, 트렌드 해석 포함. 간결하고 명확한 한국어로 답변 |
| 사용자 프롬프트 템플릿 | `질문: {original_question}\n\nSQL:\n{sql_query}\n\n결과:\n{query_results}\n\n위 결과를 한국어로 설명하세요.` |
| 출력 형식 | 텍스트 (한국어) |
| 예상 토큰 | 입력: ~500 / 출력: ~300 |
| 온도 | 0.3 (자연스러운 해석) |

### 12-3. 모델 선택 (Model Selection)

**모델 설정**: `.env` 파일의 `AI_MODEL` 변수로 관리
- 기본값: `claude-haiku-4-5-latest` (자동 마이너 업데이트)
- 고품질: `claude-sonnet-4-6-latest`
- 구체 버전 고정도 가능: `claude-haiku-4-5-20251001`

| 기능 | 모델 | 선택 이유 | 대안 | 비용 추정 |
|---|---|---|---|---|
| Text-to-SQL | Claude Haiku (기본) / Claude Sonnet (고품질) | 설정으로 전환 가능. Haiku: 빠르고 저렴, Sonnet: 복잡한 쿼리 품질 우수 | GPT-4o-mini | Haiku ~$0.003 / Sonnet ~$0.012 per query |
| 결과 해석 | Claude Haiku (기본) / Claude Sonnet (고품질) | 자연어 생성은 Haiku도 충분. Sonnet은 더 정교한 해석 | GPT-4o-mini | Haiku ~$0.002 / Sonnet ~$0.008 per query |

**월간 비용 추정** ($10 예산):

| 모드 | 쿼리당 비용 | 월 가능 쿼리 수 |
|---|---|---|
| Haiku 전용 | ~$0.005 | ~2,000회 |
| Sonnet 전용 | ~$0.020 | ~500회 |
| 혼합 (Haiku 기본 + Sonnet 필요 시) | ~$0.008 평균 | ~1,200회 |

### 12-4. 폴백 및 에러 처리 (Fallback & Error Handling)

| 시나리오 | 감지 조건 | 폴백 동작 | 사용자 메시지 |
|---|---|---|---|
| API 타임아웃 | 응답 > 30초 | 1회 재시도 → 에러 반환 | "AI 서버 응답이 지연되고 있습니다. 잠시 후 다시 시도하세요." |
| 잘못된 SQL 생성 | BigQuery 실행 에러 | 에러 메시지 포함하여 1회 재생성 → 실패 시 에러 반환 | "SQL 생성에 실패했습니다. 질문을 더 구체적으로 바꿔보세요." |
| DML/DDL 시도 | SQL 파싱 시 SELECT 이외 감지 | 차단, 재생성 없음 | "조회(SELECT) 질문만 지원합니다." |
| 월간 비용 한도 | API 비용 누적 ≥ $10 | AI 기능 비활성화 | "이번 달 AI 사용량 한도($10)에 도달했습니다." |
| 결과 과다 | 쿼리 결과 > 50행 | LIMIT 50 강제 추가 | "결과가 많아 상위 50건만 표시합니다." |

### 12-5. 평가 및 모니터링 (Evaluation & Monitoring)

| 지표 | 측정 방법 | 목표치 | 모니터링 주기 |
|---|---|---|---|
| SQL 실행 성공률 | 생성 SQL의 BigQuery 실행 성공/실패 비율 | > 80% | 수동 (학습 시) |
| 응답 시간 | API 호출 ~ 결과 표시 end-to-end 지연 | < 15초 | 수동 |
| 월간 비용 | API 호출 비용 누적 | ≤ $10/월 | 월 1회 |
| 쿼리 품질 | 생성 SQL이 의도한 데이터를 반환하는지 수동 검증 | 주관적 만족 | 수동 |

---

## 13. 구현 명세

> 섹션 9-12를 종합하여 개발 착수에 필요한 프로젝트 구조와 환경 설정을 정의한다.

### 13-1. 프로젝트 구조 (Project Structure)

```
finance_data_platform/
├── src/
│   ├── collectors/                  # 데이터 수집 모듈
│   │   ├── __init__.py
│   │   ├── universe_collector.py    # 유니버스 수집 (ETF IVV/QQQ → raw_universe, dim_symbol 소스)
│   │   ├── yfinance_collector.py    # 미국 주가 수집
│   │   ├── fred_collector.py        # FRED 경제지표 수집
│   │   └── alpha_vantage_collector.py  # 기술지표 수집 (선택)
│   ├── validators/                  # 데이터 품질 검증
│   │   ├── __init__.py
│   │   └── quality_checker.py       # 결측/이상치/중복 검증
│   ├── loaders/                     # BigQuery 적재
│   │   ├── __init__.py
│   │   └── bigquery_loader.py       # raw WRITE_TRUNCATE Full Refresh 적재
│   ├── transformers/                # Star Schema 변환
│   │   ├── __init__.py
│   │   └── star_schema.py           # CTAS 변환 + Mart View 생성
│   ├── ai/                          # Text-to-SQL AI (v2)
│   │   ├── __init__.py
│   │   ├── text_to_sql.py           # SQL 생성 + 결과 해석
│   │   └── prompts/                 # 프롬프트 템플릿
│   │       ├── sql_generation.txt
│   │       └── result_interpretation.txt
│   ├── utils/                       # 공통 유틸리티
│   │   ├── __init__.py
│   │   ├── logger.py                # 구조화된 로깅 + BigQuery 로그 적재
│   │   └── config.py                # 설정 로딩 (.env + yaml)
│   └── main.py                      # 파이프라인 단일 진입점
├── sql/
│   ├── setup.sql                    # BigQuery 스키마 초기화 (전체 테이블)
│   └── mart_views.sql               # Mart View 정의 (performance/risk/macro)
├── tests/                           # 단위 테스트 (선택 — 학습 시 작성)
├── docs/
│   └── data_dictionary.md           # 데이터 사전 (FR-011, 작성 완료 — BigQuery 정본)
├── config/
│   └── symbols.yaml                 # 유니버스 소스(sp500/nasdaq100) + FRED indicators + settings (개별종목 나열 X)
├── .github/
│   └── workflows/
│       └── pipeline.yml             # GitHub Actions 스케줄 (cron + workflow_dispatch)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

### 13-2. 환경 설정 (Configuration)

| 변수 | 기본값 | 설명 | 필수 |
|---|---|---|---|
| GCP_PROJECT_ID | — | GCP 프로젝트 ID | Y |
| BQ_DATASET | finance_db | BigQuery 데이터셋명 | Y |
| BQ_LOCATION | US | BigQuery 데이터셋 위치 (예: US) | Y |
| GOOGLE_APPLICATION_CREDENTIALS | — | 서비스계정 JSON 키 파일 경로 | Y |
| FRED_API_KEY | — | FRED API 키 | Y |
| ALPHA_VANTAGE_API_KEY | — | Alpha Vantage API 키 | N (선택) |
| AI_MODEL | claude-haiku-4-5-latest | Claude 모델 ID | N (v2) |
| ANTHROPIC_API_KEY | — | Anthropic API 키 | N (v2) |
| AI_MONTHLY_BUDGET | 10 | 월간 AI API 예산 ($) | N (v2) |
| LOG_LEVEL | INFO | 로그 레벨 | N |

#### .env.example

```
# BigQuery (GCP)
GCP_PROJECT_ID=your_gcp_project_id
BQ_DATASET=finance_db
BQ_LOCATION=US
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service_account.json

# API Keys
FRED_API_KEY=your_fred_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# AI (v2)
AI_MODEL=claude-haiku-4-5-latest
ANTHROPIC_API_KEY=your_anthropic_key
AI_MONTHLY_BUDGET=10

# Logging
LOG_LEVEL=INFO
```

#### config/symbols.yaml

개별 종목을 나열하지 않고 **유니버스 소스 + 지표(seed) + 설정**만 담습니다 (docs/data_dictionary.md 8장과 동일):

```yaml
universe:
  sp500:     { enabled: true, source: etf_holdings, etf: IVV }
  nasdaq100: { enabled: true, source: etf_holdings, etf: QQQ }
  include_extra: []      # 지수에 없지만 꼭 넣을 티커
  exclude:       []      # 강제 제외 티커 (탈출구)

indicators:              # FRED 지표는 손으로 나열 (적고 안정적) → dim_indicator seed
  - { code: FEDFUNDS, name: Federal Funds Rate,   unit: "%",   source: FRED }
  - { code: CPIAUCSL, name: Consumer Price Index, unit: index, source: FRED }

settings:
  date_range: { start: "2020-01-01" }
```

### 13-3. 개발 범위 (Development Scope)

> 상세 Phase 계획 및 시나리오 테스트는 별도 스킬로 작성 예정.

| 범위 | 포함 FR | 설명 |
|---|---|---|
| **MVP** | FR-001,002,004,005,006,007,009,010,011,012 | 유니버스 수집 → 데이터 수집 → 적재 → 변환 → 시각화 + 품질검증/로깅/문서 |
| **v2** | FR-003, FR-008 | Alpha Vantage 기술지표 + Text-to-SQL AI 질의 |

---

## Revision History

| 날짜 | 섹션 | 변경 내용 | 스킬 |
|---|---|---|---|
| 2026-05-12 | 섹션 9 | 요구사항 정의 최초 작성 (FR 11개, NFR 9개) | design-requirements |
| 2026-05-12 | 섹션 10 | 시스템 아키텍처 상세 최초 작성 (컴포넌트 9개, ADR 3개) | design-architecture |
| 2026-05-12 | 섹션 11 | 데이터 모델 최초 작성 (엔티티 10개, 관계 5개, 정합성 규칙 7개) | design-data-model |
| 2026-05-12 | 섹션 12 | AI 워크플로우 최초 작성 (AI I/O 2개, 프롬프트 2개, 모델 2개) | design-ai-workflow |
| 2026-05-12 | 섹션 13 | 구현 명세 최초 작성 (프로젝트 구조 + 환경 설정) | design-impl-spec |
| 2026-05-12 | 섹션 1,4,9,10,11 | 교차 정합성 수정 8건 (NFR-001 범위, 핵심 기능 행 분리, 결과 형태 MVP/v2 분리, KPI#5 범위 외, 사용자 흐름 진입점, 실패 시나리오 재시도, Logger 저장소 명확화, raw 보관 정책) | 수동 점검 |
| 2026-07-06 | 전체 | BigQuery 기준 정비: 플랫폼/대리키(FARM_FINGERPRINT)/적재(WRITE_TRUNCATE)/GitHub Actions 스케줄링/타입·제약 반영, ADR-004~006 추가·ADR-003 갱신 | 수동 개정 |
| 2026-07-06 | 섹션 1,2,3,9,10,11,13 | 동적 유니버스(S&P500+Nasdaq100, ETF 보유종목 IVV/QQQ) 도입 — `raw_universe`/`universe_collector` 추가, `dim_symbol` 소스 변경(→raw_universe), raw 컬럼 nullable, `symbols.yaml` 구조, IR-008(완전성), ADR-007 | 수동 개정 |
