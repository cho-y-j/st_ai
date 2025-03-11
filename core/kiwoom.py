class Kiwoom(QObject):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 설정 로드
        self.settings = QSettings("StockAI", "KiwoomTrader")
        
        # OCX 객체 생성
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        
        # 이벤트 핸들러 설정
        self._connect_slots()
        
        # 데이터 객체 초기화
        self.data = KiwoomData(self.ocx)
        
        self.logger.info("Kiwoom 클래스 초기화 완료")
    
    def connect(self):
        """
        키움 서버 접속
        """
        try:
            self.logger.info("키움 서버 접속 시도...")
            self.ocx.dynamicCall("CommConnect()")
            return True
            
        except Exception as e:
            self.logger.error(f"서버 접속 중 오류 발생: {str(e)}")
            return False
    
    def get_connect_state(self):
        """
        서버 접속 상태 확인
        
        Returns:
            bool: 접속 여부
        """
        try:
            state = self.ocx.dynamicCall("GetConnectState()")
            return state == 1
            
        except Exception as e:
            self.logger.error(f"서버 상태 확인 중 오류 발생: {str(e)}")
            return False
    
    def get_login_info(self, tag):
        """
        로그인 정보 조회
        
        Args:
            tag (str): 조회할 정보 (ACCOUNT_CNT, ACCNO, USER_ID, USER_NAME, GetServerGubun)
            
        Returns:
            str: 요청한 정보
        """
        try:
            ret = self.ocx.dynamicCall("GetLoginInfo(QString)", tag)
            return ret.strip()
            
        except Exception as e:
            self.logger.error(f"로그인 정보 조회 중 오류 발생: {str(e)}")
            return ""
    
    def get_account_list(self):
        """
        보유계좌 리스트 조회
        
        Returns:
            list: 계좌번호 리스트
        """
        try:
            account_str = self.get_login_info("ACCNO")
            return account_str.split(';')[:-1]  # 마지막 빈 문자열 제거
            
        except Exception as e:
            self.logger.error(f"계좌 목록 조회 중 오류 발생: {str(e)}")
            return []
    
    def get_account_password_saved(self):
        """계좌 비밀번호 저장 여부 확인"""
        return self.settings.value("account/save_password", False, type=bool)
    
    def set_account_password_saved(self, save):
        """계좌 비밀번호 저장 여부 설정"""
        self.settings.setValue("account/save_password", save)
        self.settings.sync()
        
        # 저장하지 않기로 한 경우 저장된 비밀번호 삭제
        if not save:
            self.delete_saved_account_password()
    
    def get_saved_account_password(self):
        """저장된 계좌 비밀번호 조회"""
        if self.get_account_password_saved():
            return self.settings.value("account/password", "", type=str)
        return ""
    
    def save_account_password(self, password):
        """계좌 비밀번호 저장"""
        if self.get_account_password_saved():
            self.settings.setValue("account/password", password)
            self.settings.sync()
    
    def delete_saved_account_password(self):
        """저장된 계좌 비밀번호 삭제"""
        self.settings.remove("account/password")
        self.settings.sync()
    
    def _connect_slots(self):
        """
        이벤트 슬롯 연결
        """
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveMsg.connect(self._handler_msg)
        self.ocx.OnReceiveChejanData.connect(self._handler_chejan)
    
    def _handler_login(self, err_code):
        """
        로그인 이벤트 처리
        """
        try:
            if err_code == 0:
                self.logger.info("로그인 성공")
                
                # 계좌 비밀번호가 저장되어 있으면 자동으로 입력
                if self.get_account_password_saved():
                    password = self.get_saved_account_password()
                    if password:
                        self.ocx.dynamicCall("KOA_Functions(QString, QString)", "ShowAccountWindow", "")
                        self.ocx.dynamicCall("SetInputValue(QString, QString)", "계좌비밀번호", password)
                        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", 
                                           "계좌비밀번호입력", "opw00001", 0, "0101")
            else:
                self.logger.error(f"로그인 실패: {err_code}")
            
        except Exception as e:
            self.logger.error(f"로그인 처리 중 오류 발생: {str(e)}")
    
    def _handler_msg(self, screen_no, rqname, trcode, msg):
        """
        메시지 수신 이벤트 처리
        """
        try:
            self.logger.info(f"메시지 수신: {msg}")
            
            # 계좌 비밀번호 입력 성공 시 저장
            if rqname == "계좌비밀번호입력" and "정상" in msg:
                password = self.ocx.dynamicCall("GetInputValue(QString)", "계좌비밀번호")
                self.save_account_password(password)
            
        except Exception as e:
            self.logger.error(f"메시지 처리 중 오류 발생: {str(e)}")
    
    def _handler_chejan(self, gubun, item_cnt, fid_list):
        """
        체결잔고 이벤트 처리
        """
        try:
            if gubun == "0":  # 주문체결
                self.logger.debug("주문체결 발생")
            elif gubun == "1":  # 잔고변경
                self.logger.debug("잔고변경 발생")
            
        except Exception as e:
            self.logger.error(f"체결잔고 처리 중 오류 발생: {str(e)}") 