"""
# AI 트레이딩 시스템 - 메인 프로그램
# 
# 이 파일은 프로그램의 진입점으로, 다음 기능을 담당합니다:
# 1. 키움 API 로그인 및 초기화
# 2. 메인 윈도우 생성 및 UI 컴포넌트 초기화
"""

import sys
import os
import logging
import platform
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt5.QtCore import QEventLoop, QSettings

# 로깅 설정
def setup_logging():
    """로깅 설정"""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # 파일 핸들러
    file_handler = logging.FileHandler('ai_trading.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger

# UI 모듈 임포트
from ui.main_window import MainWindow
from ui.dialogs.login_dialog import LoginDialog

# 코어 모듈 임포트
from core.kiwoom_wrapper.kiwoom_login import KiwoomLogin

def check_environment():
    """
    환경 체크
    
    Returns:
        tuple: (성공 여부, 메시지)
    """
    logger = logging.getLogger(__name__)
    
    # Python 버전 체크
    python_version = platform.python_version()
    python_bit = platform.architecture()[0]
    
    # 운영체제 체크
    os_name = platform.system()
    os_version = platform.version()
    
    # 로그 출력
    logger.info(f"Python 버전: {python_version} ({python_bit})")
    logger.info(f"운영체제: {os_name} {os_version}")
    
    # 32비트 Python 체크
    if python_bit != "32bit":
        return False, "키움 API는 32비트 Python에서만 동작합니다. 32비트 Python 환경에서 실행해주세요."
    
    # Windows 체크
    if os_name != "Windows":
        return False, "키움 API는 Windows에서만 동작합니다."
    
    return True, "환경 체크 완료"

def main():
    """
    프로그램 메인 함수
    """
    # 로깅 설정
    logger = setup_logging()
    logger.info("AI 트레이딩 시스템 시작...")
    
    try:
        # 환경 체크
        env_ok, env_message = check_environment()
        if not env_ok:
            logger.error(f"환경 체크 실패: {env_message}")
            print("\n" + "="*80)
            print("환경 오류:")
            print(env_message)
            print("="*80 + "\n")
            
            # GUI가 필요한 경우에만 QApplication 생성
            if 'QApplication' not in locals():
                app = QApplication(sys.argv)
                QMessageBox.critical(None, "환경 오류", env_message)
            return 1
        
        # QApplication 인스턴스 생성
        app = QApplication(sys.argv)
        
        # 키움 API 인스턴스 생성
        logger.info("키움 API 초기화 중...")
        try:
            kiwoom = KiwoomLogin()
        except Exception as e:
            logger.exception("키움 API 초기화 실패")
            error_message = f"""
            키움 API 초기화에 실패했습니다.
            
            가능한 원인:
            1. 키움 Open API가 설치되지 않았습니다.
            2. 32비트 Python 환경이 아닙니다.
            3. 관리자 권한으로 실행해야 할 수 있습니다.
            
            오류 메시지: {str(e)}
            """
            QMessageBox.critical(None, "키움 API 오류", error_message)
            return 1
        
        # 통합 로그인 다이얼로그 표시 (공지사항 + 로그인)
        logger.info("로그인 다이얼로그 표시...")
        login_dialog = LoginDialog(kiwoom)
        
        # 로그인 완료 시그널 연결
        login_success = [False]  # 리스트를 사용하여 참조로 전달
        
        def on_login_completed(success, message):
            login_success[0] = success
            if not success:
                logger.error(f"로그인 실패: {message}")
                QMessageBox.critical(None, "로그인 오류", message)
            else:
                logger.info(f"로그인 성공: {message}")
                # 계좌 정보 로깅
                account_list = kiwoom.get_account_list()
                user_id = kiwoom.get_user_id()
                user_name = kiwoom.get_user_name()
                logger.info(f"사용자 ID: {user_id}, 이름: {user_name}")
                logger.info(f"계좌 목록: {account_list}")
        
        # 로그인 완료 시그널 연결
        login_dialog.login_completed.connect(on_login_completed)
        
        # 로그인 다이얼로그 표시
        login_dialog.show()
        
        # 로그인 다이얼로그가 완료될 때까지 대기
        if login_dialog.exec_() == QDialog.Accepted and login_success[0]:
            # 공지사항 다시 보지 않기 설정 저장
            dont_show_again = login_dialog.is_dont_show_again()
            if dont_show_again:
                settings = QSettings('AITrading', 'AITradingSystem')
                settings.setValue('notice/dont_show_again', True)
                logger.info("공지사항 다시 보지 않기 설정 저장")
            
            # 메인 윈도우 생성 및 표시
            logger.info("메인 윈도우 생성 중...")
            main_window = MainWindow(kiwoom)
            
            logger.info("메인 윈도우 표시...")
            main_window.show()
            
            # 이벤트 루프 시작
            return app.exec_()
        else:
            logger.warning("로그인이 취소되었거나 실패했습니다.")
            return 0
    
    except Exception as e:
        logger.exception("프로그램 실행 중 오류 발생")
        QMessageBox.critical(None, "오류", f"프로그램 실행 중 오류가 발생했습니다.\n{str(e)}")
        return 1
    
    finally:
        logger.info("프로그램 종료")

if __name__ == "__main__":
    sys.exit(main()) 