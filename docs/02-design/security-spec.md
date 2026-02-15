# Security Audit Report - KPI Auto Report (Athome)

**Date**: 2026-02-15
**Auditor**: Security Architect Agent
**Scope**: Full project security review (OWASP Top 10 + secrets detection)
**Project**: E:\프로젝트\KPI_Auto_Report(Athome)

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| Critical | 2 | Immediate action required - credential exposure |
| High     | 3 | Fix before next release |
| Medium   | 3 | Fix in next sprint |
| Low      | 4 | Track in backlog |
| **Total** | **12** | |

---

## Critical Issues

### [SEC-001] Supabase Anon Key Hardcoded in Git-Tracked File

- **Severity**: Critical
- **OWASP**: A02 - Cryptographic Failures / A07 - Identification and Authentication Failures
- **File**: `E:\프로젝트\KPI_Auto_Report(Athome)\n8n\workflow.json`
- **Lines**: 30, 34, 63, 67, 96, 100, 129, 133
- **Description**: Real Supabase `anon` JWT token이 `n8n/workflow.json`에 8회 반복 하드코딩되어 있었음. **[FIXED]** 플레이스홀더로 교체 완료.
- **Impact**: GitHub에 push된 경우, 누구든 이 토큰으로 Supabase REST API에 접근하여 `anon` 권한으로 데이터 조회/변경 가능. Supabase RLS(Row Level Security)가 미설정 시 전체 테이블 접근 가능.
- **Evidence**:
  ```json
  // n8n/workflow.json:30
  "value": "YOUR_SUPABASE_ANON_KEY"  // [REDACTED]
  ```
- **Remediation**:
  1. `n8n/workflow.json`의 모든 토큰을 `YOUR_SUPABASE_ANON_KEY` 플레이스홀더로 교체 (workflow_complete.json처럼)
  2. Git 이력에서 토큰 제거: `git filter-branch` 또는 `BFG Repo-Cleaner` 사용
  3. Supabase 대시보드에서 anon key 로테이션 (기존 키 무효화)
  4. `n8n/workflow.json`을 `.gitignore`에 추가하거나, 시크릿이 없는 버전만 커밋

### [SEC-002] Real Credentials in .env File (Local Exposure Risk)

- **Severity**: Critical
- **OWASP**: A02 - Cryptographic Failures
- **File**: `E:\프로젝트\KPI_Auto_Report(Athome)\.env`
- **Lines**: 6, 10, 13, 18-19
- **Description**: `.env` 파일에 실제 운영 크리덴셜이 포함:
  - `POSTGRES_PASSWORD=***REDACTED***` (DB 비밀번호)
  - `SUPABASE_ANON_KEY=***REDACTED***` (JWT 토큰)
  - `SLACK_WEBHOOK_URL=***REDACTED***` (실제 Slack 웹훅)
  - `N8N_BASIC_AUTH_PASSWORD=***REDACTED***` (디폴트 비밀번호)
- **Positive**: `.env`는 `.gitignore`에 포함되어 있어 git 커밋 대상은 아님.
- **Risk**: 로컬 머신 침해, 백업 유출, 실수로 `.gitignore` 제거 시 노출.
- **Remediation**:
  1. `N8N_BASIC_AUTH_PASSWORD`를 `changeme`에서 강력한 비밀번호로 변경
  2. 가능하면 Supabase service_role key 대신 anon key만 사용 + RLS 정책 적용
  3. Slack webhook URL 주기적 로테이션

---

## High Issues

### [SEC-003] TLS Verification Disabled in Docker

- **Severity**: High
- **OWASP**: A02 - Cryptographic Failures
- **File**: `E:\프로젝트\KPI_Auto_Report(Athome)\docker-compose.yml`
- **Line**: 18
- **Description**: `NODE_TLS_REJECT_UNAUTHORIZED=0` 설정으로 Node.js의 모든 TLS 인증서 검증이 비활성화됨.
- **Impact**: MITM(Man-in-the-Middle) 공격에 취약. n8n에서 Supabase/Slack으로 보내는 모든 HTTPS 요청의 인증서가 검증되지 않아, 공격자가 중간에서 API 키와 데이터를 가로챌 수 있음.
- **Evidence**:
  ```yaml
  # docker-compose.yml:18
  - NODE_TLS_REJECT_UNAUTHORIZED=0
  ```
