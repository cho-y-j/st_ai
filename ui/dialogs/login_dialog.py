"""
로그인 다이얼로그 모듈

이 모듈은 키움 API 로그인 과정을 위한 UI를 제공합니다.
공지사항과 로그인 기능을 통합하여 하나의 창에서 처리합니다.
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QCheckBox, QProgressBar, QTextEdit,
    QTabWidget, QWidget, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize, QSettings
from PyQt5.QtGui import QIcon, QPixmap, QFont

class LoginDialog(QDialog):
    """
    로그인 다이얼로그 클래스
    
    키움 API 로그인 과정을 위한 UI를 제공합니다.
    공지사항과 로그인 기능을 통합하여 하나의 창에서 처리합니다.
    """
    
    # 로그인 완료 시그널
    login_completed = pyqtSignal(bool, str)  # 성공 여부, 메시지
    
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
        
        # 자동 로그인 변수 초기화
        self.auto_login = False
        
        # UI 초기화
        self._init_ui()
        
        # 설정 로드
        self._load_settings()
        
        # 키움 API 로그인 완료 시그널 연결
        self.kiwoom.login_completed.connect(self._on_login_completed)
        
        # 자동 로그인 시작 (선택적)
        if self.auto_login:
            QTimer.singleShot(500, self._start_login)
    
    def _init_ui(self):
        """UI 초기화"""
        # 기본 설정
        self.setWindowTitle("AI 트레이딩 시스템 - 로그인")
        self.setFixedSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                font-size: 9pt;
            }
            QPushButton {
                font-size: 9pt;
                padding: 8px;
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #0066b3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0078d7;
            }
            QCheckBox {
                font-size: 9pt;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: white;
                font-size: 9pt;
            }
        """)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 로고 및 타이틀
        title_label = QLabel("AI 트레이딩 시스템")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 공지사항 영역
        notice_group = QWidget()
        notice_layout = QVBoxLayout(notice_group)
        notice_layout.setContentsMargins(0, 0, 0, 0)
        
        # 공지사항 제목
        notice_title = QLabel("공지사항")
        notice_title.setStyleSheet("font-size: 12pt; font-weight: bold; margin-top: 10px;")
        notice_layout.addWidget(notice_title)
        
        # 공지사항 내용
        self.notice_text = QTextEdit()
        self.notice_text.setReadOnly(True)
        self.notice_text.setMinimumHeight(150)
        self.notice_text.setHtml("""
        <h2>AI 트레이딩 시스템 v1.0</h2>
        <p>이 프로그램은 키움증권 Open API를 활용한 AI 기반 자동매매 시스템입니다.</p>
        <p>주요 기능:</p>
        <ul>
            <li>실시간 시세 조회 및 종목 검색</li>
            <li>AI 기반 자동매매 패턴 생성 및 실행</li>
            <li>조건 검색 기능</li>
            <li>종목 분석 및 데이터 수집</li>
        </ul>
        <p>시작하기 전에 키움증권 로그인이 필요합니다.</p>
        <p><b>주의: 이 프로그램은 개발 중인 버전입니다.</b></p>
        <p><b>키움 Open API가 설치되어 있어야 하며, 32비트 Python 환경에서 실행해야 합니다.</b></p>
        """)
        notice_layout.addWidget(self.notice_text)
        
        # 다시 보지 않기 체크박스
        self.dont_show_again_checkbox = QCheckBox("다음에 이 공지를 표시하지 않음")
        notice_layout.addWidget(self.dont_show_again_checkbox)
        
        main_layout.addWidget(notice_group)
        
        # 구분선
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #cccccc;")
        main_layout.addWidget(separator)
        
        # 로그인 영역
        login_group = QWidget()
        login_layout = QVBoxLayout(login_group)
        login_layout.setContentsMargins(0, 0, 0, 0)
        
        # 로그인 안내 메시지
        self.info_label = QLabel("키움 API에 로그인하여 트레이딩 시스템을 시작합니다.")
        self.info_label.setStyleSheet("font-size: 10pt; color: #666666; margin: 5px;")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        login_layout.addWidget(self.info_label)
        
        # 로그인 정보 저장 체크박스
        self.save_login_checkbox = QCheckBox("로그인 정보 저장")
        self.save_login_checkbox.stateChanged.connect(self._on_save_login_changed)
        login_layout.addWidget(self.save_login_checkbox)
        
        # 진행 상태 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        login_layout.addWidget(self.progress_bar)
        
        # 상태 메시지
        self.status_label = QLabel("준비됨")
        self.status_label.setAlignment(Qt.AlignCenter)
        login_layout.addWidget(self.status_label)
        
        main_layout.addWidget(login_group)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        # 로그인 버튼
        self.login_button = QPushButton("로그인")
        self.login_button.clicked.connect(self._start_login)
        button_layout.addWidget(self.login_button)
        
        # 취소 버튼
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def _on_save_login_changed(self, state):
        """로그인 정보 저장 체크박스 상태 변경 처리"""
        try:
            is_checked = state == Qt.Checked
            
            # 설정 저장
            self.kiwoom.set_account_password_saved(is_checked)
            
            # 체크 해제 시 저장된 비밀번호 삭제
            if not is_checked:
                self.kiwoom.delete_saved_account_password()
                
        except Exception as e:
            self.logger.error(f"로그인 정보 저장 설정 변경 중 오류 발생: {str(e)}")
    
    def _load_settings(self):
        """설정 로드"""
        try:
            # 설정 객체 생성
            from PyQt5.QtCore import QSettings
            settings = QSettings('AITrading', 'AITradingSystem')
            
            # 공지사항 다시 보지 않기 설정 로드
            dont_show_again = settings.value('notice/dont_show_again', False, type=bool)
            self.dont_show_again_checkbox.setChecked(dont_show_again)
            
            # 저장된 로그인 정보가 있으면 자동 로그인 시도
            if self.kiwoom.get_account_password_saved():
                self.save_login_checkbox.setChecked(True)
                
                # 자동 로그인 설정
                self.auto_login = True
                self.logger.info("자동 로그인 설정 완료")
            else:
                self.auto_login = False
        except Exception as e:
            self.logger.error(f"설정 로드 중 오류 발생: {str(e)}")
            self.auto_login = False
    
    def _save_settings(self):
        """설정 저장"""
        try:
            # 설정 객체 생성
            settings = QSettings('AITrading', 'AITradingSystem')
            
            # 로그인 정보 저장 설정
            save_login = self.save_login_checkbox.isChecked()
            self.kiwoom.set_account_password_saved(save_login)
            
            # 공지사항 다시 보지 않기 설정
            dont_show_again = self.dont_show_again_checkbox.isChecked()
            settings.setValue('notice/dont_show_again', dont_show_again)
            
            self.logger.info("로그인 설정 저장 완료")
        except Exception as e:
            self.logger.error(f"설정 저장 중 오류 발생: {str(e)}")
    
    def _start_login(self):
        """
        로그인 시작
        """
        self.logger.info("로그인 시작")
        self.status_label.setText("키움 API 로그인 중...")
        self.progress_bar.setValue(30)
        
        # 버튼 비활성화
        self.login_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        
        # 설정 저장
        self._save_settings()
        
        # 로그인 요청
        try:
            # 연결 상태 확인
            connect_state = self.kiwoom.get_connect_state()
            if connect_state == 1:
                self.logger.info("이미 로그인되어 있습니다.")
                self._on_login_completed(True, "이미 로그인되어 있습니다.")
                return
            
            # 로그인 요청
            self.kiwoom.login()
            self.progress_bar.setValue(50)
            
            # 안내 메시지 업데이트
            self.info_label.setText("키움 로그인 창이 나타나면 아이디와 비밀번호를 입력하세요.")
            self.info_label.setStyleSheet("font-size: 10pt; color: #0066cc; margin: 5px; font-weight: bold;")
            
        except Exception as e:
            self.logger.exception("로그인 요청 중 오류 발생")
            self._on_login_completed(False, f"로그인 요청 중 오류 발생: {str(e)}")
    
    def _on_login_completed(self, success, message):
        """
        로그인 완료 처리
        
        Args:
            success (bool): 성공 여부
            message (str): 결과 메시지
        """
        try:
            if success:
                self.progress_bar.setValue(100)
                self.status_label.setText("로그인 성공")
                
                # 설정 저장
                self._save_settings()
                
                # 로그인 완료 시그널 발생
                self.login_completed.emit(True, "로그인 성공")
                
                # 대화상자 닫기
                self.accept()
            else:
                self.progress_bar.setValue(0)
                self.status_label.setText(f"로그인 실패: {message}")
                self.info_label.setText("로그인에 실패했습니다. 다시 시도해주세요.")
                self.info_label.setStyleSheet("font-size: 10pt; color: red; margin: 5px;")
                
                # 버튼 활성화
                self.login_button.setEnabled(True)
                self.cancel_button.setEnabled(True)
                
                # 로그인 완료 시그널 발생
                self.login_completed.emit(False, message)
        except Exception as e:
            self.logger.error(f"로그인 완료 처리 중 오류 발생: {str(e)}")
    
    def is_dont_show_again(self):
        """
        공지사항 다시 보지 않기 설정 여부 반환
        
        Returns:
            bool: 다시 보지 않기 설정 여부
        """
        return self.dont_show_again_checkbox.isChecked() 