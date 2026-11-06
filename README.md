# 개인 가계부 웹앱

FastAPI와 SQLite로 만든 한국어 개인 수입·지출 관리 웹앱입니다. 거래를 등록·수정·삭제하고, 잔액과 월별·카테고리별 소비 통계를 확인할 수 있습니다.

## 주요 기능

- 수입·지출의 날짜, 금액, 카테고리, 메모 관리
- 전체 및 이번 달 수입·지출·잔액 요약
- 기간·카테고리 검색
- 카테고리별 도넛 차트와 월별 막대 차트
- SQLite 기반 영속 저장 및 반응형 화면

## 기술 스택

- Python 3.10 이상, FastAPI, Uvicorn, Pydantic
- SQLite (`sqlite3`, Python 기본 모듈)
- HTML5, CSS3, JavaScript, Chart.js CDN

## 설치

Windows PowerShell에서 `upload` 폴더로 이동한 후 실행합니다.

```powershell
python -m pip install -r requirements.txt
```

가상환경을 사용하지 않는 환경을 전제로 하지만, 다른 프로젝트와의 충돌을 피하려면 배포·운영 환경에서는 가상환경이나 컨테이너를 권장합니다.

## 실행

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

브라우저에서 <http://127.0.0.1:8000>에 접속합니다. 클라우드에서는 다음처럼 `PORT` 환경변수를 사용합니다.

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port $env:PORT
```

## 사용 방법

`거래 추가`에서 수입 또는 지출, 날짜, 양수 금액, 카테고리와 메모를 입력합니다. 거래 목록의 `수정`·`삭제` 버튼으로 기존 내역을 관리하고, 날짜 범위와 카테고리 필터로 조회합니다.

## 데이터베이스 초기화

첫 실행 시 `data/expenses.db`와 `transactions` 테이블이 자동 생성됩니다. 데이터베이스 파일은 저장소에 포함하지 않습니다. 로컬 데이터를 초기화하려면 서버를 중지한 뒤 다음 명령을 실행하세요.

```powershell
Remove-Item .\data\expenses.db
```

다음 실행 시 빈 데이터베이스가 다시 생성됩니다. `DATABASE_PATH` 환경변수로 저장 위치를 변경할 수 있습니다. 실제 사용자 데이터, 로그, 캐시, 임시 파일은 Git에 커밋하지 마세요.

## CI/CD 및 배포

`Dockerfile`은 Python 3.12 slim 이미지에서 고정된 의존성을 설치하고 앱을 실행합니다. `.github/workflows/ci.yml`은 Pull Request와 `main` Push에서 의존성 설치, Python 컴파일, SQLite 초기화, Docker 이미지 빌드, 컨테이너 `/health` 검사를 수행합니다. `main` Push에서는 다음 GitHub Actions Secrets를 사용해 Docker Hub에 자동 업로드합니다.

- `DOCKERHUB_USERNAME`: Docker Hub 사용자명
- `DOCKERHUB_TOKEN`: Docker Hub Access Token(비밀번호 대신 사용)

이미지 이름은 `${DOCKERHUB_USERNAME}/personal-expense-tracker`이며 `latest`와 커밋 SHA 태그가 생성됩니다. 저장소에 토큰을 직접 작성하거나 로그로 출력하지 마세요. 배포 시에는 `/app/data`를 영속 볼륨에 연결해야 SQLite 데이터가 유지됩니다.

### Self-hosted Runner 자동 배포

`.github/workflows/deploy-self-hosted.yml`은 `Build and Push Docker Image` workflow가 성공한 뒤 Windows Self-hosted Runner에서 자동 실행됩니다. Runner에는 Docker Desktop 또는 Docker Engine이 설치되어 있고, Runner 서비스 계정이 Docker CLI를 실행할 수 있어야 합니다. 기본 라벨(`self-hosted`, `Windows`, `X64`)을 사용합니다.

배포 workflow는 Docker Hub 로그인, 성공한 CI 커밋 SHA 이미지 pull, 기존 `personal-expense-tracker` 컨테이너 교체, `personal-expense-tracker-data` 볼륨 연결, `http://127.0.0.1:8000/health` 확인을 수행합니다. Runner의 8000 포트가 사용 중이면 배포가 실패하므로 먼저 해당 포트를 비워야 합니다. Runner 설치 폴더와 실행 로그는 `.gitignore`에서 제외합니다.

SQLite는 단일 인스턴스·소규모 사용에 적합합니다. 클라우드에서는 컨테이너 재생성 시 파일이 사라질 수 있으므로 영속 디스크를 연결하거나 PostgreSQL 등 관리형 DB로 이전해야 합니다. `.env`, DB 파일, 인증정보를 저장소나 로그에 남기지 마세요. Chart.js CDN을 사용할 수 없는 폐쇄망에서는 라이브러리를 별도 정적 자산으로 제공해야 합니다.