- **Remediation**:
  1. `NODE_TLS_REJECT_UNAUTHORIZED=0`을 제거
  2. 인증서 문제가 있다면 올바른 CA 인증서를 추가하거나 `NODE_EXTRA_CA_CERTS` 환경변수 사용

### [SEC-004] Weak Default n8n Admin Password

- **Severity**: High
- **OWASP**: A07 - Identification and Authentication Failures
- **File**: `E:\프로젝트\KPI_Auto_Report(Athome)\.env` (Line 19), `docker-compose.yml` (Line 13)
- **Description**: n8n 관리자 비밀번호가 `changeme` (디폴트 값). docker-compose에서도 fallback으로 `changeme`를 사용.
- **Impact**: n8n 대시보드에 누구든 접근하여 워크플로우 수정/실행 가능. 워크플로우에 포함된 API 키 탈취, 악의적 코드 실행, 데이터 유출.
- **Evidence**:
  ```env
  # .env:19
  N8N_BASIC_AUTH_PASSWORD=changeme
  ```
  ```yaml
  # docker-compose.yml:13
  - N8N_BASIC_AUTH_PASSWORD=${N8N_BASIC_AUTH_PASSWORD:-changeme}
  ```
- **Remediation**:
  1. `.env`에서 `N8N_BASIC_AUTH_PASSWORD`를 최소 16자 이상의 강력한 비밀번호로 변경
  2. docker-compose의 fallback 값 `changeme`도 제거하고 환경변수 필수 설정으로 변경

### [SEC-005] Supabase RLS (Row Level Security) 미확인

- **Severity**: High
- **OWASP**: A01 - Broken Access Control
- **Files**: `E:\프로젝트\KPI_Auto_Report(Athome)\schema\brand_daily_sales.sql`, `products.sql`, `market_competitors.sql`, `ab_test_sample.sql`
- **Description**: 4개 테이블 모두 `CREATE TABLE` 후 RLS(Row Level Security) 정책이 정의되어 있지 않음. `anon` 키로 REST API를 호출하면 모든 데이터에 대해 읽기/쓰기가 가능할 수 있음.
- **Impact**: anon key가 노출된 상황(SEC-001)에서 임의의 사용자가 매출 데이터 조회, 변조, 삭제 가능.
- **Evidence**: SQL 파일에 `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`, `CREATE POLICY` 구문 없음.
- **Remediation**:
  1. 모든 테이블에 RLS 활성화:
     ```sql
     ALTER TABLE brand_daily_sales ENABLE ROW LEVEL SECURITY;
     ALTER TABLE products ENABLE ROW LEVEL SECURITY;
     ALTER TABLE market_competitors ENABLE ROW LEVEL SECURITY;
     ALTER TABLE ab_test_results ENABLE ROW LEVEL SECURITY;
     ```
  2. 필요한 최소 권한만 허용하는 정책 생성 (읽기 전용 정책 등)
  3. 쓰기 작업은 `service_role` 키 사용 (서버 사이드에서만)

---

## Medium Issues

### [SEC-006] Python HTTP 요청 시 SSL 검증 미명시

- **Severity**: Medium
- **OWASP**: A02 - Cryptographic Failures
- **File**: `E:\프로젝트\KPI_Auto_Report(Athome)\crawlers\supabase_loader.py`
- **Lines**: 51, 88, 111, 143, 170, 197
- **Description**: `requests.post()` / `requests.get()` 호출 시 `verify=True`가 명시되지 않음. requests 라이브러리 기본값은 `True`이므로 현재 안전하지만, 명시적으로 지정하는 것이 방어적 프로그래밍.
- **Remediation**: 모든 requests 호출에 `verify=True` 명시 권장

### [SEC-007] Error Logging에서 잠재적 정보 노출

- **Severity**: Medium
- **OWASP**: A09 - Security Logging and Monitoring Failures
- **Files**:
  - `E:\프로젝트\KPI_Auto_Report(Athome)\crawlers\supabase_loader.py` (Lines 62, 94, 122, 150, 176, 202)
  - `E:\프로젝트\KPI_Auto_Report(Athome)\crawlers\coupang_crawler.py` (Line 55)
  - `E:\프로젝트\KPI_Auto_Report(Athome)\crawlers\naver_crawler.py` (Line 71)
