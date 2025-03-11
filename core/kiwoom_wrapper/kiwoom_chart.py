"""
키움 API 차트 데이터 모듈

이 모듈은 키움증권 Open API를 통한 차트 데이터 조회 및 처리를 담당합니다.
"""

import logging
from PyQt5.QtCore import QObject, pyqtSignal, QEventLoop

class KiwoomChart(QObject):
    """
    키움 API 차트 데이터 클래스
    
    차트 데이터 조회 및 처리를 담당합니다.
    """
    
    # 차트 데이터 시그널
    chart_data_received = pyqtSignal(str, str, dict)  # 종목코드, 차트 타입, 차트 데이터
    chart_data_signal = chart_data_received  # 별칭 추가 (호환성 유지)
    
    def __init__(self, ocx):
        """
        초기화
        
        Args:
            ocx: 키움 API OCX 객체
        """
        super().__init__()
        self.ocx = ocx
        self.logger = logging.getLogger(__name__)
        self.logger.info("KiwoomChart 클래스 초기화")
        
        # TR 요청 대기를 위한 이벤트 루프
        self.tr_event_loop = None
        self.tr_data = {}  # TR 데이터 저장용
        
        # 이벤트 핸들러 연결
        self.ocx.OnReceiveTrData.connect(self._handler_tr_data)
    
    def get_minute_chart(self, code, tick_range=1, date_from=None, date_to=None, next=0):
        """
        분봉 차트 데이터 요청
        
        Args:
            code (str): 종목코드
            tick_range (int): 틱 범위 (1: 1분, 3: 3분, 5: 5분, 10: 10분, 15: 15분, 30: 30분, 45: 45분, 60: 60분)
            date_from (str): 조회 시작일(YYYYMMDD)
            date_to (str): 조회 종료일(YYYYMMDD)
            next (int): 연속 조회 여부 (0: 초기 조회, 2: 연속 조회)
            
        Returns:
            dict: 분봉 차트 데이터
        """
        try:
            self.logger.info(f"분봉 차트 데이터 요청: {code}, 틱 범위: {tick_range}, 기간: {date_from} ~ {date_to}")
            
            # TR 요청 준비
            rqname = "opt10080_req"
            trcode = "opt10080"
            screen_no = "1080"
            
            # 입력 데이터 설정
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "틱범위", str(tick_range))
            
            # 조회 기간 설정 (설정된 경우)
            if date_from:
                self.ocx.dynamicCall("SetInputValue(QString, QString)", "시작일자", date_from)
            if date_to:
                self.ocx.dynamicCall("SetInputValue(QString, QString)", "종료일자", date_to)
                
            # TR 요청
            self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
            
            # 이벤트 루프 생성 및 실행
            self.tr_event_loop = QEventLoop()
            self.tr_event_loop.exec_()
            
            # 데이터 반환
            return self.tr_data.get(rqname, {})
            
        except Exception as e:
            self.logger.error(f"분봉 차트 데이터 요청 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {}
    
    def get_daily_chart(self, code, date_from=None, date_to=None, next=0):
        """
        일봉 차트 데이터 요청
        
        Args:
            code (str): 종목코드
            date_from (str): 조회 시작일(YYYYMMDD)
            date_to (str): 조회 종료일(YYYYMMDD)
            next (int): 연속 조회 여부 (0: 초기 조회, 2: 연속 조회)
            
        Returns:
            dict: 일봉 차트 데이터
        """
        try:
            self.logger.info(f"일봉 차트 데이터 요청: {code}, 기간: {date_from} ~ {date_to}")
            
            # TR 요청 준비
            rqname = "opt10081_req"
            trcode = "opt10081"
            screen_no = "1081"
            
            # 입력 데이터 설정
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "기준일자", date_to if date_to else "")
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            
            # 조회 기간 설정 (설정된 경우)
            if date_from:
                self.ocx.dynamicCall("SetInputValue(QString, QString)", "시작일자", date_from)
            if date_to:
                self.ocx.dynamicCall("SetInputValue(QString, QString)", "종료일자", date_to)
                
            # TR 요청
            self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
            
            # 이벤트 루프 생성 및 실행
            self.tr_event_loop = QEventLoop()
            self.tr_event_loop.exec_()
            
            # 데이터 반환
            return self.tr_data.get(rqname, {})
            
        except Exception as e:
            self.logger.error(f"일봉 차트 데이터 요청 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {}
    
    def get_weekly_chart(self, code, date_from=None, date_to=None, next=0):
        """
        주봉 차트 데이터 요청
        
        Args:
            code (str): 종목코드
            date_from (str): 조회 시작일(YYYYMMDD)
            date_to (str): 조회 종료일(YYYYMMDD)
            next (int): 연속 조회 여부 (0: 초기 조회, 2: 연속 조회)
            
        Returns:
            dict: 주봉 차트 데이터
        """
        try:
            self.logger.info(f"주봉 차트 데이터 요청: {code}, 기간: {date_from} ~ {date_to}")
            
            # TR 요청 준비
            rqname = "opt10082_req"
            trcode = "opt10082"
            screen_no = "1082"
            
            # 입력 데이터 설정
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "기준일자", date_to if date_to else "")
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            
            # 조회 기간 설정 (설정된 경우)
            if date_from:
                self.ocx.dynamicCall("SetInputValue(QString, QString)", "시작일자", date_from)
            if date_to:
                self.ocx.dynamicCall("SetInputValue(QString, QString)", "종료일자", date_to)
                
            # TR 요청
            self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
            
            # 이벤트 루프 생성 및 실행
            self.tr_event_loop = QEventLoop()
            self.tr_event_loop.exec_()
            
            # 데이터 반환
            return self.tr_data.get(rqname, {})
            
        except Exception as e:
            self.logger.error(f"주봉 차트 데이터 요청 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {}
    
    def get_monthly_chart(self, code, date_from=None, date_to=None, next=0):
        """
        월봉 차트 데이터 요청
        
        Args:
            code (str): 종목코드
            date_from (str): 조회 시작일(YYYYMMDD)
            date_to (str): 조회 종료일(YYYYMMDD)
            next (int): 연속 조회 여부 (0: 초기 조회, 2: 연속 조회)
            
        Returns:
            dict: 월봉 차트 데이터
        """
        try:
            self.logger.info(f"월봉 차트 데이터 요청: {code}, 기간: {date_from} ~ {date_to}")
            
            # TR 요청 준비
            rqname = "opt10083_req"
            trcode = "opt10083"
            screen_no = "1083"
            
            # 입력 데이터 설정
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "기준일자", date_to if date_to else "")
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            
            # 조회 기간 설정 (설정된 경우)
            if date_from:
                self.ocx.dynamicCall("SetInputValue(QString, QString)", "시작일자", date_from)
            if date_to:
                self.ocx.dynamicCall("SetInputValue(QString, QString)", "종료일자", date_to)
                
            # TR 요청
            self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
            
            # 이벤트 루프 생성 및 실행
            self.tr_event_loop = QEventLoop()
            self.tr_event_loop.exec_()
            
            # 데이터 반환
            return self.tr_data.get(rqname, {})
            
        except Exception as e:
            self.logger.error(f"월봉 차트 데이터 요청 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {}
    
    def _handler_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        """
        TR 데이터 수신 이벤트 핸들러
        
        Args:
            screen_no (str): 화면번호
            rqname (str): 사용자 구분명
            trcode (str): TR 코드
            record_name (str): 레코드 이름
            next (str): 연속 조회 여부
        """
        try:
            self.logger.debug(f"TR 데이터 수신: {rqname}, {trcode}, {next}")
            
            # 분봉 차트 조회 응답 처리
            if rqname == "opt10080_req" and trcode == "opt10080":
                self._process_minute_chart_data(trcode, rqname, next)
                
            # 일봉 차트 조회 응답 처리
            elif rqname == "opt10081_req" and trcode == "opt10081":
                self._process_daily_chart_data(trcode, rqname, next)
                
            # 주봉 차트 조회 응답 처리
            elif rqname == "opt10082_req" and trcode == "opt10082":
                self._process_weekly_chart_data(trcode, rqname, next)
                
            # 월봉 차트 조회 응답 처리
            elif rqname == "opt10083_req" and trcode == "opt10083":
                self._process_monthly_chart_data(trcode, rqname, next)
                
            # 이벤트 루프 종료
            if self.tr_event_loop is not None:
                self.tr_event_loop.exit()
                
        except Exception as e:
            self.logger.error(f"TR 데이터 처리 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            # 이벤트 루프 종료
            if self.tr_event_loop is not None:
                self.tr_event_loop.exit()
    
    def _process_minute_chart_data(self, trcode, rqname, next):
        """
        분봉 차트 데이터 처리
        
        Args:
            trcode (str): TR 코드
            rqname (str): 사용자 구분명
            next (str): 연속 조회 여부
        """
        try:
            # 데이터 개수 확인
            data_count = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            self.logger.debug(f"분봉 차트 데이터 개수: {data_count}")
            
            # 분봉 데이터 저장
            minute_data = {
                "date": [],        # 날짜
                "time": [],        # 시간
                "open": [],        # 시가
                "high": [],        # 고가
                "low": [],         # 저가
                "close": [],       # 종가
                "volume": [],      # 거래량
                "next": next       # 연속 조회 여부
            }
            
            # 데이터 추출
            for i in range(data_count):
                date = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "체결시간")
                open_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시가")
                high_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "고가")
                low_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "저가")
                close_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가")
                volume = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래량")
                
                # 데이터 형식 변환
                date = date.strip()
                date_only = date[:8]  # YYYYMMDD
                time_only = date[8:12]  # HHMM
                
                open_price = abs(int(open_price.strip()))
                high_price = abs(int(high_price.strip()))
                low_price = abs(int(low_price.strip()))
                close_price = abs(int(close_price.strip()))
                volume = int(volume.strip())
                
                # 데이터 저장
                minute_data["date"].append(date_only)
                minute_data["time"].append(time_only)
                minute_data["open"].append(open_price)
                minute_data["high"].append(high_price)
                minute_data["low"].append(low_price)
                minute_data["close"].append(close_price)
                minute_data["volume"].append(volume)
            
            # 데이터 저장
            self.tr_data[rqname] = minute_data
            
            # 종목코드 추출
            code = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "종목코드").strip()
            if not code:
                code = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "종목코드").strip()
            
            # 시그널 발생
            self.chart_data_received.emit(code, "minute", minute_data)
            
            self.logger.info(f"분봉 차트 데이터 처리 완료: {len(minute_data['date'])}개")
            
        except Exception as e:
            self.logger.error(f"분봉 차트 데이터 처리 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _process_daily_chart_data(self, trcode, rqname, next):
        """
        일봉 차트 데이터 처리
        
        Args:
            trcode (str): TR 코드
            rqname (str): 사용자 구분명
            next (str): 연속 조회 여부
        """
        try:
            # 데이터 개수 확인
            data_count = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            self.logger.debug(f"일봉 차트 데이터 개수: {data_count}")
            
            # 일봉 데이터 저장
            daily_data = {
                "date": [],        # 날짜
                "open": [],        # 시가
                "high": [],        # 고가
                "low": [],         # 저가
                "close": [],       # 종가
                "volume": [],      # 거래량
                "next": next       # 연속 조회 여부
            }
            
            # 데이터 추출
            for i in range(data_count):
                date = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "일자")
                open_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시가")
                high_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "고가")
                low_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "저가")
                close_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가")
                volume = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래량")
                
                # 데이터 형식 변환
                date = date.strip()
                open_price = abs(int(open_price.strip()))
                high_price = abs(int(high_price.strip()))
                low_price = abs(int(low_price.strip()))
                close_price = abs(int(close_price.strip()))
                volume = int(volume.strip())
                
                # 데이터 저장
                daily_data["date"].append(date)
                daily_data["open"].append(open_price)
                daily_data["high"].append(high_price)
                daily_data["low"].append(low_price)
                daily_data["close"].append(close_price)
                daily_data["volume"].append(volume)
            
            # 데이터 저장
            self.tr_data[rqname] = daily_data
            
            # 종목코드 추출
            code = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "종목코드").strip()
            if not code:
                code = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "종목코드").strip()
            
            # 시그널 발생
            self.chart_data_received.emit(code, "day", daily_data)
            
            self.logger.info(f"일봉 차트 데이터 처리 완료: {len(daily_data['date'])}개")
            
        except Exception as e:
            self.logger.error(f"일봉 차트 데이터 처리 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _process_weekly_chart_data(self, trcode, rqname, next):
        """
        주봉 차트 데이터 처리
        
        Args:
            trcode (str): TR 코드
            rqname (str): 사용자 구분명
            next (str): 연속 조회 여부
        """
        try:
            # 데이터 개수 확인
            data_count = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            self.logger.debug(f"주봉 차트 데이터 개수: {data_count}")
            
            # 주봉 데이터 저장
            weekly_data = {
                "date": [],        # 날짜
                "open": [],        # 시가
                "high": [],        # 고가
                "low": [],         # 저가
                "close": [],       # 종가
                "volume": [],      # 거래량
                "next": next       # 연속 조회 여부
            }
            
            # 데이터 추출
            for i in range(data_count):
                date = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "일자")
                open_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시가")
                high_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "고가")
                low_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "저가")
                close_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가")
                volume = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래량")
                
                # 데이터 형식 변환
                date = date.strip()
                open_price = abs(int(open_price.strip()))
                high_price = abs(int(high_price.strip()))
                low_price = abs(int(low_price.strip()))
                close_price = abs(int(close_price.strip()))
                volume = int(volume.strip())
                
                # 데이터 저장
                weekly_data["date"].append(date)
                weekly_data["open"].append(open_price)
                weekly_data["high"].append(high_price)
                weekly_data["low"].append(low_price)
                weekly_data["close"].append(close_price)
                weekly_data["volume"].append(volume)
            
            # 데이터 저장
            self.tr_data[rqname] = weekly_data
            
            # 종목코드 추출
            code = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "종목코드").strip()
            if not code:
                code = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "종목코드").strip()
            
            # 시그널 발생
            self.chart_data_received.emit(code, "week", weekly_data)
            
            self.logger.info(f"주봉 차트 데이터 처리 완료: {len(weekly_data['date'])}개")
            
        except Exception as e:
            self.logger.error(f"주봉 차트 데이터 처리 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _process_monthly_chart_data(self, trcode, rqname, next):
        """
        월봉 차트 데이터 처리
        
        Args:
            trcode (str): TR 코드
            rqname (str): 사용자 구분명
            next (str): 연속 조회 여부
        """
        try:
            # 데이터 개수 확인
            data_count = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            self.logger.debug(f"월봉 차트 데이터 개수: {data_count}")
            
            # 월봉 데이터 저장
            monthly_data = {
                "date": [],        # 날짜
                "open": [],        # 시가
                "high": [],        # 고가
                "low": [],         # 저가
                "close": [],       # 종가
                "volume": [],      # 거래량
                "next": next       # 연속 조회 여부
            }
            
            # 데이터 추출
            for i in range(data_count):
                date = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "일자")
                open_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시가")
                high_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "고가")
                low_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "저가")
                close_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가")
                volume = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래량")
                
                # 데이터 형식 변환
                date = date.strip()
                open_price = abs(int(open_price.strip()))
                high_price = abs(int(high_price.strip()))
                low_price = abs(int(low_price.strip()))
                close_price = abs(int(close_price.strip()))
                volume = int(volume.strip())
                
                # 데이터 저장
                monthly_data["date"].append(date)
                monthly_data["open"].append(open_price)
                monthly_data["high"].append(high_price)
                monthly_data["low"].append(low_price)
                monthly_data["close"].append(close_price)
                monthly_data["volume"].append(volume)
            
            # 데이터 저장
            self.tr_data[rqname] = monthly_data
            
            # 종목코드 추출
            code = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "종목코드").strip()
            if not code:
                code = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "종목코드").strip()
            
            # 시그널 발생
            self.chart_data_received.emit(code, "month", monthly_data)
            
            self.logger.info(f"월봉 차트 데이터 처리 완료: {len(monthly_data['date'])}개")
            
        except Exception as e:
            self.logger.error(f"월봉 차트 데이터 처리 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc()) 