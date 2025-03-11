# AI 트레이딩 시스템

키움증권 Open API를 활용한 AI 기반 자동매매 시스템입니다.

## 주요 기능

- 실시간 주식 데이터 분석
- 조건 검색 기능
- AI 기반 자동매매 전략 생성 및 실행
- 종목 분석 및 데이터 수집

## 설치 방법

1. 키움증권 Open API 설치
   - [키움증권 Open API](https://www1.kiwoom.com/nkw.templateFrameSet.do?m=m1408000000) 다운로드 및 설치

2. 필요한 패키지 설치
   ```
   pip install -r requirements.txt
   ```

## 실행 방법

```
python main.py
```

## 개발 환경

- Python 3.8 이상
- PyQt5
- 키움증권 Open API

## 프로젝트 구조

```
my_project/
├── main.py                         # 프로그램 실행 (진입점)
│
├── ui/                             # UI 관련 파일
│   ├── main_window.py              # 메인 윈도우
│   ├── dialogs/                    # 다이얼로그 관련 파일들
│   ├── panels/                     # 다양한 UI 패널 파일들
│
├── core/                           # 핵심 로직
│   ├── kiwoom_wrapper/             # 키움 API 관련 모듈
│   ├── trading_engine/             # 트레이딩 엔진 관련 모듈
│   ├── backtester/                 # 백테스트 관련 모듈
│
├── database/                       # 데이터베이스 관련 파일
│
├── analysis/                       # AI 및 데이터 분석 모듈
│
└── reports/                        # 보고서 관련 모듈
```

## 주의사항

- 이 프로그램은 개발 중인 버전입니다.
- 실제 투자에 사용하기 전에 충분한 테스트가 필요합니다.
- 투자의 책임은 사용자에게 있습니다. 