- **Description**: `except requests.RequestException as e` 에서 `e` 객체를 직접 로그에 출력. HTTP 에러 응답에 API 키, 토큰, 내부 URL 등이 포함될 수 있음. 특히 Supabase 에러 응답에는 서버 내부 정보가 포함될 수 있음.
- **Evidence**:
  ```python
  # supabase_loader.py:62
  logger.error(f"[Supabase] 배치 {batch_num} 적재 실패: {e}")
  ```
- **Remediation**:
  1. 에러 메시지에서 민감 정보 필터링
  2. 디버그 레벨에서만 full traceback 출력, INFO/ERROR 레벨에서는 요약 메시지만

### [SEC-008] n8n Crawler Workflow의 Command Injection 가능성

- **Severity**: Medium
- **OWASP**: A03 - Injection
- **File**: `E:\프로젝트\KPI_Auto_Report(Athome)\n8n\workflow_crawler.json`
- **Line**: 24
- **Description**: `Execute Command` 노드에서 `cd /app && python -m crawlers.main --all` 고정 명령어를 실행. 현재는 하드코딩되어 안전하나, 이 명령어에 동적 입력이 추가되면 OS Command Injection 위험. n8n의 Execute Command 노드 자체가 잠재적 공격 표면.
- **Evidence**:
  ```json
  "command": "cd /app && python -m crawlers.main --all"
  ```
- **Remediation**:
  1. Execute Command 노드 사용 최소화, 가능하면 HTTP 기반 트리거로 대체
  2. 동적 파라미터 삽입 시 반드시 화이트리스트 검증

---

## Low Issues

### [SEC-009] User-Agent Spoofing in Coupang Crawler

- **Severity**: Low
- **OWASP**: N/A (Legal/Ethical)
- **File**: `E:\프로젝트\KPI_Auto_Report(Athome)\crawlers\coupang_crawler.py`
- **Lines**: 19-25
- **Description**: 크롤링 시 랜덤 User-Agent를 사용하여 봇 탐지를 우회 시도. 쿠팡의 robots.txt 및 이용약관 위반 가능성.
- **Impact**: 법적 리스크 (서비스 이용약관 위반), IP 차단, 계정 정지.
- **Remediation**: 공식 API가 있다면 API 사용 권장. 크롤링이 불가피한 경우 robots.txt 준수 및 rate limiting 유지.

### [SEC-010] Python 의존성 버전 고정 미흡

- **Severity**: Low
- **OWASP**: A06 - Vulnerable and Outdated Components
- **File**: `E:\프로젝트\KPI_Auto_Report(Athome)\requirements.txt`
- **Description**: `>=` 방식으로 최소 버전만 지정. 상위 버전에서 보안 취약점이 도입될 수 있음.
- **Evidence**:
  ```
  requests>=2.31.0
  beautifulsoup4>=4.12.0
  pandas>=2.1.0
  scipy>=1.11.0
  scikit-learn>=1.3.0
  ```
- **Remediation**:
  1. `pip freeze > requirements.lock` 또는 `pip-tools`로 정확한 버전 고정
  2. `pip-audit` 또는 `safety` 도구로 정기적 취약점 스캔

### [SEC-011] Slack Webhook URL 검증 부재

- **Severity**: Low
- **OWASP**: A10 - Server-Side Request Forgery (SSRF)
- **Files**: `E:\프로젝트\KPI_Auto_Report(Athome)\n8n\slack_send.js` (Line 19), `n8n\crawler_notify.js` (Line 105)
- **Description**: Slack Webhook URL이 코드에 하드코딩된 플레이스홀더(`YOUR_SLACK_WEBHOOK_URL`)이거나 환경변수로 주입됨. URL 검증이 없어, 환경변수가 악의적으로 변조되면 SSRF 공격 가능.
- **Remediation**:
  1. Webhook URL 형식 검증 (정규식: `^https://hooks\.slack\.com/services/`)
  2. 네트워크 레벨에서 outbound 트래픽을 필요한 도메인으로 제한

### [SEC-012] Supabase Project ID 노출

