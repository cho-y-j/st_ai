"""
공지 다이얼로그 모듈

이 모듈은 시스템 공지사항을 표시하는 다이얼로그를 제공합니다.
"""

import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTextEdit, QCheckBox)
from PyQt5.QtCore import Qt

class NoticeDialog(QDialog):
    """
    공지 다이얼로그 클래스
    
    시스템 공지사항을 표시하는 다이얼로그를 제공합니다.
    """
    
    def __init__(self, title="공지사항", message="", parent=None):
        """
        초기화 함수
        
        Args:
            title (str): 다이얼로그 제목
            message (str): 공지 메시지
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.title = title
        self.message = message
        
        # UI 초기화
        self._init_ui()
    
    def _init_ui(self):
        """
        UI 초기화
        """
        # 다이얼로그 설정
        self.setWindowTitle(self.title)
        self.setFixedSize(500, 400)
        self.setWindowFlags(Qt.WindowCloseButtonHint)  # 최소화, 최대화 버튼 제거
        
        # 레이아웃 설정
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 제목 라벨
        title_label = QLabel(self.title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 공지 내용
        self.notice_text = QTextEdit()
        self.notice_text.setReadOnly(True)
        self.notice_text.setHtml(self.message)
        self.notice_text.setStyleSheet("font-size: 12pt; margin: 10px;")
        main_layout.addWidget(self.notice_text)
        
        # 다시 보지 않기 체크박스
        self.dont_show_again_checkbox = QCheckBox("다시 보지 않기")
        main_layout.addWidget(self.dont_show_again_checkbox)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        
        # 확인 버튼
        self.ok_button = QPushButton("확인")
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
    
    def is_dont_show_again(self):
        """
        다시 보지 않기 체크 여부 반환
        
        Returns:
            bool: 다시 보지 않기 체크 여부
        """
        return self.dont_show_again_checkbox.isChecked()
    
    @staticmethod
    def show_notice(title, message, parent=None):
        """
        공지 다이얼로그 표시 (정적 메서드)
        
        Args:
            title (str): 다이얼로그 제목
            message (str): 공지 메시지
            parent: 부모 위젯
            
        Returns:
            tuple: (다이얼로그 결과, 다시 보지 않기 체크 여부)
        """
        dialog = NoticeDialog(title, message, parent)
        result = dialog.exec_()
        dont_show_again = dialog.is_dont_show_again()
        return result, dont_show_again 