"""
차트 패널 모듈

이 모듈은 주식 차트를 표시하는 UI 패널을 구현합니다.
"""

import logging
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, 
    QLabel, QFrame, QSplitter, QGridLayout, QCheckBox, QDateEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QDate
import pyqtgraph as pg

class CandlestickItem(pg.GraphicsObject):
    """캔들스틱 차트 아이템 클래스"""
    
    def __init__(self):
        pg.GraphicsObject.__init__(self)
        self.picture = None
        self.data = None
        
    def set_data(self, data):
        """
        데이터 설정
        
        Args:
            data (dict): 차트 데이터 (open, high, low, close, time)
        """
        self.data = data
        self.generate_picture()
        self.informViewBoundsChanged()
        
    def generate_picture(self):
        """캔들스틱 그림 생성"""
        if self.data is None:
            return
            
        self.picture = pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.picture)
        
        w = 0.6  # 캔들 너비
        
        for i in range(len(self.data['time'])):
            # 시가, 고가, 저가, 종가
            open_price = self.data['open'][i]
            high_price = self.data['high'][i]
            low_price = self.data['low'][i]
            close_price = self.data['close'][i]
            
            # 캔들 위치
            t = self.data['time'][i]
            
            # 양봉/음봉 결정
            if close_price >= open_price:
                # 양봉 (빨간색)
                p.setPen(pg.mkPen('r'))
                p.setBrush(pg.mkBrush('r'))
            else:
                # 음봉 (파란색)
                p.setPen(pg.mkPen('b'))
                p.setBrush(pg.mkBrush('b'))
                
            # 몸통 그리기
            p.drawRect(pg.QtCore.QRectF(t-w/2, open_price, w, close_price-open_price))
            
            # 꼬리 그리기
            p.drawLine(pg.QtCore.QLineF(t, low_price, t, high_price))
            
        p.end()
        
    def paint(self, p, *args):
        """그리기"""
        if self.picture is not None:
            p.drawPicture(0, 0, self.picture)
            
    def boundingRect(self):
        """경계 사각형"""
        if self.picture is None:
            return pg.QtCore.QRectF(0, 0, 0, 0)
        return pg.QtCore.QRectF(self.picture.boundingRect())