- **Severity**: Low
- **OWASP**: A05 - Security Misconfiguration
- **Files**: `E:\프로젝트\KPI_Auto_Report(Athome)\n8n\workflow.json`, `n8n\workflow_complete.json`, `.env`
- **Description**: Supabase Project ID (`rjulhuseewaaxpbgyaah`)가 여러 파일에 노출. Project ID 자체는 공개 정보이지만, anon key와 함께 노출 시 공격 표면이 됨.
- **Remediation**: anon key 보호 (SEC-001 해결)가 우선. Project URL도 환경변수화 권장.

---

## Positive Findings (Good Practices)

### SQL Injection 방어 - PASS

- **Files**: `schema/*.sql` (모든 RPC 함수)
- **Assessment**: 모든 PostgreSQL RPC 함수(`get_brand_kpis_yesterday`, `get_brand_kpis_last_week`, `get_top_products`, `get_competitor_changes`, `get_weekly_summary`, `get_monthly_summary`)가 **매개변수 없이** CURRENT_DATE 기반으로 동작하거나, `p_end_date`, `p_year`, `p_month` 등 **타입이 지정된 파라미터**만 사용. SQL 인젝션 취약점 없음.

### Python DB 접근 - PASS

- **Files**: `crawlers/supabase_loader.py`
- **Assessment**: Supabase REST API를 통해서만 DB에 접근. 동적 SQL 쿼리 생성이 전혀 없음. URL 파라미터(`select`, `order`, `limit`)도 코드에 하드코딩되어 있어 사용자 입력이 들어갈 여지 없음.

### XSS in Slack Messages - PASS (해당 없음)

- **Files**: `n8n/transform.js`
- **Assessment**: Slack 메시지는 Supabase RPC 응답 데이터(서버 제어 데이터)로만 구성. 사용자 입력이 Slack 메시지에 직접 삽입되는 경로가 없음. Slack의 mrkdwn 포맷은 HTML이 아니므로 XSS 자체가 불가.

### .env 파일 Git 추적 방지 - PASS

- **File**: `.gitignore`
- **Assessment**: `.env`, `.env.local`, `.env.production` 모두 `.gitignore`에 포함.

### workflow_complete.json 시크릿 처리 - PASS

- **File**: `n8n/workflow_complete.json`
- **Assessment**: `YOUR_SUPABASE_ANON_KEY`, `YOUR_SLACK_WEBHOOK_URL` 플레이스홀더 사용. 올바른 접근.

---

## Remediation Priority

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| 1 (NOW)  | SEC-001: workflow.json 시크릿 제거 + git 이력 정리 | Medium | Critical |
| 2 (NOW)  | SEC-003: TLS 검증 활성화 | Low    | High |
| 3 (NOW)  | SEC-004: n8n 디폴트 비밀번호 변경 | Low    | High |
| 4 (ASAP) | SEC-005: Supabase RLS 정책 추가 | Medium | High |
| 5 (ASAP) | SEC-002: Supabase anon key 로테이션 | Medium | Critical |
| 6 (Sprint) | SEC-007: 로그 민감정보 필터링 | Low  | Medium |
| 7 (Sprint) | SEC-008: Command injection 방어 | Low  | Medium |
| 8 (Backlog) | SEC-010: 의존성 버전 고정 | Low  | Low |

---

## Recommended Actions (Immediate)

### 1. workflow.json 시크릿 교체

```bash
# workflow.json에서 실제 토큰을 플레이스홀더로 교체
# 모든 anon key 값을 YOUR_SUPABASE_ANON_KEY로 변경

# git 이력에서 시크릿 제거 (BFG 사용)
# bfg --replace-text passwords.txt repo.git
```

### 2. TLS 검증 활성화

```yaml
# docker-compose.yml에서 아래 라인 제거
- NODE_TLS_REJECT_UNAUTHORIZED=0
```

### 3. n8n 비밀번호 강화

```env
# .env
N8N_BASIC_AUTH_PASSWORD=<최소 16자 영문+숫자+특수문자>
```

### 4. Supabase RLS 적용

```sql
-- 모든 테이블에 RLS 활성화
ALTER TABLE brand_daily_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_daily_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_competitors ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab_test_results ENABLE ROW LEVEL SECURITY;

-- anon 사용자에게 읽기 전용 허용 (예시)
CREATE POLICY "anon_read_brand_sales" ON brand_daily_sales
    FOR SELECT USING (true);

-- 쓰기는 service_role만 허용 (기본적으로 RLS가 차단)
```
