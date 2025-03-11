# 🚀 AI 트레이딩 시스템 프로젝트 가이드 (`PROJECT_GUIDE.md`)

## **📌 1️⃣ 프로젝트 개요**

이 프로젝트는 **실시간 주식 데이터 분석, 조건 검색, AI 기반 자동매매 전략 생성 및 실행**을 목표로 합니다.

### **📌 핵심 목표:**

- **키움 API를 활용한 실시간 시세 조회 및 종목 검색**
- **HTS(영웅문)에서 설정한 조건식을 API를 통해 가져와 활용 가능**
- **AI가 자동매매 패턴을 생성하고, 저장 후 매매 실행 가능**
- **사용자가 다수의 매매 전략을 선택하여 특정 종목별로 자동매매 실행 가능**
- **조건 검색 기능과 AI 자동매매 패턴을 유기적으로 연동**
- **종목 분석을 위한 다양한 데이터 수집 및 AI 패턴 학습 기능 포함**
- **각 기능이 독립적으로 동작하면서도 중앙 데이터 저장소를 통해 상호 연결될 수 있도록 설계**
- **주식 종목을 분석하기 위한 종합적인 데이터 수집 및 분석 시스템 구축**

---

## **📌 2️⃣ 폴더 및 파일 구조 및 연결 관계**

```
my_project/
├── main.py                         # 프로그램 실행 (진입점)
│
├── ui/                             # UI 관련 파일
│   ├── main_window.py              # 메인 윈도우 (전체 패널/메뉴/탭 구성 관리)
│   ├── dialogs/
│   │   ├── login_dialog.py         # 로그인 다이얼로그 (공지, 로그인 상태 표시 등)
│   │   ├── notice_dialog.py        # 공지 및 알림 팝업 (필요 시)
│   ├── panels/
│   │   ├── price_panel.py          # 현재가 패널
│   │   ├── favorites_panel.py      # 관심종목 패널
│   │   ├── chart_panel.py          # 차트 패널
│   │   ├── holdings_panel.py       # 보유 종목 패널 (잔고, 평가손익)
│   │   ├── account_panel.py        # 계좌 관리 패널 (예수금, 주문 가능 금액 등)
│   │   ├── trade_history_panel.py  # 거래 내역 패널 (체결/미체결 내역)
│   │   ├── real_time_trade_panel.py# 실시간 거래 현황 패널
│   │   ├── condition_panel.py      # 조건 검색 패널
│   │   ├── pattern_selection_panel.py # 자동매매 패턴 선택 패널
│   │   ├── pattern_creator_panel.py   # 자동매매 패턴 생성 패널
│   │   ├── backtest_panel.py       # 백테스트 패널
│   │   ├── ai_trading_panel.py     # AI 자동매매 패널
│   │   ├── stock_analysis_panel.py # 종목 분석 패널 (핵심!)
│   │   ├── risk_management_panel.py # 리스크 관리 패널 (손절/익절 기준 설정)
│
├── core/                           # 핵심 로직 (데이터 처리 및 분석)
│   ├── kiwoom_wrapper/             # 키움 API 관련 모듈
│   │   ├── kiwoom_login.py         # 키움 API 로그인
│   │   ├── kiwoom_data.py          # 종목 데이터 조회 (현재가, 시세, 체결 내역)
│   │   ├── kiwoom_condition.py     # 키움 API 기반 조건 검색 실행
│   │   ├── kiwoom_order.py         # 주문 실행 (매수/매도)
│   ├── trading_engine/              
│   │   ├── condition_scanner.py    # 조건 검색 스캐너 (조건식 실행)
│   │   ├── strategy_manager.py     # 자동매매 패턴 저장 및 로드
│   │   ├── auto_trade_engine.py    # AI 자동매매 엔진
│   ├── backtester/
│   │   ├── backtester.py           # 백테스트 실행 (과거 데이터로 전략 검증)
│   ├── data_fetcher.py             # 실시간 데이터 수집 모듈
│   ├── stock_analyzer.py           # AI 기반 종목 분석 엔진 (신규 추가!)
│   ├── risk_manager.py             # 종목별 리스크 평가 및 최적 매매 타이밍 분석
│
├── database/
│   ├── indicators_data.db          # 보조 지표 저장
│   ├── trading_strategies.db       # AI 매매 알고리즘 및 조건 검색 논리 저장
│   ├── stock_analysis.db           # 종목 분석 데이터 저장 (핵심!)
│   ├── db_manager.py               # 데이터베이스 CRUD 관리
│
├── analysis/                       # AI 및 데이터 분석 모듈
│   ├── indicators.py               # 보조 지표 계산 (RSI, MACD 등)
│   ├── pattern_manager.py          # 자동매매 패턴 저장 및 불러오기
│   ├── machine_learning.py         # AI 기반 종목 분석
│   ├── stock_analysis.py           # 종목 분석 및 최적 매매 패턴 탐색
│   ├── data_preprocessor.py        # 종목 데이터 전처리 및 정리
│   ├── risk_management.py          # 리스크 관리 알고리즘
│   ├── sentiment_analysis.py       # 뉴스 및 공시 데이터 감성 분석 (신규 추가!)
│   ├── feature_engineering.py      # AI 분석을 위한 데이터 가공 (신규 추가!)
│
└── reports/
    ├── trading_report.py           # 거래 리포트 생성
    ├── performance_metrics.py      # AI 매매 성과 분석
```

---

## **📌 3️⃣ AI 트레이딩 시스템 핵심 기능**

### **🔹 종목 분석 시스템 (핵심 기능 추가)**

📌 **데이터 수집**
- 재무제표, 기초 지표 (PER, PBR, ROE, 부채비율)
- 거래량, 외국인/기관 매매 동향, 공매도 정보
- 뉴스 데이터, 공시 데이터 분석
- 기술적 분석 데이터 (이동평균선, 볼린저밴드 등)
- 기업 실적 및 미래 예측 데이터

📌 **AI 분석 엔진**
- 머신러닝 기반 종목 선별 (KNN, 랜덤 포레스트 등 적용)
- 기술적 분석 패턴 학습 및 적용
- AI가 최적 매매 시점을 탐색
- 실시간 리스크 관리 및 손절/익절 기준 설정
- 뉴스 및 공시 데이터 감성 분석 적용
- 데이터 가공 및 특징 엔지니어링 적용

📌 **패턴 학습 및 저장**
- AI가 찾은 이상적인 매매 패턴 저장
- 자동매매 패턴을 전략 DB에 저장 후 실행

---

## **📌 4️⃣ 최종 목적 및 활용 방식**

✅ **AI는 종목 분석을 기반으로 자동매매 패턴을 생성하여 실행하도록 설계**
✅ **강화된 리스크 관리 기능 포함**
✅ **Cursor AI는 종목 분석, 조건 검색, 자동매매 개발 시 코드 구조를 이해하고 작업해야 함**



