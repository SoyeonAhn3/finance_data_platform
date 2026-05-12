# Phase 5 — Power BI Dashboard `🔲 Not Started`

> Connect Power BI to Snowflake Mart Views and build KPI visualization dashboard

**Status**: 🔲 Not Started
**Prerequisites**: Phase 4 completion (Mart Views created and verified)

---

## Overview

Connect Power BI Desktop to Snowflake Mart Views and build an interactive dashboard displaying key financial KPIs: returns, volatility, trading volume trends, and sector comparison. Users can filter by date range and stock ticker.

---

## Deliverables

| # | Item | Status | Type |
|---|---|---|---|
| 1 | Power BI → Snowflake connection setup | 🔲 | project-specific |
| 2 | Data model in Power BI (import Mart Views) | 🔲 | project-specific |
| 3 | Returns chart (daily/weekly/monthly) | 🔲 | project-specific |
| 4 | Volatility chart | 🔲 | project-specific |
| 5 | Trading volume trend chart | 🔲 | project-specific |
| 6 | Sector comparison chart | 🔲 | project-specific |
| 7 | Date filter (slicer) | 🔲 | project-specific |
| 8 | Ticker filter (slicer) | 🔲 | project-specific |
| 9 | Macro indicator overlay (optional) | 🔲 | project-specific |
| 10 | `docs/data_dictionary.md` (FR-011) | 🔲 | project-specific |

---

## Dashboard Details

### Connection Setup

| Setting | Value |
|---|---|
| Connector | Snowflake (native) |
| Server | `{SNOWFLAKE_ACCOUNT}.snowflakecomputing.com` |
| Warehouse | XS_WH |
| Database | FINANCE_DB |
| Data source | Mart Views (mart_performance, mart_risk, mart_macro) |

### KPI Charts (FR-007)

#### 1. Returns Analysis (mart_performance)
- **Chart type**: Line chart
- **X-axis**: Date
- **Y-axis**: Daily / weekly / monthly return (%)
- **Legend**: Ticker
- **Filters**: Date range slicer, ticker slicer

#### 2. Volatility Analysis (mart_risk)
- **Chart type**: Bar chart / Card
- **Metrics**: Standard deviation, max drawdown
- **Grouping**: By ticker
- **Filters**: Date range slicer

#### 3. Trading Volume Trend (mart_performance)
- **Chart type**: Area chart
- **X-axis**: Date
- **Y-axis**: Volume
- **Legend**: Ticker

#### 4. Sector Comparison (mart_performance + dim_symbol)
- **Chart type**: Clustered bar chart
- **X-axis**: Sector
- **Y-axis**: Average return (%)
- **Filters**: Date range

#### 5. Macro Overlay (mart_macro) — Optional
- **Chart type**: Dual-axis line chart
- **Primary axis**: Stock price / return
- **Secondary axis**: Interest rate / CPI
- **Purpose**: Visualize macro-stock correlation

### Filters / Slicers

| Filter | Type | Source |
|---|---|---|
| Date range | Date slicer | dim_date |
| Ticker | Dropdown | dim_symbol |
| Sector | Dropdown | dim_symbol |

### Data Dictionary (FR-011)

Create `docs/data_dictionary.md` documenting:
- All tables/views with descriptions
- Column definitions, types, and calculations
- Data source mapping (which API feeds which table)
- Mart View calculation formulas (LAG, STDDEV, CORR)

---

## Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Power BI data mode | DirectQuery or Import | Import for small data (better performance), DirectQuery if data grows |
| Dashboard layout | Single page with filters | Simple, all KPIs visible at once |
| Macro overlay | Optional | Core KPIs work without it, adds complexity |
| Data dictionary format | Markdown file | Version-controlled, readable without special tools |

---

## Prerequisites & Dependencies

- Phase 4 completed (all 3 Mart Views return data)
- Power BI Desktop installed
- Snowflake ODBC driver or native connector configured
- Snowflake account active with XS warehouse

---

## Development Notes

- Power BI `.pbix` file should be saved in project root or a dedicated `reports/` directory
- `.pbix` files are binary — git tracks them but diff is not meaningful
- Test each chart with sample data before finalizing layout
- Dashboard is read-only — no write-back to Snowflake
- Data dictionary should be maintained as schema evolves

---

## Change Log

| Date | Description |
|---|---|
| 2026-05-12 | Initial creation |

---
---

# Phase 5 — Power BI 대시보드 `🔲 미시작`

> Power BI를 Snowflake Mart View에 연결하고 KPI 시각화 대시보드 구축

**상태**: 🔲 미시작
**선행 조건**: Phase 4 완료 (Mart View 생성 및 검증 완료)

---

## 개요

Power BI Desktop을 Snowflake Mart View에 연결하고, 핵심 금융 KPI(수익률, 변동성, 거래량 추이, 섹터 비교)를 시각화하는 대화형 대시보드를 구축한다. 사용자는 날짜 범위와 종목으로 필터링할 수 있다.

