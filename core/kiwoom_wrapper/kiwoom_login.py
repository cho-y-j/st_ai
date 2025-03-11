"""
키움 API 로그인 모듈

이 모듈은 키움증권 Open API와의 연결 및 로그인 처리를 담당합니다.
"""

import logging
import os
import sys
import time
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop, pyqtSignal, QObject, QSettings
from PyQt5.QtWidgets import QMessageBox, QApplication
from .kiwoom_data import KiwoomData
from .kiwoom_chart import KiwoomChart

class KiwoomLogin(QObject):
    """
    키움 API 로그인 클래스
    
    키움증권 Open API와의 연결 및 로그인 처리를 담당합니다.
    """
    
    # 로그인 관련 시그널
    login_completed = pyqtSignal(bool, str)  # 성공 여부, 메시지
    
    def __init__(self):
        """
        초기화 함수
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 설정 로드
        self.settings = QSettings('AITrading', 'AITradingSystem')
        
        # 키움 API 인스턴스 생성
        try:
            self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
            self.logger.info("키움 API 인스턴스 생성 성공")
        except Exception as e:
            self.logger.error(f"키움 API 인스턴스 생성 실패: {str(e)}")
            self.logger.error("키움 Open API가 설치되어 있는지 확인하세요.")
            self.logger.error("32비트 Python 환경에서 실행해야 합니다.")
            self.logger.error("관리자 권한으로 실행해보세요.")
            raise
        
        # 데이터 인스턴스 생성
        self.data = KiwoomData(self.ocx)
        self.logger.info("키움 데이터 인스턴스 생성 성공")
        
        # 차트 인스턴스 생성
        self.chart = KiwoomChart(self.ocx)
        self.logger.info("키움 차트 인스턴스 생성 성공")
        
        # 이벤트 루프 생성 (비동기 처리용)
        self.login_event_loop = None
        
        # 이벤트 핸들러 연결
        try:
            # 이벤트 슬롯 연결
            self.ocx.OnEventConnect[int].connect(self._handler_event_connect)
            self.logger.info("이벤트 핸들러 연결 성공 (방식 1)")
        except Exception as e:
            self.logger.error(f"이벤트 핸들러 연결 실패: {str(e)}")
            raise
        
        self.logger.info("키움 API 인스턴스 생성 완료")
        
        # 계좌 비밀번호 관련 변수
        self.account_password = ""
        self.load_account_password()
    
    def load_account_password(self):
        """저장된 계좌 비밀번호 로드"""
        try:
            if self.get_account_password_saved():
                encrypted_password = self.settings.value('account/password', '')
                if encrypted_password:
                    # 실제 환경에서는 적절한 암호화/복호화 방식을 사용해야 함
                    # 여기서는 간단한 예시로 구현
                    self.account_password = self._decrypt_password(encrypted_password)
                    self.logger.info("저장된 계좌 비밀번호 로드 완료")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"계좌 비밀번호 로드 중 오류 발생: {str(e)}")
            return False
    
    def save_account_password(self, password):
        """계좌 비밀번호 저장"""
        try:
            if self.get_account_password_saved():
                # 실제 환경에서는 적절한 암호화 방식을 사용해야 함
                encrypted_password = self._encrypt_password(password)
                self.settings.setValue('account/password', encrypted_password)
                self.account_password = password
                self.logger.info("계좌 비밀번호 저장 완료")
                return True
            else:
                self.delete_saved_account_password()
                return False
        except Exception as e:
            self.logger.error(f"계좌 비밀번호 저장 중 오류 발생: {str(e)}")
            return False
    
    def delete_saved_account_password(self):
        """저장된 계좌 비밀번호 삭제"""
        try:
            self.settings.remove('account/password')
            self.account_password = ""
            self.logger.info("저장된 계좌 비밀번호 삭제 완료")
            return True
        except Exception as e:
            self.logger.error(f"계좌 비밀번호 삭제 중 오류 발생: {str(e)}")
            return False
    
    def get_account_password_saved(self):
        """계좌 비밀번호 저장 여부 확인"""
        return self.settings.value('account/save_password', False, type=bool)
    
    def set_account_password_saved(self, saved):
        """계좌 비밀번호 저장 여부 설정"""
        self.settings.setValue('account/save_password', saved)
        if not saved:
            self.delete_saved_account_password()
        return True
    
    def set_account_password(self, password):
        """계좌 비밀번호 설정"""
        self.account_password = password
        if self.get_account_password_saved():
            self.save_account_password(password)
        return True
    
    def _encrypt_password(self, password):
        """비밀번호 암호화 (간단한 예시)"""
        # 실제 환경에서는 더 안전한 암호화 방식을 사용해야 함
        return ''.join([chr(ord(c) + 1) for c in password])
    
    def _decrypt_password(self, encrypted):
        """비밀번호 복호화 (간단한 예시)"""
        # 실제 환경에서는 더 안전한 복호화 방식을 사용해야 함
        return ''.join([chr(ord(c) - 1) for c in encrypted])
    
    def _handler_event_connect(self, err_code):
        """
        로그인 이벤트 핸들러
        
        Args:
            err_code (int): 에러 코드 (0: 성공, 그 외: 실패)
        """
        try:
            self.logger.info(f"로그인 이벤트 수신: 에러 코드 {err_code}")
            
            if err_code == 0:
                self.logger.info("로그인 성공")
                self.login_completed.emit(True, "로그인 성공")
            else:
                error_message = self.get_error_message(err_code)
                self.logger.error(f"로그인 실패: {error_message}")
                self.login_completed.emit(False, f"로그인 실패: {error_message}")
            
            # 로그인 이벤트 루프 종료
            if self.login_event_loop is not None and self.login_event_loop.isRunning():
                self.login_event_loop.exit()
        
        except Exception as e:
            self.logger.error(f"로그인 이벤트 처리 중 오류 발생: {str(e)}")
            self.login_completed.emit(False, f"로그인 이벤트 처리 중 오류 발생: {str(e)}")
            if self.login_event_loop is not None and self.login_event_loop.isRunning():
                self.login_event_loop.exit()
    
    def show_account_window(self):
        """
        계좌 비밀번호 입력창 표시
        
        Returns:
            bool: 성공 여부
        """
        try:
            # 저장된 계좌 비밀번호가 있는지 확인
            if self.get_account_password_saved() and self.account_password:
                self.logger.info("저장된 계좌 비밀번호가 있습니다. 자동 입력 설정 시도")
                
                # 계좌 비밀번호 자동 입력 설정
                self.set_account_password_auto(True)
                
                # 계좌 비밀번호 입력창 표시 (자동 입력 설정이 되어 있으면 바로 처리됨)
                self.logger.info("계좌 비밀번호 입력창 표시 요청 (자동 입력 설정됨)")
                result = self.ocx.dynamicCall("KOA_Functions(QString, QString)", ["ShowAccountWindow", ""])
                self.logger.info(f"계좌 비밀번호 입력창 표시 결과: {result}")
                
                return True
            else:
                # 저장된 비밀번호가 없는 경우 일반적인 입력창 표시
                self.logger.info("계좌 비밀번호 입력창 표시 요청")
                result = self.ocx.dynamicCall("KOA_Functions(QString, QString)", ["ShowAccountWindow", ""])
                self.logger.info(f"계좌 비밀번호 입력창 표시 결과: {result}")
                return True
                
        except Exception as e:
            self.logger.error(f"계좌 비밀번호 입력창 표시 중 오류 발생: {str(e)}")
            return False
    
    def set_account_password_auto(self, auto=True):
        """
        계좌 비밀번호 자동 입력 설정
        
        Args:
            auto (bool): 자동 입력 여부
        
        Returns:
            bool: 성공 여부
        """
        try:
            self.logger.info(f"계좌 비밀번호 자동 입력 설정: {auto}")
            
            # 키움 API에서 제공하는 계좌 비밀번호 자동 입력 설정 함수 호출
            # 이 함수는 키움 API 트레이 아이콘에서 '계좌비밀번호 저장' 메뉴에서 'AUTO' 체크박스를 선택하는 것과 동일한 효과
            result = self.ocx.dynamicCall("KOA_Functions(QString, QString)", ["SetAutoAccountPasswordCheck", "1" if auto else "0"])
            
            self.logger.info(f"계좌 비밀번호 자동 입력 설정 결과: {result}")
            return True
        except Exception as e:
            self.logger.error(f"계좌 비밀번호 자동 입력 설정 중 오류 발생: {str(e)}")
            return False
    
    def login(self):
        """
        로그인 요청
        
        Returns:
            bool: 로그인 성공 여부
        """
        self.logger.info("로그인 요청 시작")
        
        # 연결 상태 확인
        connect_state = self.get_connect_state()
        if connect_state == 1:
            self.logger.info("이미 로그인되어 있습니다.")
            
            # 계좌 비밀번호 자동 입력 설정
            if self.get_account_password_saved() and self.account_password:
                self.set_account_password_auto(True)
            
            # 로그인 완료 시그널 발생
            self.login_completed.emit(True, "이미 로그인되어 있습니다.")
            return True
        
        # 로그인 요청 - CommConnect 함수 호출
        try:
            # 이벤트 루프 생성
            self.login_event_loop = QEventLoop()
            
            # 로그인 요청
            result = self.ocx.dynamicCall("CommConnect()")
            self.logger.info(f"CommConnect 호출 결과: {result}")
            
            # 로그인 완료될 때까지 대기
            self.login_event_loop.exec_()
            
            # 로그인 상태 확인
            login_status = self.get_connect_state()
            if login_status == 1:
                self.logger.info("로그인 성공 확인")
                
                # 계좌 비밀번호 자동 입력 설정
                if self.get_account_password_saved() and self.account_password:
                    self.set_account_password_auto(True)
                
                # 필요한 계좌 정보 로드
                account_list = self.get_account_list()
                self.logger.info(f"계좌 목록: {account_list}")
                
                # 로그인 완료 시그널 발생
                self.login_completed.emit(True, "로그인 성공")
                return True
            else:
                self.logger.error("로그인 실패 확인")
                self.login_completed.emit(False, "로그인 실패")
                return False
                
        except Exception as e:
            self.logger.error(f"로그인 요청 중 오류 발생: {str(e)}")
            self.login_completed.emit(False, f"로그인 요청 중 오류 발생: {str(e)}")
            return False
        finally:
            self.login_event_loop = None
    
    def get_connect_state(self):
        """
        로그인 상태 확인
        
        Returns:
            int: 연결 상태 (0: 연결 안됨, 1: 연결됨)
        """
        try:
            return self.ocx.dynamicCall("GetConnectState()")
        except Exception as e:
            self.logger.error(f"연결 상태 확인 중 오류 발생: {str(e)}")
            return 0
    
    def get_account_list(self):
        """
        계좌 목록 조회
        
        Returns:
            list: 계좌 목록
        """
        try:
            account_list = self.ocx.dynamicCall("GetLoginInfo(QString)", ["ACCLIST"]).split(';')
            return [account for account in account_list if account]
        except Exception as e:
            self.logger.error(f"계좌 목록 조회 중 오류 발생: {str(e)}")
            return []
    
    def get_user_id(self):
        """
        사용자 ID 조회
        
        Returns:
            str: 사용자 ID
        """
        try:
            return self.ocx.dynamicCall("GetLoginInfo(QString)", ["USER_ID"])
        except Exception as e:
            self.logger.error(f"사용자 ID 조회 중 오류 발생: {str(e)}")
            return ""
    
    def get_user_name(self):
        """
        사용자 이름 조회
        
        Returns:
            str: 사용자 이름
        """
        try:
            return self.ocx.dynamicCall("GetLoginInfo(QString)", ["USER_NAME"])
        except Exception as e:
            self.logger.error(f"사용자 이름 조회 중 오류 발생: {str(e)}")
            return ""
    
    def get_error_message(self, error_code):
        """
        에러 메시지 조회
        
        Args:
            error_code (int): 에러 코드
            
        Returns:
            str: 에러 메시지
        """
        try:
            return self.ocx.dynamicCall("GetErrorMessage(int)", [error_code])
        except Exception as e:
            self.logger.error(f"에러 메시지 조회 중 오류 발생: {str(e)}")
            return f"에러 코드: {error_code}" 