class ChartPanel(QWidget):
    """
    차트 패널 클래스
    
    주식 차트를 표시하는 UI 패널입니다.
    """
    
    # 시그널 정의
    chart_request_signal = pyqtSignal(str, str, int)  # 종목코드, 차트 타입, 틱 범위
    
    def __init__(self, kiwoom, parent=None):
        """
        초기화
        
        Args:
            kiwoom: 키움 API 객체
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.kiwoom = kiwoom
        self.logger = logging.getLogger(__name__)
        self.logger.info("차트 패널 초기화")
        
        # 현재 차트 정보
        self.current_code = None
        self.current_chart_type = "day"  # 기본값: 일봉
        self.current_tick_range = 1      # 기본값: 1분
        
        # 차트 데이터
        self.chart_data = {
            "date": [],
            "time": [],
            "open": [],
            "high": [],
            "low": [],
            "close": [],
            "volume": []
        }
        
        # UI 초기화
        self._init_ui()
        
        # 시그널 연결
        self._connect_signals()
        
    def _init_ui(self):
        """UI 초기화"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 상단 컨트롤 영역
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(10, 5, 10, 5)
        
        # 차트 타입 선택
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["분봉", "일봉", "주봉", "월봉"])
        self.chart_type_combo.setCurrentIndex(1)  # 기본값: 일봉
        
        # 분봉 선택 (분봉 선택 시에만 활성화)
        self.tick_range_combo = QComboBox()
        self.tick_range_combo.addItems(["1분", "3분", "5분", "10분", "15분", "30분", "60분"])
        self.tick_range_combo.setEnabled(False)  # 기본적으로 비활성화
        
        # 조회 기간 설정
        self.date_from_label = QLabel("시작일:")
        self.date_from_edit = QDateEdit()
        self.date_from_edit.setCalendarPopup(True)
        self.date_from_edit.setDate(QDate.currentDate().addMonths(-3))  # 기본값: 3개월 전
        
        self.date_to_label = QLabel("종료일:")
        self.date_to_edit = QDateEdit()
        self.date_to_edit.setCalendarPopup(True)
        self.date_to_edit.setDate(QDate.currentDate())  # 기본값: 오늘
        
        # 지표 선택
        self.indicator_combo = QComboBox()
        self.indicator_combo.addItems(["없음", "이동평균선", "볼린저밴드", "MACD", "RSI", "스토캐스틱"])
        
        # 새로고침 버튼
        self.refresh_button = QPushButton("새로고침")
        
        # 컨트롤 레이아웃에 위젯 추가
        control_layout.addWidget(QLabel("차트 타입:"))
        control_layout.addWidget(self.chart_type_combo)
        control_layout.addWidget(QLabel("분봉:"))
        control_layout.addWidget(self.tick_range_combo)
        control_layout.addWidget(self.date_from_label)
        control_layout.addWidget(self.date_from_edit)
        control_layout.addWidget(self.date_to_label)
        control_layout.addWidget(self.date_to_edit)
        control_layout.addWidget(QLabel("지표:"))
        control_layout.addWidget(self.indicator_combo)
        control_layout.addStretch(1)
        control_layout.addWidget(self.refresh_button)
        
        # 차트 영역
        chart_splitter = QSplitter(Qt.Vertical)
        
        # 메인 차트 (캔들스틱)
        self.price_plot = pg.PlotWidget()
        self.price_plot.setBackground('w')
        self.price_plot.showGrid(x=True, y=True)
        self.price_plot.setLabel('left', '가격')
        
        # Y축 고정을 위한 ViewBox 설정
        self.price_plot.setMouseEnabled(x=True, y=False)  # Y축 마우스 이동 비활성화
        self.price_plot.getViewBox().setAutoVisible(y=True)  # Y축 자동 조정 활성화
        
        # 캔들스틱 아이템
        self.candle_item = CandlestickItem()
        self.price_plot.addItem(self.candle_item)
        
        # 이동평균선 아이템들
        self.ma_items = {}
        
        # 거래량 차트
        self.volume_plot = pg.PlotWidget()
        self.volume_plot.setBackground('w')
        self.volume_plot.showGrid(x=True, y=True)
        self.volume_plot.setLabel('left', '거래량')
        
        # 거래량 차트 ViewBox 설정
        self.volume_plot.setMouseEnabled(x=True, y=False)  # Y축 마우스 이동 비활성화
        self.volume_plot.getViewBox().setAutoVisible(y=True)  # Y축 자동 조정 활성화
        
        # 거래량 막대 아이템
        self.volume_bars = pg.BarGraphItem(x=[], height=[], width=0.6, brush='g')
        self.volume_plot.addItem(self.volume_bars)
        
        # X축 연결 (두 차트의 X축을 동기화)
        self.price_plot.setXLink(self.volume_plot)
        
        # 차트 영역에 추가
        chart_splitter.addWidget(self.price_plot)
        chart_splitter.addWidget(self.volume_plot)
        chart_splitter.setSizes([700, 300])  # 비율 설정
        
        # 메인 레이아웃에 추가
        main_layout.addWidget(control_frame)
        main_layout.addWidget(chart_splitter)
        
        # 이동평균선 설정 영역
        ma_frame = QFrame()
        ma_layout = QHBoxLayout(ma_frame)
        ma_layout.setContentsMargins(10, 5, 10, 5)
        
        # 이동평균선 체크박스
        self.ma_checkboxes = {}
        ma_periods = [5, 10, 20, 60, 120]
        ma_colors = ['r', 'g', 'b', 'c', 'm']
        
        for i, period in enumerate(ma_periods):
            checkbox = QCheckBox(f"MA{period}")
            checkbox.setChecked(False)
            self.ma_checkboxes[period] = checkbox
            ma_layout.addWidget(checkbox)
            
            # 이동평균선 아이템 생성
            self.ma_items[period] = pg.PlotDataItem(pen=pg.mkPen(ma_colors[i], width=1))
            self.price_plot.addItem(self.ma_items[period])
            self.ma_items[period].hide()  # 초기에는 숨김
        
        ma_layout.addStretch(1)
        main_layout.addWidget(ma_frame)
        
    def _connect_signals(self):
        """시그널 연결"""
        try:
            # 차트 타입 변경 시그널
            self.chart_type_combo.currentIndexChanged.connect(self._on_chart_type_changed)
            
            # 분봉 범위 변경 시그널
            self.tick_range_combo.currentIndexChanged.connect(self._on_tick_range_changed)
            
            # 지표 변경 시그널
            self.indicator_combo.currentIndexChanged.connect(self._on_indicator_changed)
            
            # 새로고침 버튼 클릭 시그널
            self.refresh_button.clicked.connect(self._on_refresh_clicked)
            
            # 이동평균선 체크박스 시그널
            for period, checkbox in self.ma_checkboxes.items():
                checkbox.stateChanged.connect(lambda state, p=period: self._on_ma_checkbox_changed(p, state))
            
            # 키움 차트 데이터 수신 시그널
            if hasattr(self.kiwoom, 'chart'):
                self.kiwoom.chart.chart_data_signal.connect(self._on_chart_data_received)
                self.logger.info("차트 데이터 시그널 연결 완료")
            else:
                self.logger.warning("키움 차트 객체가 없어 시그널을 연결할 수 없습니다.")
                
            # 날짜 변경 시그널
            self.date_from_edit.dateChanged.connect(self._on_date_changed)
            self.date_to_edit.dateChanged.connect(self._on_date_changed)
            
        except Exception as e:
            self.logger.error(f"시그널 연결 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def set_stock(self, code, name):
        """
        종목 설정
        
        Args:
            code (str): 종목코드
            name (str): 종목명
        """
        try:
            self.logger.info(f"차트 종목 설정: {code} ({name})")
            
            # 이전 종목과 동일한 경우 중복 요청 방지
            if self.current_code == code:
                self.logger.info(f"이미 조회 중인 종목입니다: {code}")
                return
                
            self.current_code = code
            
            # 차트 타이틀 설정
            self.price_plot.setTitle(f"{name} ({code})")
            
            # 차트 데이터 요청
            self._request_chart_data()
            
        except Exception as e:
            self.logger.error(f"종목 설정 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _request_chart_data(self):
        """차트 데이터 요청"""
        try:
            if not self.current_code:
                self.logger.warning("종목코드가 설정되지 않았습니다.")
                return
                
            if not hasattr(self.kiwoom, 'chart'):
                self.logger.error("키움 차트 객체가 없습니다.")
                return
                
            # 조회 기간 설정
            date_from = self.date_from_edit.date().toString("yyyyMMdd")
            date_to = self.date_to_edit.date().toString("yyyyMMdd")
                
            self.logger.info(f"차트 데이터 요청: {self.current_code}, 타입: {self.current_chart_type}, 기간: {date_from} ~ {date_to}")
            
            # 차트 타입에 따라 데이터 요청
            if self.current_chart_type == "minute":
                tick_range_values = [1, 3, 5, 10, 15, 30, 60]
                tick_range = tick_range_values[self.tick_range_combo.currentIndex()]
                self.kiwoom.chart.get_minute_chart(self.current_code, tick_range, date_from, date_to)
                
            elif self.current_chart_type == "day":
                self.kiwoom.chart.get_daily_chart(self.current_code, date_from, date_to)
                
            elif self.current_chart_type == "week":
                self.kiwoom.chart.get_weekly_chart(self.current_code, date_from, date_to)
                
            elif self.current_chart_type == "month":
                self.kiwoom.chart.get_monthly_chart(self.current_code, date_from, date_to)
                
        except Exception as e:
            self.logger.error(f"차트 데이터 요청 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    @pyqtSlot(str, str, dict)
    def _on_chart_data_received(self, code, chart_type, data):
        """
        차트 데이터 수신 시 처리
        
        Args:
            code (str): 종목코드
            chart_type (str): 차트 타입
            data (dict): 차트 데이터
        """
        try:
            # 현재 종목이 아닌 경우 무시
            if code != self.current_code:
                return
                
            self.logger.info(f"차트 데이터 수신: {code}, 타입: {chart_type}")
            
            # 차트 데이터 저장
            self.chart_data = data
            
            # 차트 업데이트
            self._update_chart()
            
        except Exception as e:
            self.logger.error(f"차트 데이터 처리 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _update_chart(self):
        """차트 업데이트"""
        try:
            if not self.chart_data or not self.chart_data.get("date"):
                self.logger.warning("업데이트할 차트 데이터가 없습니다.")
                return
                
            self.logger.info("차트 업데이트 시작")
            
            # 날짜/시간 데이터 변환
            dates = self.chart_data["date"]
            times = self.chart_data.get("time", ["" for _ in dates])
            
            # X축 인덱스 생성
            x_data = np.arange(len(dates))
            
            # 캔들스틱 데이터 설정
            candle_data = {
                "time": x_data,
                "open": self.chart_data["open"],
                "high": self.chart_data["high"],
                "low": self.chart_data["low"],
                "close": self.chart_data["close"]
            }
            self.candle_item.set_data(candle_data)
            
            # 거래량 데이터 설정
            volume_data = self.chart_data["volume"]
            self.volume_bars.setOpts(x=x_data, height=volume_data, width=0.6)
            
            # 거래량 색상 설정 (양봉: 빨간색, 음봉: 파란색)
            colors = []
            for i in range(len(x_data)):
                if i > 0 and self.chart_data["close"][i] >= self.chart_data["close"][i-1]:
                    colors.append('r')
                else:
                    colors.append('b')
            
            # X축 눈금 설정
            def format_x_tick(x):
                if x < 0 or x >= len(dates):
                    return ""
                idx = int(x)
                if self.current_chart_type == "minute":
                    return f"{dates[idx]} {times[idx]}"
                else:
                    return dates[idx]
            
            # X축 눈금 설정
            x_axis = self.price_plot.getAxis('bottom')
            x_axis.setTicks([[(i, format_x_tick(i)) for i in range(0, len(dates), max(1, len(dates)//10))]])
            
            # 이동평균선 계산 및 표시
            self._calculate_moving_averages(x_data)
            
            # 차트 범위 설정 - Y축 자동 조정
            self.price_plot.autoRange()
            self.volume_plot.autoRange()
            
            # Y축 범위 고정 (최고가와 최저가 기준으로 여유 공간 추가)
            if len(self.chart_data["high"]) > 0 and len(self.chart_data["low"]) > 0:
                max_price = max(self.chart_data["high"])
                min_price = min(self.chart_data["low"])
                price_range = max_price - min_price
                
                # 여유 공간 10% 추가
                self.price_plot.setYRange(min_price - price_range * 0.1, max_price + price_range * 0.1)
                
                # 거래량 차트도 여유 공간 추가
                max_volume = max(volume_data) if volume_data else 0
                self.volume_plot.setYRange(0, max_volume * 1.1)
            
            self.logger.info("차트 업데이트 완료")
            
        except Exception as e:
            self.logger.error(f"차트 업데이트 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _calculate_moving_averages(self, x_data):
        """
        이동평균선 계산
        
        Args:
            x_data (numpy.ndarray): X축 데이터
        """
        try:
            if not self.chart_data or not self.chart_data.get("close"):
                return
                
            close_prices = np.array(self.chart_data["close"])
            
            for period, item in self.ma_items.items():
                if self.ma_checkboxes[period].isChecked():
                    # 이동평균 계산
                    ma_values = np.zeros_like(close_prices)
                    for i in range(len(close_prices)):
                        if i < period - 1:
                            ma_values[i] = np.nan
                        else:
                            ma_values[i] = np.mean(close_prices[max(0, i-period+1):i+1])
                    
                    # 이동평균선 데이터 설정
                    item.setData(x=x_data, y=ma_values)
                    item.show()
                else:
                    item.hide()
                    
        except Exception as e:
            self.logger.error(f"이동평균선 계산 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _on_chart_type_changed(self, index):
        """
        차트 타입 변경 시 처리
        
        Args:
            index (int): 콤보박스 인덱스
        """
        try:
            chart_types = ["minute", "day", "week", "month"]
            self.current_chart_type = chart_types[index]
            
            # 분봉 선택 시 분봉 콤보박스 활성화
            self.tick_range_combo.setEnabled(self.current_chart_type == "minute")
            
            # 현재 종목이 있으면 차트 데이터 요청
            if self.current_code:
                self._request_chart_data()
                
        except Exception as e:
            self.logger.error(f"차트 타입 변경 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _on_tick_range_changed(self, index):
        """
        분봉 범위 변경 시 처리
        
        Args:
            index (int): 콤보박스 인덱스
        """
        try:
            # 현재 차트 타입이 분봉이고, 현재 종목이 있으면 차트 데이터 요청
            if self.current_chart_type == "minute" and self.current_code:
                self._request_chart_data()
                
        except Exception as e:
            self.logger.error(f"분봉 범위 변경 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _on_indicator_changed(self, index):
        """
        지표 변경 시 처리
        
        Args:
            index (int): 콤보박스 인덱스
        """
        try:
            # 지표에 따른 처리
            indicator = self.indicator_combo.currentText()
            
            # 이동평균선 표시 여부
            for checkbox in self.ma_checkboxes.values():
                checkbox.setVisible(indicator == "이동평균선")
                
            # 차트 업데이트
            self._update_chart()
                
        except Exception as e:
            self.logger.error(f"지표 변경 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _on_date_changed(self, date):
        """
        날짜 변경 시 처리
        
        Args:
            date (QDate): 변경된 날짜
        """
        try:
            # 시작일이 종료일보다 이후인 경우 조정
            if self.date_from_edit.date() > self.date_to_edit.date():
                if self.sender() == self.date_from_edit:
                    self.date_from_edit.setDate(self.date_to_edit.date())
                else:
                    self.date_to_edit.setDate(self.date_from_edit.date())
                    
            # 현재 종목이 있으면 차트 데이터 요청
            if self.current_code:
                self._request_chart_data()
                
        except Exception as e:
            self.logger.error(f"날짜 변경 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _on_refresh_clicked(self):
        """새로고침 버튼 클릭 시 처리"""
        try:
            if self.current_code:
                self._request_chart_data()
                
        except Exception as e:
            self.logger.error(f"새로고침 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _on_ma_checkbox_changed(self, period, state):
        """
        이동평균선 체크박스 변경 시 처리
        
        Args:
            period (int): 이동평균 기간
            state (int): 체크박스 상태
        """
        try:
            self.logger.info(f"이동평균선 {period}일선 상태 변경: {state}")
            
            # 체크박스 상태에 따라 이동평균선 표시/숨김
            if state == Qt.Checked:
                self.ma_items[period].show()
            else:
                self.ma_items[period].hide()
                
            # 차트 업데이트
            self._update_chart()
                
        except Exception as e:
            self.logger.error(f"이동평균선 설정 변경 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def closeEvent(self, event):
        """위젯 종료 시 처리"""
        self.logger.info("차트 패널 종료")
        event.accept() 