---

## 완료 예정 / 완료 항목

| # | 항목 | 상태 | 타입 |
|---|---|---|---|
| 1 | Power BI → Snowflake 연결 설정 | 🔲 | project-specific |
| 2 | Power BI 데이터 모델 (Mart View 가져오기) | 🔲 | project-specific |
| 3 | 수익률 차트 (일간/주간/월간) | 🔲 | project-specific |
| 4 | 변동성 차트 | 🔲 | project-specific |
| 5 | 거래량 추이 차트 | 🔲 | project-specific |
| 6 | 섹터 비교 차트 | 🔲 | project-specific |
| 7 | 날짜 필터 (슬라이서) | 🔲 | project-specific |
| 8 | 종목 필터 (슬라이서) | 🔲 | project-specific |
| 9 | 매크로 지표 오버레이 (선택) | 🔲 | project-specific |
| 10 | `docs/data_dictionary.md` (FR-011) | 🔲 | project-specific |

---

## 대시보드 상세

### 연결 설정

| 설정 | 값 |
|---|---|
| 커넥터 | Snowflake (네이티브) |
| 서버 | `{SNOWFLAKE_ACCOUNT}.snowflakecomputing.com` |
| 웨어하우스 | XS_WH |
| 데이터베이스 | FINANCE_DB |
| 데이터 소스 | Mart View (mart_performance, mart_risk, mart_macro) |

### KPI 차트 (FR-007)

#### 1. 수익률 분석 (mart_performance)
- **차트 유형**: 꺾은선형 차트
- **X축**: 날짜
- **Y축**: 일간 / 주간 / 월간 수익률 (%)
- **범례**: 종목
- **필터**: 날짜 범위 슬라이서, 종목 슬라이서

#### 2. 변동성 분석 (mart_risk)
- **차트 유형**: 막대 차트 / 카드
- **지표**: 표준편차, 최대 낙폭
- **그룹**: 종목별
- **필터**: 날짜 범위 슬라이서

#### 3. 거래량 추이 (mart_performance)
- **차트 유형**: 영역 차트
- **X축**: 날짜
- **Y축**: 거래량
- **범례**: 종목

#### 4. 섹터 비교 (mart_performance + dim_symbol)
- **차트 유형**: 묶은 세로 막대형 차트
- **X축**: 섹터
- **Y축**: 평균 수익률 (%)
- **필터**: 날짜 범위

#### 5. 매크로 오버레이 (mart_macro) — 선택
- **차트 유형**: 이중축 꺾은선형 차트
- **기본축**: 주가 / 수익률
- **보조축**: 금리 / CPI
- **목적**: 매크로-주가 상관관계 시각화

### 필터 / 슬라이서

| 필터 | 유형 | 소스 |
|---|---|---|
| 날짜 범위 | 날짜 슬라이서 | dim_date |
| 종목 | 드롭다운 | dim_symbol |
| 섹터 | 드롭다운 | dim_symbol |

### 데이터 사전 (FR-011)

`docs/data_dictionary.md` 생성:
- 전체 테이블/뷰 설명
- 컬럼 정의, 타입, 계산식
- 데이터 소스 매핑 (어떤 API가 어떤 테이블에 적재되는지)
- Mart View 계산 공식 (LAG, STDDEV, CORR)

---

## 설계 결정 사항

| 결정 | 선택 | 이유 |
|---|---|---|
| Power BI 데이터 모드 | DirectQuery 또는 Import | 소규모 데이터는 Import (성능 우수), 데이터 증가 시 DirectQuery |
| 대시보드 레이아웃 | 필터 포함 단일 페이지 | 단순, 모든 KPI를 한눈에 확인 |
| 매크로 오버레이 | 선택 사항 | 핵심 KPI 없이도 동작, 복잡도 증가 |
| 데이터 사전 형식 | Markdown 파일 | 버전 관리 가능, 특별한 도구 없이 읽기 가능 |

---

## 선행 조건 및 의존성

- Phase 4 완료 (3개 Mart View 모두 데이터 반환)
- Power BI Desktop 설치 완료
- Snowflake ODBC 드라이버 또는 네이티브 커넥터 설정
- Snowflake 계정 활성 (XS warehouse)

---

## 개발 시 주의사항

- Power BI `.pbix` 파일은 프로젝트 루트 또는 `reports/` 디렉토리에 저장
- `.pbix` 파일은 바이너리 — git 추적은 되지만 diff는 무의미
- 레이아웃 확정 전 샘플 데이터로 각 차트 테스트
- 대시보드는 읽기 전용 — Snowflake에 write-back 없음
- 데이터 사전은 스키마 변경 시 함께 유지보수

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-12 | 최초 작성 |
