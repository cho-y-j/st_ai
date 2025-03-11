"""
메인 윈도우 모듈

이 모듈은 AI 트레이딩 시스템의 메인 윈도우를 구현합니다.
"""

import os
import sys
import logging
import json
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QSplitter, QStatusBar, QAction, QDialog, 
    QMessageBox, QApplication, QPushButton, QToolBar, QMenu,
    QDockWidget, QTabWidget, QInputDialog, QSizePolicy, QGroupBox, QCheckBox, QLineEdit
)
from PyQt5.QtCore import Qt, QSettings, pyqtSlot, QSize, QTimer, QTime
from PyQt5.QtGui import QIcon

# UI 패널 임포트
from .panels.price_panel import PricePanel
from .panels.chart_panel import ChartPanel

# 로거 설정
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """
    메인 윈도우 클래스
    
    AI 트레이딩 시스템의 메인 UI를 담당합니다.
    """
    
    def __init__(self, kiwoom=None):
        """
        메인 윈도우 초기화
        
        Args:
            kiwoom: 키움 API 객체
        """
        super().__init__()
        
        # 로거 설정
        self.logger = logging.getLogger(__name__)
        
        # 키움 API 객체 설정
        self.kiwoom = kiwoom
        
        try:
            # 설정 객체 생성
            self.settings = QSettings('AITrading', 'AITradingSystem')
            
            # 설정 로드
            self._load_settings()
            
            # 패널 저장 변수 초기화
            self.panels = {}
            
            # UI 초기화
            self._init_ui()
            
            # 메뉴바 생성
            self.create_menu_bar()
            
            # 툴바 생성
            self.create_toolbar()
            
            # 윈도우 상태 복원
            self._restore_window_state()
            
            # 현재가 패널 생성 (키움 API가 있는 경우에만)
            if self.kiwoom:
                self.create_price_panel()
                self.create_chart_panel()
            
            self.logger.info("초기화 완료")
            
        except Exception as e:
            self.logger.error(f"초기화 중 오류 발생: {str(e)}")
    
    def _init_ui(self):
        """
        UI 초기화
        """
        try:
            # 윈도우 설정
            self.setWindowTitle("AI 트레이딩 시스템")
            self.setGeometry(100, 100, 1200, 800)
            
            # 중앙 위젯
            self.central_widget = QWidget()
            self.setCentralWidget(self.central_widget)
            
            # 중앙 위젯 레이아웃
            self.main_layout = QVBoxLayout(self.central_widget)
            
            # 상태바
            self.statusBar().showMessage("준비됨")
            self.statusBar().setVisible(True)
            
            # 도킹 가능하도록 설정
            self.setDockNestingEnabled(True)
            self.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
            self.setCorner(Qt.TopRightCorner, Qt.RightDockWidgetArea)
            self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
            self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)
            
            logger.info("UI 초기화 완료")
            
        except Exception as e:
            logger.error(f"UI 초기화 중 오류 발생: {e}")
            raise
    
    def create_menu_bar(self):
        """
        메뉴바 생성
        """
        self.logger.info("메뉴바 생성")
        
        # 메뉴바 생성
        menu_bar = self.menuBar()
        
        # 설정 메뉴
        settings_menu = menu_bar.addMenu('설정')
        
        # 일반 설정 액션
        general_settings_action = QAction('일반 설정', self)
        general_settings_action.triggered.connect(self.show_general_settings)
        settings_menu.addAction(general_settings_action)
        
        # 계좌 비밀번호 설정 액션
        account_settings_action = QAction('계좌 비밀번호 설정', self)
        account_settings_action.triggered.connect(self.show_account_settings)
        settings_menu.addAction(account_settings_action)
        
        # 대시보드 메뉴
        dashboard_menu = menu_bar.addMenu('대시보드')
        
        # 대시보드 저장 액션
        save_dashboard_action = QAction('현재 대시보드 저장', self)
        save_dashboard_action.triggered.connect(self.save_dashboard)
        dashboard_menu.addAction(save_dashboard_action)
        
        # 대시보드 불러오기 액션
        load_dashboard_action = QAction('대시보드 불러오기', self)
        load_dashboard_action.triggered.connect(self.load_dashboard)
        dashboard_menu.addAction(load_dashboard_action)
        
        # 대시보드 삭제 액션
        delete_dashboard_action = QAction('대시보드 삭제', self)
        delete_dashboard_action.triggered.connect(self.delete_dashboard)
        dashboard_menu.addAction(delete_dashboard_action)
        
        # 패널 메뉴
        panel_menu = menu_bar.addMenu('패널')
        
        # 차트 패널 액션
        chart_action = QAction('차트', self)
        chart_action.triggered.connect(lambda: self.show_panel('chart'))
        panel_menu.addAction(chart_action)
        
        # 현재가 패널 액션
        price_action = QAction('현재가', self)
        price_action.triggered.connect(lambda: self.show_panel('price'))
        panel_menu.addAction(price_action)
        
        # 보유종목 패널 액션
        holdings_action = QAction('보유종목', self)
        holdings_action.triggered.connect(lambda: self.show_panel('holdings'))
        panel_menu.addAction(holdings_action)
        
        # 관심종목 패널 액션
        favorites_action = QAction('관심종목', self)
        favorites_action.triggered.connect(lambda: self.show_panel('favorites'))
        panel_menu.addAction(favorites_action)
        
        # 주문 패널 액션
        order_action = QAction('주문', self)
        order_action.triggered.connect(lambda: self.show_panel('order'))
        panel_menu.addAction(order_action)
        
        # 거래내역 패널 액션
        transactions_action = QAction('거래내역', self)
        transactions_action.triggered.connect(lambda: self.show_panel('transactions'))
        panel_menu.addAction(transactions_action)
        
        # AI 메뉴
        ai_menu = menu_bar.addMenu('AI')
        
        # AI 트레이딩 조건 액션
        ai_trading_conditions_action = QAction('AI 트레이딩 조건', self)
        ai_trading_conditions_action.triggered.connect(self.show_ai_trading_conditions)
        ai_menu.addAction(ai_trading_conditions_action)
        
        # 자동 매매 액션
        auto_trading_action = QAction('자동 매매', self)
        auto_trading_action.triggered.connect(self.show_auto_trading)
        ai_menu.addAction(auto_trading_action)
        
        # AI 종목 검색 액션
        ai_search_action = QAction('AI 종목 검색', self)
        ai_search_action.triggered.connect(self.show_ai_search)
        ai_menu.addAction(ai_search_action)
        
        # 도움말 메뉴
        help_menu = menu_bar.addMenu('도움말')
        
        # 도움말 액션
        help_action = QAction('도움말', self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        # 정보 액션
        about_action = QAction('정보', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        self.logger.info("메뉴바 생성 완료")
    
    def create_toolbar(self):
        """
        툴바 생성
        """
        try:
            # 메인 툴바
            main_toolbar = QToolBar()
            main_toolbar.setMovable(False)
            self.addToolBar(main_toolbar)
            
            # 연결 상태 라벨
            self.connection_status_label = QLabel()
            self.connection_status_label.setMinimumWidth(100)
            self.connection_status_label.setAlignment(Qt.AlignCenter)
            self.update_connection_status(False)  # 초기 상태는 미연결
            
            # 우측 정렬을 위한 빈 위젯
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            
            main_toolbar.addWidget(spacer)
            main_toolbar.addWidget(self.connection_status_label)
            
            # 연결 상태 업데이트 타이머
            self.connection_timer = QTimer()
            self.connection_timer.timeout.connect(self.check_connection_status)
            self.connection_timer.start(1000)  # 1초마다 연결 상태 체크
            
            if self.kiwoom and hasattr(self.kiwoom, 'data'):
                self.kiwoom.data.connection_status_updated.connect(self.update_connection_status)
            
            logger.info("툴바 생성 완료")
            
        except Exception as e:
            logger.error(f"툴바 생성 중 오류 발생: {e}")
    
    def update_connection_status(self, is_connected):
        """서버 연결 상태 UI 업데이트"""
        try:
            if is_connected:
                self.connection_status_label.setText("서버 연결됨")
                self.connection_status_label.setStyleSheet(
                    "QLabel { color: white; background-color: #2ecc71; padding: 5px; border-radius: 3px; }"
                )
            else:
                self.connection_status_label.setText("서버 미연결")
                self.connection_status_label.setStyleSheet(
                    "QLabel { color: white; background-color: #e74c3c; padding: 5px; border-radius: 3px; }"
                )
        except Exception as e:
            logger.error(f"연결 상태 업데이트 중 오류 발생: {e}")
    
    def check_connection_status(self):
        """서버 연결 상태 주기적 체크"""
        try:
            if self.kiwoom and hasattr(self.kiwoom, 'data'):
                self.kiwoom.data.check_connection()
        except Exception as e:
            logger.error(f"연결 상태 체크 중 오류 발생: {e}")
    
    def create_price_panel(self):
        """
        현재가 패널 생성
        """
        try:
            self.logger.info("현재가 패널 생성")
            
            # 이미 생성된 패널이 있는지 확인
            if self.findChild(QDockWidget, 'price'):
                self.logger.info("이미 생성된 현재가 패널이 있습니다.")
                return
            
            # 현재가 패널 생성
            self.show_panel('price')
            
        except Exception as e:
            self.logger.error(f"현재가 패널 생성 중 오류 발생: {str(e)}")
    
    def create_chart_panel(self):
        """
        차트 패널 생성
        """
        try:
            self.logger.info("차트 패널 생성")
            
            # 이미 생성된 차트 패널이 있는지 확인
            if self.findChild(QDockWidget, 'chart'):
                self.logger.info("이미 생성된 차트 패널이 있습니다.")
                return
            
            # 차트 패널 생성
            self.show_panel('chart')
            
        except Exception as e:
            self.logger.error(f"차트 패널 생성 중 오류 발생: {str(e)}")
    
    def show_panel(self, panel_name):
        """
        패널 표시
        
        Args:
            panel_name (str): 패널 이름
        """
        try:
            self.logger.info(f"패널 표시 요청: {panel_name}")
            
            # 이미 표시된 패널인지 확인
            existing_panel = self.findChild(QDockWidget, panel_name)
            if existing_panel:
                self.logger.info(f"이미 표시된 패널: {panel_name}")
                existing_panel.show()
                existing_panel.raise_()
                return
            
            # 패널 생성
            panel_widget = None
            
            if panel_name == 'chart':
                panel_widget = ChartPanel(self.kiwoom, self)
            elif panel_name == 'price':
                panel_widget = PricePanel(self.kiwoom, self)
                # 현재가 패널의 종목 선택 시그널을 차트 패널 업데이트에 연결
                panel_widget.stock_selected_signal.connect(self._on_stock_selected)
            elif panel_name == 'holdings':
                from ui.panels.holdings_panel import HoldingsPanel
                panel_widget = HoldingsPanel(self.kiwoom, self)
            elif panel_name == 'favorites':
                from ui.panels.favorites_panel import FavoritesPanel
                panel_widget = FavoritesPanel(self.kiwoom, self)
            elif panel_name == 'order':
                from ui.panels.order_panel import OrderPanel
                panel_widget = OrderPanel(self.kiwoom, self)
            elif panel_name == 'transactions':
                from ui.panels.transactions_panel import TransactionsPanel
                panel_widget = TransactionsPanel(self.kiwoom, self)
            else:
                self.logger.warning(f"알 수 없는 패널 이름: {panel_name}")
                QMessageBox.warning(self, '패널 표시 오류', f'알 수 없는 패널 이름: {panel_name}')
                return
            
            # 도킹 위젯 생성
            dock = QDockWidget(panel_name.capitalize(), self)
            dock.setObjectName(panel_name)
            dock.setWidget(panel_widget)
            dock.setAllowedAreas(Qt.AllDockWidgetAreas)
            dock.setFeatures(QDockWidget.DockWidgetClosable | 
                            QDockWidget.DockWidgetMovable | 
                            QDockWidget.DockWidgetFloatable)
            
            # 패널 추가 - 중앙에 플로팅 상태로 표시
            self.addDockWidget(Qt.RightDockWidgetArea, dock)
            dock.setFloating(True)
            
            # 화면 중앙에 위치시키기
            screen_geometry = QApplication.desktop().availableGeometry()
            dock_geometry = dock.geometry()
            dock.setGeometry(
                screen_geometry.width() // 2 - dock_geometry.width() // 2,
                screen_geometry.height() // 2 - dock_geometry.height() // 2,
                dock_geometry.width(),
                dock_geometry.height()
            )
            
            self.logger.info(f"패널 표시 완료: {panel_name}")
            
        except Exception as e:
            self.logger.error(f"패널 표시 중 오류 발생: {str(e)}")
            QMessageBox.warning(self, '패널 표시 오류', f'패널 표시 중 오류가 발생했습니다.\n{str(e)}')
    
    def _on_stock_selected(self, code, name):
        """
        종목 선택 시 처리
        
        Args:
            code (str): 종목코드
            name (str): 종목명
        """
        try:
            self.logger.info(f"종목 선택됨: {code} ({name})")
            
            # 차트 패널이 있으면 선택된 종목 정보 전달
            chart_dock = self.findChild(QDockWidget, 'chart')
            if chart_dock:
                chart_panel = chart_dock.widget()
                if chart_panel:
                    chart_panel.set_stock(code, name)
                    self.logger.info(f"차트 패널에 종목 정보 전달: {code} ({name})")
                else:
                    self.logger.warning("차트 패널 위젯을 찾을 수 없습니다.")
            else:
                # 차트 패널이 없으면 생성
                self.logger.info("차트 패널이 없어 새로 생성합니다.")
                self.create_chart_panel()
                
                # 약간의 지연 후 종목 정보 설정 (패널 생성 완료 후)
                QTimer.singleShot(100, lambda: self._set_chart_stock(code, name))
                
        except Exception as e:
            self.logger.error(f"종목 선택 처리 중 오류 발생: {str(e)}")
            
    def _set_chart_stock(self, code, name):
        """
        차트 패널에 종목 정보 설정 (지연 실행용)
        
        Args:
            code (str): 종목코드
            name (str): 종목명
        """
        try:
            chart_dock = self.findChild(QDockWidget, 'chart')
            if chart_dock:
                chart_panel = chart_dock.widget()
                if chart_panel:
                    chart_panel.set_stock(code, name)
                    self.logger.info(f"차트 패널에 종목 정보 전달 완료: {code} ({name})")
        except Exception as e:
            self.logger.error(f"차트 패널 종목 설정 중 오류 발생: {str(e)}")
    
    def show_settings_dialog(self):
        """설정 다이얼로그 표시"""
        try:
            logger.info("설정 다이얼로그 표시")
            # TODO: 설정 다이얼로그 구현
            pass
            
        except Exception as e:
            logger.error(f"설정 다이얼로그 표시 중 오류 발생: {e}")
    
    def show_account_settings(self):
        """
        계좌 비밀번호 설정 대화상자 표시
        """
        try:
            self.logger.info("계좌 비밀번호 설정 대화상자 표시")
            dialog = AccountSettingsDialog(self)
            dialog.exec_()
        except Exception as e:
            self.logger.error(f"계좌 비밀번호 설정 대화상자 표시 중 오류 발생: {str(e)}")
            QMessageBox.warning(self, '설정 오류', f'계좌 비밀번호 설정 대화상자 표시 중 오류가 발생했습니다.\n{str(e)}')
    
    def show_ai_trading_conditions(self):
        """
        AI 트레이딩 조건 패널 표시
        """
        try:
            self.logger.info("AI 트레이딩 조건 패널 표시")
            QMessageBox.information(self, 'AI 트레이딩 조건', 'AI 트레이딩 조건 기능은 현재 개발 중입니다.')
        except Exception as e:
            self.logger.error(f"AI 트레이딩 조건 패널 표시 중 오류 발생: {str(e)}")
            QMessageBox.warning(self, '패널 표시 오류', f'AI 트레이딩 조건 패널 표시 중 오류가 발생했습니다.\n{str(e)}')
    
    def show_auto_trading(self):
        """
        자동 매매 패널 표시
        """
        try:
            self.logger.info("자동 매매 패널 표시")
            QMessageBox.information(self, '자동 매매', '자동 매매 기능은 현재 개발 중입니다.')
        except Exception as e:
            self.logger.error(f"자동 매매 패널 표시 중 오류 발생: {str(e)}")
            QMessageBox.warning(self, '패널 표시 오류', f'자동 매매 패널 표시 중 오류가 발생했습니다.\n{str(e)}')
    
    def show_ai_search(self):
        """
        AI 종목 검색 패널 표시
        """
        try:
            self.logger.info("AI 종목 검색 패널 표시")
            QMessageBox.information(self, 'AI 종목 검색', 'AI 종목 검색 기능은 현재 개발 중입니다.')
        except Exception as e:
            self.logger.error(f"AI 종목 검색 패널 표시 중 오류 발생: {str(e)}")
            QMessageBox.warning(self, '패널 표시 오류', f'AI 종목 검색 패널 표시 중 오류가 발생했습니다.\n{str(e)}')
    
    def show_help(self):
        """
        도움말 표시
        """
        try:
            self.logger.info("도움말 표시")
            QMessageBox.information(self, '도움말', '도움말 기능은 현재 개발 중입니다.')
        except Exception as e:
            self.logger.error(f"도움말 표시 중 오류 발생: {str(e)}")
            QMessageBox.warning(self, '도움말 오류', f'도움말 표시 중 오류가 발생했습니다.\n{str(e)}')
    
    def show_about(self):
        """
        정보 표시
        """
        try:
            self.logger.info("정보 표시")
            QMessageBox.about(self, '정보', 
                             '키움 API를 활용한 AI 트레이딩 시스템\n\n'
                             '버전: 1.0.0\n'
                             '개발자: AI 트레이딩 팀')
        except Exception as e:
            self.logger.error(f"정보 표시 중 오류 발생: {str(e)}")
            QMessageBox.warning(self, '정보 오류', f'정보 표시 중 오류가 발생했습니다.\n{str(e)}')
    
    def save_dashboard(self):
        """
        현재 대시보드 상태 저장
        """
        try:
            self.logger.info("대시보드 저장 시작")
            
            # 대시보드 이름 입력 받기
            dashboard_name, ok = QInputDialog.getText(self, '대시보드 저장', '대시보드 이름:')
            
            if ok and dashboard_name:
                # 설정 객체 생성
                settings = QSettings("AITrader", "Dashboard")
                
                # 대시보드 목록 가져오기
                dashboard_list = settings.value("dashboard_list", [])
                if not isinstance(dashboard_list, list):
                    dashboard_list = []
                
                # 대시보드 목록에 추가
                if dashboard_name not in dashboard_list:
                    dashboard_list.append(dashboard_name)
                    settings.setValue("dashboard_list", dashboard_list)
                
                # 현재 윈도우 상태 저장
                settings.beginGroup(dashboard_name)
                settings.setValue("geometry", self.saveGeometry())
                settings.setValue("windowState", self.saveState())
                
                # 패널 정보 저장
                panel_info = []
                for dock in self.findChildren(QDockWidget):
                    if dock.isVisible():
                        panel_info.append({
                            "name": dock.objectName(),
                            "area": self.dockWidgetArea(dock),
                            "floating": dock.isFloating(),
                            "geometry": dock.geometry()
                        })
                
                settings.setValue("panels", panel_info)
                settings.endGroup()
                
                self.logger.info(f"대시보드 '{dashboard_name}' 저장 완료")
                QMessageBox.information(self, '대시보드 저장', f'대시보드 "{dashboard_name}"이(가) 저장되었습니다.')
            else:
                self.logger.info("대시보드 저장 취소됨")
        
        except Exception as e:
            self.logger.error(f"대시보드 저장 중 오류 발생: {str(e)}")
            QMessageBox.warning(self, '대시보드 저장 오류', f'대시보드 저장 중 오류가 발생했습니다.\n{str(e)}')
    
    def load_dashboard(self):
        """
        저장된 대시보드 불러오기
        """
        try:
            self.logger.info("대시보드 불러오기 시작")
            
            # 설정 객체 생성
            settings = QSettings("AITrader", "Dashboard")
            
            # 대시보드 목록 가져오기
            dashboard_list = settings.value("dashboard_list", [])
            if not isinstance(dashboard_list, list) or not dashboard_list:
                self.logger.info("저장된 대시보드가 없음")
                QMessageBox.information(self, '대시보드 불러오기', '저장된 대시보드가 없습니다.')
                return
            
            # 대시보드 선택 다이얼로그
            dashboard_name, ok = QInputDialog.getItem(self, '대시보드 불러오기', 
                                                     '대시보드 선택:', dashboard_list, 0, False)
            
            if ok and dashboard_name:
                # 모든 패널 닫기
                for dock in self.findChildren(QDockWidget):
                    dock.close()
                
                # 대시보드 상태 불러오기
                settings.beginGroup(dashboard_name)
                
                # 윈도우 상태 복원
                geometry = settings.value("geometry")
                if geometry:
                    self.restoreGeometry(geometry)
                
                window_state = settings.value("windowState")
                if window_state:
                    self.restoreState(window_state)
                
                # 패널 정보 불러오기
                panel_info = settings.value("panels", [])
                if panel_info:
                    for panel in panel_info:
                        self.show_panel(panel["name"])
                        dock = self.findChild(QDockWidget, panel["name"])
                        if dock:
                            if panel.get("floating", False):
                                dock.setFloating(True)
                                if "geometry" in panel:
                                    dock.setGeometry(panel["geometry"])
                            else:
                                self.addDockWidget(panel["area"], dock)
                
                settings.endGroup()
                
                self.logger.info(f"대시보드 '{dashboard_name}' 불러오기 완료")
                QMessageBox.information(self, '대시보드 불러오기', f'대시보드 "{dashboard_name}"이(가) 불러와졌습니다.')
            else:
                self.logger.info("대시보드 불러오기 취소됨")
        
        except Exception as e:
            self.logger.error(f"대시보드 불러오기 중 오류 발생: {str(e)}")
            QMessageBox.warning(self, '대시보드 불러오기 오류', f'대시보드 불러오기 중 오류가 발생했습니다.\n{str(e)}')
    
    def delete_dashboard(self):
        """
        저장된 대시보드 삭제
        """
        try:
            self.logger.info("대시보드 삭제 시작")
            
            # 설정 객체 생성
            settings = QSettings("AITrader", "Dashboard")
            
            # 대시보드 목록 가져오기
            dashboard_list = settings.value("dashboard_list", [])
            if not isinstance(dashboard_list, list) or not dashboard_list:
                self.logger.info("저장된 대시보드가 없음")
                QMessageBox.information(self, '대시보드 삭제', '저장된 대시보드가 없습니다.')
                return
            
            # 대시보드 선택 다이얼로그
            dashboard_name, ok = QInputDialog.getItem(self, '대시보드 삭제', 
                                                     '삭제할 대시보드 선택:', dashboard_list, 0, False)
            
            if ok and dashboard_name:
                # 확인 메시지
                reply = QMessageBox.question(self, '대시보드 삭제 확인', 
                                            f'대시보드 "{dashboard_name}"을(를) 삭제하시겠습니까?',
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    # 대시보드 목록에서 제거
                    dashboard_list.remove(dashboard_name)
                    settings.setValue("dashboard_list", dashboard_list)
                    
                    # 대시보드 설정 삭제
                    settings.beginGroup(dashboard_name)
                    settings.remove("")  # 그룹 내 모든 키 삭제
                    settings.endGroup()
                    
                    self.logger.info(f"대시보드 '{dashboard_name}' 삭제 완료")
                    QMessageBox.information(self, '대시보드 삭제', f'대시보드 "{dashboard_name}"이(가) 삭제되었습니다.')
                else:
                    self.logger.info("대시보드 삭제 취소됨")
            else:
                self.logger.info("대시보드 삭제 취소됨")
        
        except Exception as e:
            self.logger.error(f"대시보드 삭제 중 오류 발생: {str(e)}")
            QMessageBox.warning(self, '대시보드 삭제 오류', f'대시보드 삭제 중 오류가 발생했습니다.\n{str(e)}')
    
    def closeEvent(self, event):
        """
        윈도우 종료 이벤트
        
        Args:
            event: 종료 이벤트
        """
        try:
            # 윈도우 상태 저장
            self.settings.setValue('window/geometry', self.saveGeometry())
            self.settings.setValue('window/state', self.saveState())
            
            # 종료 확인
            reply = QMessageBox.question(
                self, '종료 확인',
                "프로그램을 종료하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
                
        except Exception as e:
            logger.error(f"종료 처리 중 오류 발생: {e}")
            event.accept()

    def show_general_settings(self):
        """
        일반 설정 대화상자 표시
        """
        try:
            self.logger.info("일반 설정 대화상자 표시")
            # 기존 show_settings_dialog 메서드 호출
            self.show_settings_dialog()
        except Exception as e:
            self.logger.error(f"일반 설정 대화상자 표시 중 오류 발생: {str(e)}")
            QMessageBox.warning(self, '설정 오류', f'일반 설정 대화상자 표시 중 오류가 발생했습니다.\n{str(e)}')

    def _restore_window_state(self):
        """윈도우 상태 복원"""
        try:
            geometry = self.settings.value('window/geometry')
            if geometry:
                self.restoreGeometry(geometry)
            
            state = self.settings.value('window/state')
            if state:
                self.restoreState(state)
            
            # 메뉴바와 툴바 표시
            self.menuBar().setVisible(True)
            for toolbar in self.findChildren(QToolBar):
                toolbar.setVisible(True)
            
            self.logger.info("윈도우 상태 복원 완료")
            
        except Exception as e:
            self.logger.error(f"윈도우 상태 복원 중 오류 발생: {str(e)}")

    def _load_settings(self):
        """
        설정 로드
        """
        try:
            self.logger.info("설정 로드 시작")
            
            # 설정 객체가 없으면 생성
            if not hasattr(self, 'settings'):
                self.settings = QSettings('AITrading', 'AITradingSystem')
            
            # 기본 설정 로드
            self.auto_login = self.settings.value('login/auto_login', False, type=bool)
            
            self.logger.info("설정 로드 완료")
            
        except Exception as e:
            self.logger.error(f"설정 로드 중 오류 발생: {str(e)}")

class AccountSettingsDialog(QDialog):
    def __init__(self, parent=None):
        """
        계좌 비밀번호 설정 대화상자 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent)
        
        # 로거 설정
        self.logger = logging.getLogger(__name__)
        
        # 키움 API 객체 가져오기
        if parent and hasattr(parent, 'kiwoom'):
            self.kiwoom = parent.kiwoom
        else:
            self.kiwoom = None
            self.logger.warning("키움 API 객체를 찾을 수 없습니다.")
        
        # UI 초기화
        self.setWindowTitle('계좌 비밀번호 설정')
        self.setMinimumWidth(400)
        self._init_ui()
    
    def _init_ui(self):
        """UI 초기화"""
        self.setFixedSize(400, 200)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        
        # 비밀번호 설정 그룹
        password_group = QGroupBox("계좌 비밀번호 설정")
        password_layout = QVBoxLayout()
        
        # 비밀번호 저장 체크박스
        self.save_password_checkbox = QCheckBox("계좌 비밀번호 저장")
        if self.kiwoom:
            self.save_password_checkbox.setChecked(self.kiwoom.get_account_password_saved())
        password_layout.addWidget(self.save_password_checkbox)
        
        # 비밀번호 삭제 버튼
        self.delete_password_button = QPushButton("저장된 비밀번호 삭제")
        self.delete_password_button.clicked.connect(self._delete_saved_password)
        password_layout.addWidget(self.delete_password_button)
        
        password_group.setLayout(password_layout)
        main_layout.addWidget(password_group)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        # 확인 버튼
        self.ok_button = QPushButton("확인")
        self.ok_button.clicked.connect(self._save_settings)
        button_layout.addWidget(self.ok_button)
        
        # 취소 버튼
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def _save_settings(self):
        """설정 저장"""
        try:
            self.logger.info("계좌 비밀번호 설정 저장")
            
            if self.kiwoom:
                # 비밀번호 저장 설정
                save_password = self.save_password_checkbox.isChecked()
                self.kiwoom.set_account_password_saved(save_password)
                
                self.logger.info(f"계좌 비밀번호 저장 설정: {save_password}")
                QMessageBox.information(self, "설정 저장", "계좌 비밀번호 설정이 저장되었습니다.")
                self.accept()
            else:
                self.logger.error("키움 API 객체가 없습니다.")
                QMessageBox.warning(self, "설정 저장 오류", "키움 API 객체를 찾을 수 없습니다.")
        
        except Exception as e:
            self.logger.error(f"설정 저장 중 오류 발생: {str(e)}")
            QMessageBox.warning(self, "설정 저장 오류", f"설정 저장 중 오류가 발생했습니다.\n{str(e)}")
    
    def _delete_saved_password(self):
        """저장된 비밀번호 삭제"""
        try:
            self.logger.info("저장된 계좌 비밀번호 삭제 요청")
            
            if self.kiwoom:
                # 확인 메시지
                reply = QMessageBox.question(
                    self, 
                    "비밀번호 삭제 확인", 
                    "저장된 계좌 비밀번호를 삭제하시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 비밀번호 삭제
                    self.kiwoom.delete_saved_account_password()
                    self.save_password_checkbox.setChecked(False)
                    
                    self.logger.info("저장된 계좌 비밀번호 삭제 완료")
                    QMessageBox.information(self, "비밀번호 삭제", "저장된 계좌 비밀번호가 삭제되었습니다.")
                else:
                    self.logger.info("계좌 비밀번호 삭제 취소")
            else:
                self.logger.error("키움 API 객체가 없습니다.")
                QMessageBox.warning(self, "비밀번호 삭제 오류", "키움 API 객체를 찾을 수 없습니다.")
        
        except Exception as e:
            self.logger.error(f"비밀번호 삭제 중 오류 발생: {str(e)}")
            QMessageBox.warning(self, "비밀번호 삭제 오류", f"비밀번호 삭제 중 오류가 발생했습니다.\n{str(e)}") 