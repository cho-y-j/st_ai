"""
현재가 패널 모듈

이 모듈은 실시간 현재가 조회 및 주문 기능을 제공하는 패널을 구현합니다.
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QSpinBox, QDoubleSpinBox,
    QListWidget, QListWidgetItem, QFrame, QGroupBox, QTabWidget, QFormLayout, QAbstractSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush

class StockSearchDialog(QListWidget):
    """종목 검색 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMouseTracking(True)
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                background-color: white;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: #e6e6e6;
            }
            QListWidget::item:selected {
                background-color: #0078d7;
                color: white;
            }
        """)

class PricePanel(QWidget):
    """
    현재가 패널 클래스
    
    실시간 현재가 조회 및 주문 기능을 제공하는 UI 패널입니다.
    """
    
    # 시그널 정의
    order_signal = pyqtSignal(dict)  # 주문 요청 시그널
    stock_selected_signal = pyqtSignal(str, str)  # 종목코드, 종목명
    
    def __init__(self, kiwoom, parent=None):
        """
        초기화
        
        Args:
            kiwoom: 키움 API 인스턴스
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.kiwoom = kiwoom
        self.logger = logging.getLogger(__name__)
        
        # 현재 조회 중인 종목 코드
        self.current_code = None
        
        # 검색 다이얼로그
        self.search_dialog = StockSearchDialog(self)
        self.search_dialog.itemClicked.connect(self._on_stock_selected)
        
        # UI 초기화
        self._init_ui()
        
        # 시그널 연결
        self._connect_signals()
    
    def _init_ui(self):
        """UI 초기화"""
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 상단 검색 영역 (헤더)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)
        
        # 종목 검색 입력창
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("종목명 또는 코드 입력")
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_input.returnPressed.connect(self._on_search_clicked)
        self.search_input.setFixedHeight(30)
        header_layout.addWidget(self.search_input, 7)
        
        # 검색 버튼
        self.search_button = QPushButton("검색")
        self.search_button.clicked.connect(self._on_search_clicked)
        self.search_button.setFixedHeight(30)
        header_layout.addWidget(self.search_button, 1)
        
        # 장 상태 표시
        self.market_state_label = QLabel("장 상태")
        self.market_state_label.setAlignment(Qt.AlignCenter)
        self.market_state_label.setStyleSheet("background-color: #f0f0f0; border-radius: 3px; padding: 3px;")
        self.market_state_label.setFixedHeight(30)
        header_layout.addWidget(self.market_state_label, 2)
        
        main_layout.addLayout(header_layout)
        
        # 종목 기본 정보 영역
        stock_info_layout = QHBoxLayout()
        
        # 종목명 및 코드
        name_code_layout = QVBoxLayout()
        self.name_label = QLabel("종목명")
        self.name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        name_code_layout.addWidget(self.name_label)
        
        self.code_label = QLabel("종목코드")
        self.code_label.setStyleSheet("font-size: 12px; color: #666;")
        name_code_layout.addWidget(self.code_label)
        
        stock_info_layout.addLayout(name_code_layout, 3)
        
        # 현재가 및 변동
        price_layout = QVBoxLayout()
        
        # 현재가
        self.current_price = QLabel("0")
        self.current_price.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.current_price.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        price_layout.addWidget(self.current_price)
        
        # 전일대비 및 등락률
        change_layout = QHBoxLayout()
        change_layout.setSpacing(5)
        
        self.price_change = QLabel("0")
        self.price_change.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        change_layout.addWidget(self.price_change, 1)
        
        self.change_rate = QLabel("0.00%")
        self.change_rate.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        change_layout.addWidget(self.change_rate, 1)
        
        price_layout.addLayout(change_layout)
        stock_info_layout.addLayout(price_layout, 2)
        
        # 거래량 정보
        volume_layout = QVBoxLayout()
        
        volume_title = QLabel("거래량")
        volume_title.setStyleSheet("font-size: 12px; color: #666;")
        volume_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        volume_layout.addWidget(volume_title)
        
        self.volume = QLabel("0")
        self.volume.setStyleSheet("font-size: 14px;")
        self.volume.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        volume_layout.addWidget(self.volume)
        
        stock_info_layout.addLayout(volume_layout, 2)
        
        main_layout.addLayout(stock_info_layout)
        
        # 중앙 영역 (호가창 + 차트/정보)
        central_layout = QHBoxLayout()
        
        # 좌측 호가창 영역
        hoga_layout = QVBoxLayout()
        hoga_layout.setSpacing(0)
        
        # 호가창 타이틀
        hoga_title = QLabel("호가")
        hoga_title.setStyleSheet("font-size: 14px; font-weight: bold; background-color: #f0f0f0; padding: 5px;")
        hoga_title.setAlignment(Qt.AlignCenter)
        hoga_layout.addWidget(hoga_title)
        
        # 호가창 테이블
        self.hoga_table = QTableWidget()
        self.hoga_table.setColumnCount(4)
        self.hoga_table.setRowCount(20)  # 매도 10줄 + 매수 10줄
        self.hoga_table.setHorizontalHeaderLabels(["매도잔량", "매도호가", "매수호가", "매수잔량"])
        self.hoga_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.hoga_table.verticalHeader().setVisible(False)
        self.hoga_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.hoga_table.setSelectionMode(QTableWidget.NoSelection)
        self.hoga_table.setFocusPolicy(Qt.NoFocus)
        self.hoga_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #f0f0f0;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        
        # 호가창 초기화
        for i in range(20):
            for j in range(4):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.hoga_table.setItem(i, j, item)
                
            # 매도호가 영역 (0-9행)
            if i < 10:
                self.hoga_table.item(i, 1).setBackground(QColor("#fff8f8"))
            # 매수호가 영역 (10-19행)
            else:
                self.hoga_table.item(i, 2).setBackground(QColor("#f8f8ff"))
                
        # 호가창 중앙에 현재가 표시 영역
        self.hoga_current_price = QLabel("현재가")
        self.hoga_current_price.setStyleSheet("""
            background-color: #f0f0f0;
            border: 1px solid #ddd;
            padding: 5px;
            font-weight: bold;
            font-size: 14px;
        """)
        self.hoga_current_price.setAlignment(Qt.AlignCenter)
        
        hoga_layout.addWidget(self.hoga_table, 10)
        hoga_layout.addWidget(self.hoga_current_price)
        
        # 호가 요약 정보
        hoga_summary_layout = QHBoxLayout()
        
        # 매도총잔량
        self.total_ask_volume = QLabel("매도총잔량: 0")
        self.total_ask_volume.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        hoga_summary_layout.addWidget(self.total_ask_volume)
        
        # 매수총잔량
        self.total_bid_volume = QLabel("매수총잔량: 0")
        self.total_bid_volume.setStyleSheet("color: #4d96ff; font-weight: bold;")
        hoga_summary_layout.addWidget(self.total_bid_volume)
        
        hoga_layout.addLayout(hoga_summary_layout)
        
        central_layout.addLayout(hoga_layout, 4)
        
        # 우측 정보 영역 (탭 위젯)
        info_tabs = QTabWidget()
        info_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                background: white;
            }
            QTabBar::tab {
                background: #f0f0f0;
                border: 1px solid #ddd;
                padding: 5px 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
            }
        """)
        
        # 탭1: 종목 정보
        stock_info_tab = QWidget()
        stock_info_layout = QVBoxLayout(stock_info_tab)
        
        # 가격 정보
        price_group = QGroupBox("가격 정보")
        price_group_layout = QFormLayout()
        
        self.open_price = QLabel("-")
        self.high_price = QLabel("-")
        self.low_price = QLabel("-")
        self.upper_limit = QLabel("-")
        self.lower_limit = QLabel("-")
        
        price_group_layout.addRow("시가:", self.open_price)
        price_group_layout.addRow("고가:", self.high_price)
        price_group_layout.addRow("저가:", self.low_price)
        price_group_layout.addRow("상한가:", self.upper_limit)
        price_group_layout.addRow("하한가:", self.lower_limit)
        
        price_group.setLayout(price_group_layout)
        stock_info_layout.addWidget(price_group)
        
        # 투자 정보
        invest_group = QGroupBox("투자 정보")
        invest_group_layout = QFormLayout()
        
        self.market_cap = QLabel("-")
        self.per = QLabel("-")
        self.eps = QLabel("-")
        self.roe = QLabel("-")
        self.pbr = QLabel("-")
        
        invest_group_layout.addRow("시가총액:", self.market_cap)
        invest_group_layout.addRow("PER:", self.per)
        invest_group_layout.addRow("EPS:", self.eps)
        invest_group_layout.addRow("ROE:", self.roe)
        invest_group_layout.addRow("PBR:", self.pbr)
        
        invest_group.setLayout(invest_group_layout)
        stock_info_layout.addWidget(invest_group)
        
        # 재무 정보
        finance_group = QGroupBox("재무 정보")
        finance_group_layout = QFormLayout()
        
        self.sales = QLabel("-")
        self.operating_profit = QLabel("-")
        self.net_income = QLabel("-")
        
        finance_group_layout.addRow("매출액:", self.sales)
        finance_group_layout.addRow("영업이익:", self.operating_profit)
        finance_group_layout.addRow("당기순이익:", self.net_income)
        
        finance_group.setLayout(finance_group_layout)
        stock_info_layout.addWidget(finance_group)
        
        stock_info_layout.addStretch(1)
        
        # 탭2: 주문
        order_tab = QWidget()
        order_layout = QVBoxLayout(order_tab)
        
        # 주문 유형
        order_type_group = QGroupBox("주문 유형")
        order_type_layout = QHBoxLayout()
        
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["지정가", "시장가", "조건부지정가", "최유리지정가", "최우선지정가"])
        order_type_layout.addWidget(self.order_type_combo)
        
        order_type_group.setLayout(order_type_layout)
        order_layout.addWidget(order_type_group)
        
        # 주문 수량
        quantity_group = QGroupBox("주문 수량")
        quantity_layout = QVBoxLayout()
        
        self.order_quantity = QSpinBox()
        self.order_quantity.setRange(1, 1000000)
        self.order_quantity.setValue(1)
        self.order_quantity.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.order_quantity.setStyleSheet("font-size: 14px; padding: 5px;")
        
        quantity_buttons_layout = QHBoxLayout()
        for pct in [10, 25, 50, 100]:
            btn = QPushButton(f"{pct}%")
            btn.setFixedHeight(30)
            quantity_buttons_layout.addWidget(btn)
        
        quantity_layout.addWidget(self.order_quantity)
        quantity_layout.addLayout(quantity_buttons_layout)
        
        quantity_group.setLayout(quantity_layout)
        order_layout.addWidget(quantity_group)
        
        # 주문 가격
        price_group = QGroupBox("주문 가격")
        price_layout = QVBoxLayout()
        
        self.order_price = QDoubleSpinBox()
        self.order_price.setRange(0, 100000000)
        self.order_price.setDecimals(0)
        self.order_price.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.order_price.setStyleSheet("font-size: 14px; padding: 5px;")
        
        price_buttons_layout = QHBoxLayout()
        for delta in [-1000, -100, -10, +10, +100, +1000]:
            btn = QPushButton(f"{delta:+}")
            btn.setFixedHeight(30)
            price_buttons_layout.addWidget(btn)
        
        price_layout.addWidget(self.order_price)
        price_layout.addLayout(price_buttons_layout)
        
        price_group.setLayout(price_layout)
        order_layout.addWidget(price_group)
        
        # 주문 버튼
        order_buttons_layout = QHBoxLayout()
        
        self.buy_button = QPushButton("매수")
        self.buy_button.setStyleSheet("""
            QPushButton {
                background-color: #4d96ff;
                color: white;
                font-weight: bold;
                font-size: 16px;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3a7bd5;
            }
        """)
        self.buy_button.clicked.connect(lambda: self._on_order_clicked("매수"))
        
        self.sell_button = QPushButton("매도")
        self.sell_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                font-weight: bold;
                font-size: 16px;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
        """)
        self.sell_button.clicked.connect(lambda: self._on_order_clicked("매도"))
        
        order_buttons_layout.addWidget(self.buy_button)
        order_buttons_layout.addWidget(self.sell_button)
        
        order_layout.addLayout(order_buttons_layout)
        order_layout.addStretch(1)
        
        # 탭 추가
        info_tabs.addTab(stock_info_tab, "종목 정보")
        info_tabs.addTab(order_tab, "주문")
        
        central_layout.addWidget(info_tabs, 3)
        
        main_layout.addLayout(central_layout)
        
        self.setLayout(main_layout)
        
        # 스타일 초기화
        self._init_styles()
    
    def _init_styles(self):
        """스타일 초기화"""
        # 기본 스타일
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                padding: 2px;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton {
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 5px;
                background-color: #f5f5f5;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # 가격 정보 초기 스타일
        self.current_price.setStyleSheet("font-size: 24px; font-weight: bold; color: #000000;")
        self.price_change.setStyleSheet("font-size: 16px; color: #000000;")
        self.change_rate.setStyleSheet("font-size: 16px; color: #000000;")

    def _connect_signals(self):
        """시그널 연결"""
        try:
            if hasattr(self.kiwoom, 'data'):
                # 실시간 가격 정보 시그널 연결
                self.kiwoom.data.price_updated.connect(self._on_price_updated)
                
                # 실시간 호가 정보 시그널 연결
                self.kiwoom.data.hoga_updated.connect(self._on_hoga_updated)
                
                self.logger.info("시그널 연결 완료")
            else:
                self.logger.error("키움 데이터 객체가 없어 시그널을 연결할 수 없습니다.")
        except Exception as e:
            self.logger.error(f"시그널 연결 중 오류 발생: {str(e)}")
    
    def _on_search_text_changed(self, text):
        """
        종목 검색어 변경 시 처리
        
        Args:
            text (str): 검색어
        """
        try:
            text = text.strip()
            self.logger.debug(f"검색어 입력: '{text}', 길이: {len(text)}")
            
            if not text or len(text) < 2:  # 최소 2글자 이상 입력해야 검색
                self.search_dialog.clear()
                self.search_dialog.hide()
                return
            
            # 종목 검색
            if not hasattr(self.kiwoom, 'data'):
                self.logger.error("키움 데이터 객체가 없습니다.")
                return
            
            # 검색 실행
            results = self.kiwoom.data.search_stocks(text)
            self.logger.debug(f"검색 결과: {len(results)}개 종목")
            
            # 검색 결과 표시
            self.search_dialog.clear()
            
            if not results:
                item = QListWidgetItem("검색 결과가 없습니다.")
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # 선택 불가능하게 설정
                self.search_dialog.addItem(item)
            else:
                for code, name in results[:30]:  # 최대 30개까지만 표시
                    item = QListWidgetItem(f"[{code}] {name}")
                    item.setData(Qt.UserRole, code)
                    self.search_dialog.addItem(item)
            
            # 검색 결과 팝업 표시
            pos = self.search_input.mapToGlobal(self.search_input.rect().bottomLeft())
            self.search_dialog.setGeometry(
                pos.x(),
                pos.y(),
                300,  # 너비
                min(400, max(60, len(results) * 25 + 10))  # 높이 (최소 60px)
            )
            self.search_dialog.show()
            
        except Exception as e:
            self.logger.error(f"종목 검색 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _on_search_clicked(self):
        """검색 버튼 클릭 또는 엔터 키 입력 시 처리"""
        try:
            text = self.search_input.text().strip()
            self.logger.info(f"검색 시작 - 입력값: '{text}', 길이: {len(text)}")
            
            if not text:
                self.logger.warning("검색어가 비어있습니다.")
                return
            
            if not hasattr(self.kiwoom, 'data'):
                self.logger.error("키움 데이터 객체가 없습니다.")
                return
            
            # 종목 코드인 경우 직접 조회 (6자리 숫자)
            if text.isdigit() and len(text) == 6:
                code = text
                self.logger.info(f"종목 코드로 직접 조회: {code}")
                self._request_stock_data(code)
                return
            
            # 검색 실행
            results = self.kiwoom.data.search_stocks(text)
            self.logger.info(f"검색 결과: {len(results)}개 종목 발견")
            
            if results:
                code, name = results[0]
                self.logger.info(f"첫 번째 종목 선택: [{code}] {name}")
                self.search_input.setText(code)
                self.name_label.setText(name)
                self._request_stock_data(code)
            else:
                self.logger.warning("검색 결과가 없습니다.")
                self.name_label.setText("종목을 찾을 수 없습니다.")
            
        except Exception as e:
            self.logger.error(f"종목 검색 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _on_stock_selected(self, item):
        """
        종목 선택 시 처리
        
        Args:
            item (QListWidgetItem): 선택된 아이템
        """
        try:
            # 선택 불가능한 항목인 경우 무시
            if not (item.flags() & Qt.ItemIsEnabled):
                return
                
            code = item.data(Qt.UserRole)
            if not code:
                self.logger.warning("선택된 항목에 종목코드가 없습니다.")
                return
                
            self.logger.info(f"종목 선택: {code}")
            self.search_input.setText(code)
            
            # 검색 다이얼로그 숨기기
            self.search_dialog.hide()
            
            # 종목 조회
            self._request_stock_data(code)
            
        except Exception as e:
            self.logger.error(f"종목 선택 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _request_stock_data(self, code):
        """
        종목 데이터 요청
        
        Args:
            code (str): 종목코드
        """
        try:
            self.logger.info(f"종목 데이터 요청: {code}")
            
            if not hasattr(self.kiwoom, 'data'):
                self.logger.error("키움 데이터 객체가 없습니다.")
                return
            
            # 이전 종목과 동일한 경우 중복 요청 방지
            if self.current_code == code:
                self.logger.info(f"이미 조회 중인 종목입니다: {code}")
                return
                
            self.current_code = code
            
            # 종목명 조회 (캐시에서)
            name = ""
            if code in self.kiwoom.data.code_cache:
                name = self.kiwoom.data.code_cache[code]
                self.name_label.setText(name)
            
            # 종목 선택 시그널 발생
            self.stock_selected_signal.emit(code, name)
            
            # 기본 정보 조회
            stock_info = self.kiwoom.data.search_stock(code)
            
            if not stock_info:
                self.logger.error(f"종목 정보를 가져오지 못했습니다: {code}")
                self.name_label.setText("정보를 가져올 수 없습니다")
                return
                
            self.logger.info(f"종목 정보 조회 성공: {code}")
            
            # 종목 정보 업데이트
            if "종목명" in stock_info:
                self.name_label.setText(stock_info["종목명"])
            
            # 현재가 정보 업데이트
            try:
                current_price = abs(int(stock_info.get("현재가", "0").replace(",", "")))
                price_change = int(stock_info.get("전일대비", "0").replace(",", ""))
                change_rate = float(stock_info.get("등락율", "0").replace(",", ""))
                volume = int(stock_info.get("거래량", "0").replace(",", ""))
                
                self.current_price.setText(f"{current_price:,}")
                self.price_change.setText(f"{price_change:+,}")
                self.change_rate.setText(f"{change_rate:+.2f}%")
                self.volume.setText(f"{volume:,}")
                
                # 가격 정보 색상 설정
                if price_change > 0:
                    color = "#ff6b6b"  # 빨간색
                elif price_change < 0:
                    color = "#4d96ff"  # 파란색
                else:
                    color = "#000000"  # 검은색
                
                self.current_price.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
                self.price_change.setStyleSheet(f"font-size: 16px; color: {color};")
                self.change_rate.setStyleSheet(f"font-size: 16px; color: {color};")
                
                # 주문 가격 설정
                self.order_price.setValue(current_price)
            except (ValueError, TypeError) as e:
                self.logger.error(f"가격 정보 처리 중 오류: {str(e)}")
            
            # 추가 정보 업데이트
            self.update_additional_info(stock_info)
            
            # 장 상태 표시
            self.market_state_label.setText("실시간 시세 조회 중")
            
        except Exception as e:
            self.logger.error(f"종목 데이터 요청 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def update_additional_info(self, stock_info):
        """추가 종목 정보 업데이트"""
        try:
            if not stock_info:
                self.logger.warning("업데이트할 종목 정보가 없습니다.")
                return
                
            # 종목코드 표시
            if "종목코드" in stock_info:
                self.code_label.setText(stock_info["종목코드"])
                
            # 가격 정보 업데이트
            try:
                self.open_price.setText(f"{abs(int(stock_info.get('시가', '0').replace(',', ''))):,}")
                self.high_price.setText(f"{abs(int(stock_info.get('고가', '0').replace(',', ''))):,}")
                self.low_price.setText(f"{abs(int(stock_info.get('저가', '0').replace(',', ''))):,}")
                self.upper_limit.setText(f"{abs(int(stock_info.get('상한가', '0').replace(',', ''))):,}")
                self.lower_limit.setText(f"{abs(int(stock_info.get('하한가', '0').replace(',', ''))):,}")
            except (ValueError, TypeError) as e:
                self.logger.error(f"가격 정보 처리 중 오류: {str(e)}")
            
            # 투자 정보 업데이트
            self.market_cap.setText(stock_info.get('시가총액', '-'))
            self.per.setText(stock_info.get('PER', '-'))
            self.eps.setText(stock_info.get('EPS', '-'))
            self.roe.setText(stock_info.get('ROE', '-'))
            self.pbr.setText(stock_info.get('PBR', '-'))
            
            # 재무 정보 업데이트
            self.sales.setText(stock_info.get('매출액', '-'))
            self.operating_profit.setText(stock_info.get('영업이익', '-'))
            self.net_income.setText(stock_info.get('당기순이익', '-'))
            
            self.logger.info("추가 정보 업데이트 완료")
            
        except Exception as e:
            self.logger.error(f"추가 정보 업데이트 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _on_order_clicked(self, order_type):
        """
        매수/매도 버튼 클릭 시 처리
        
        Args:
            order_type (str): 매수 또는 매도
        """
        if not self.current_code:
            return
        
        try:
            # 주문 정보 생성
            order_info = {
                "code": self.current_code,
                "order_type": order_type,
                "price_type": self.order_price.text(),
                "price": self.order_price.value(),
                "quantity": self.order_quantity.value()
            }
            
            # 주문 시그널 발생
            self.order_signal.emit(order_info)
            
        except Exception as e:
            self.logger.error(f"주문 요청 중 오류 발생: {str(e)}")
    
    def _on_price_updated(self, code, data):
        """
        실시간 가격 정보 수신 시 처리
        
        Args:
            code (str): 종목코드
            data (dict): 가격 정보
        """
        if code != self.current_code:
            return
            
        try:
            # 현재가 업데이트
            self.current_price.setText(f"{data['current_price']:,}")
            
            # 전일대비 업데이트
            price_change = data["price_change"]
            self.price_change.setText(f"{price_change:+,}")
            
            # 등락률 업데이트
            change_rate = data["change_rate"]
            self.change_rate.setText(f"{change_rate:+.2f}%")
            
            # 거래량 업데이트
            self.volume.setText(f"{data['volume']:,}")
            
            # 스타일 설정
            if price_change > 0:
                color = "#ff6b6b"  # 빨간색
            elif price_change < 0:
                color = "#4d96ff"  # 파란색
            else:
                color = "#000000"  # 검은색
            
            self.current_price.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
            self.price_change.setStyleSheet(f"font-size: 16px; color: {color};")
            self.change_rate.setStyleSheet(f"font-size: 16px; color: {color};")
            
        except Exception as e:
            self.logger.error(f"가격 정보 업데이트 중 오류 발생: {str(e)}")
    
    def _on_hoga_updated(self, code, hoga_data):
        """
        실시간 호가 정보 수신 시 처리
        
        Args:
            code (str): 종목코드
            hoga_data (dict): 호가 정보
        """
        if code != self.current_code:
            return
            
        try:
            self.logger.debug(f"호가 정보 업데이트 시작: {code}")
            
            # 매도호가 (상단 10개 행)
            ask_prices = hoga_data.get("ask_prices", [])
            ask_volumes = hoga_data.get("ask_volumes", [])
            
            # 매수호가 (하단 10개 행)
            bid_prices = hoga_data.get("bid_prices", [])
            bid_volumes = hoga_data.get("bid_volumes", [])
            
            self.logger.debug(f"호가 데이터: 매도호가={ask_prices}, 매도잔량={ask_volumes}, 매수호가={bid_prices}, 매수잔량={bid_volumes}")
            
            # 호가 테이블 업데이트
            # 매도호가 (역순으로 표시 - 높은 가격이 아래에 오도록)
            for i in range(min(5, len(ask_prices))):
                # 매도잔량 (0열)
                volume_item = self.hoga_table.item(9-i, 0)
                volume_item.setText(f"{ask_volumes[i]:,}")
                volume_item.setForeground(QBrush(QColor("#ff6b6b")))  # 빨간색
                
                # 매도호가 (1열)
                price_item = self.hoga_table.item(9-i, 1)
                price_item.setText(f"{ask_prices[i]:,}")
                price_item.setForeground(QBrush(QColor("#ff6b6b")))  # 빨간색
            
            # 매수호가
            for i in range(min(5, len(bid_prices))):
                # 매수호가 (2열)
                price_item = self.hoga_table.item(10+i, 2)
                price_item.setText(f"{bid_prices[i]:,}")
                price_item.setForeground(QBrush(QColor("#4d96ff")))  # 파란색
                
                # 매수잔량 (3열)
                volume_item = self.hoga_table.item(10+i, 3)
                volume_item.setText(f"{bid_volumes[i]:,}")
                volume_item.setForeground(QBrush(QColor("#4d96ff")))  # 파란색
            
            # 호가창 중앙에 현재가 표시
            current_price = abs(int(self.current_price.text().replace(",", "")))
            self.hoga_current_price.setText(f"현재가: {current_price:,}")
            
            # 총잔량 계산
            total_ask_volume = sum(ask_volumes)
            total_bid_volume = sum(bid_volumes)
            
            # 총잔량 표시
            self.total_ask_volume.setText(f"매도총잔량: {total_ask_volume:,}")
            self.total_bid_volume.setText(f"매수총잔량: {total_bid_volume:,}")
            
            self.logger.debug(f"호가 정보 업데이트 완료: {code}")
            
        except Exception as e:
            self.logger.error(f"호가 정보 업데이트 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def closeEvent(self, event):
        """
        패널 종료 시 처리
        
        Args:
            event: 종료 이벤트
        """
        try:
            self.current_code = None
            
        except Exception as e:
            self.logger.error(f"패널 종료 중 오류 발생: {str(e)}")
        
        super().closeEvent(event) 