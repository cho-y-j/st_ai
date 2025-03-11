"""
키움 API 데이터 조회 모듈

이 모듈은 키움증권 API를 통한 데이터 조회 기능을 제공합니다.
- 종목 정보 조회
- 실시간 시세 조회
- 호가 데이터 조회
"""

import logging
from PyQt5.QtCore import QObject, pyqtSignal, QEventLoop
from PyQt5.QAxContainer import QAxWidget

class KiwoomData(QObject):
    """
    키움 API 데이터 조회 클래스
    
    실시간 데이터 조회 및 이벤트 처리를 담당합니다.
    """
    
    # 실시간 데이터 시그널
    price_updated = pyqtSignal(str, dict)  # 종목코드, 가격 정보
    hoga_updated = pyqtSignal(str, dict)   # 종목코드, 호가 정보
    tick_updated = pyqtSignal(str, dict)   # 종목코드, 체결 정보
    connection_status_updated = pyqtSignal(bool)  # 서버 연결 상태
    
    def __init__(self, ocx):
        """
        초기화
        
        Args:
            ocx: 키움 API OCX 객체
        """
        super().__init__()
        self.ocx = ocx
        self.logger = logging.getLogger(__name__)
        self.logger.info("KiwoomData 클래스 초기화 시작")
        
        # 실시간 데이터 수신 종목 코드
        self.subscribed_codes = set()
        
        # 종목 코드 캐시
        self.code_cache = {}
        
        # 실시간 FID 목록
        self.fids = {
            "체결시간": "20",
            "현재가": "10",
            "전일대비": "11",
            "등락율": "12",
            "거래량": "15",
            "거래대금": "16",
            "시가": "13",
            "고가": "14",
            "저가": "17",
            "매도호가1": "41",
            "매수호가1": "51",
            "매도호가2": "42",
            "매수호가2": "52",
            "매도호가3": "43",
            "매수호가3": "53",
            "매도호가4": "44",
            "매수호가4": "54",
            "매도호가5": "45",
            "매수호가5": "55",
            "매도호가수량1": "61",
            "매수호가수량1": "71",
            "매도호가수량2": "62",
            "매수호가수량2": "72",
            "매도호가수량3": "63",
            "매수호가수량3": "73",
            "매도호가수량4": "64",
            "매수호가수량4": "74",
            "매도호가수량5": "65",
            "매수호가수량5": "75",
        }
        
        # 이벤트 핸들러 연결
        self.ocx.OnReceiveRealData.connect(self._handler_real_data)
        self.ocx.OnReceiveTrData.connect(self._handler_tr_data)
        self.ocx.OnReceiveMsg.connect(self._handler_msg)
        
        # TR 요청 대기를 위한 이벤트 루프
        self.tr_event_loop = None
        self.tr_data = {}  # TR 데이터 저장용
        
        # 종목 코드 캐시 초기화
        self._init_code_cache()
        
        self.logger.info("KiwoomData 클래스 초기화 완료")

    def search_stock(self, code):
        """
        종목 기본 정보 검색
        
        Args:
            code (str): 종목코드
            
        Returns:
            dict: 종목 정보 딕셔너리. 실패시 빈 딕셔너리 반환
        """
        try:
            self.logger.info(f"종목 검색 시작: {code}")
            
            # 연결 상태 확인
            state = self.ocx.dynamicCall("GetConnectState()")
            if state != 1:
                self.logger.error("키움 서버에 연결되어 있지 않습니다.")
                return {}
            
            # TR 입력값 설정
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            
            # TR 요청
            rqname = "주식기본정보요청"
            trcode = "opt10001"
            next = 0
            screen_no = "0101"
            
            result = self.ocx.dynamicCall(
                "CommRqData(QString, QString, int, QString)",
                rqname, trcode, next, screen_no
            )
            
            if result != 0:
                self.logger.error(f"종목 정보 요청 실패. 에러코드: {result}")
                return {}
                
            # 응답 대기
            self.tr_event_loop = QEventLoop()
            self.tr_event_loop.exec_()
            
            if not self.tr_data:
                self.logger.error("종목 정보 수신 실패")
                return {}
                
            self.logger.info(f"종목 검색 완료: {code}")
            return self.tr_data
            
        except Exception as e:
            self.logger.error(f"종목 검색 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {}

    def check_connection(self):
        """서버 연결 상태 확인"""
        try:
            state = self.ocx.dynamicCall("GetConnectState()")
            is_connected = state == 1
            self.connection_status_updated.emit(is_connected)
            return is_connected
        except Exception as e:
            self.logger.error(f"서버 연결 상태 확인 중 오류 발생: {str(e)}")
            self.connection_status_updated.emit(False)
            return False

    def _init_code_cache(self):
        """종목 코드 캐시 초기화"""
        try:
            self.logger.info("=== 종목 코드 캐시 초기화 시작 ===")
            
            # 연결 상태 확인
            state = self.ocx.dynamicCall("GetConnectState()")
            self.logger.info(f"서버 연결 상태: {state}")
            
            if state != 1:
                self.logger.error("키움 서버에 연결되어 있지 않습니다. 로그인이 필요합니다.")
                return
            
            # 코스피 종목 로드
            self.logger.info("=== 코스피 종목 로드 시작 ===")
            kospi_raw = self.ocx.dynamicCall("GetCodeListByMarket(QString)", "0")
            self.logger.info(f"코스피 원본 데이터: {kospi_raw}")
            
            if not kospi_raw:
                self.logger.error("코스피 종목 코드 수신 실패")
                return
            
            # 세미콜론으로 분리하고 마지막 빈 항목 제거
            kospi_codes = kospi_raw.split(";")
            kospi_codes = kospi_codes[:-1] if kospi_codes[-1] == "" else kospi_codes
            self.logger.info(f"코스피 종목코드 수신: {len(kospi_codes)}개")
            self.logger.info(f"처음 5개 코스피 종목: {kospi_codes[:5]}")
            
            # 코스닥 종목 로드
            self.logger.info("=== 코스닥 종목 로드 시작 ===")
            kosdaq_raw = self.ocx.dynamicCall("GetCodeListByMarket(QString)", "10")
            self.logger.info(f"코스닥 원본 데이터: {kosdaq_raw}")
            
            if not kosdaq_raw:
                self.logger.error("코스닥 종목 코드 수신 실패")
                return
            
            # 세미콜론으로 분리하고 마지막 빈 항목 제거
            kosdaq_codes = kosdaq_raw.split(";")
            kosdaq_codes = kosdaq_codes[:-1] if kosdaq_codes[-1] == "" else kosdaq_codes
            self.logger.info(f"코스닥 종목코드 수신: {len(kosdaq_codes)}개")
            self.logger.info(f"처음 5개 코스닥 종목: {kosdaq_codes[:5]}")
            
            # 전체 종목 코드 리스트 생성
            total_codes = kospi_codes + kosdaq_codes
            self.logger.info(f"=== 전체 종목 수: {len(total_codes)}개 ===")
            
            # 기존 캐시 초기화
            self.code_cache.clear()
            
            # 종목명 조회
            self.logger.info("=== 종목명 조회 시작 ===")
            success_count = 0
            
            for i, code in enumerate(total_codes):
                try:
                    name = self.ocx.dynamicCall("GetMasterCodeName(QString)", code)
                    if name:
                        name = name.strip()
                        self.code_cache[code] = name
                        success_count += 1
                        
                        # 처음 5개 종목만 상세 로깅
                        if success_count <= 5:
                            self.logger.info(f"종목 추가: [{code}] {name}")
                            
                        # 100개 단위로 진행상황 로깅
                        if (i + 1) % 100 == 0:
                            self.logger.info(f"진행 상황: {i + 1}/{len(total_codes)} 종목 처리 완료 (성공: {success_count}개)")
                    else:
                        self.logger.warning(f"종목명 조회 실패: {code}")
                except Exception as e:
                    self.logger.error(f"종목 {code} 처리 중 오류: {str(e)}")
            
            self.logger.info(f"=== 종목 코드 캐시 초기화 완료 ===")
            self.logger.info(f"전체 종목 수: {len(total_codes)}개")
            self.logger.info(f"성공적으로 로드된 종목 수: {success_count}개")
            
            if not self.code_cache:
                self.logger.error("종목 코드 캐시가 비어있습니다. 초기화에 실패했을 수 있습니다.")
            
        except Exception as e:
            self.logger.error(f"종목 코드 캐시 초기화 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

    def get_code_list(self):
        """
        현재 캐시된 종목 코드 목록 조회
        
        Returns:
            list: [(종목코드, 종목명)] 형식의 리스트
        """
        try:
            codes = [(code, name) for code, name in self.code_cache.items()]
            self.logger.info(f"종목 코드 조회: 총 {len(codes)}개")
            return sorted(codes, key=lambda x: x[1])  # 종목명 기준 정렬
        except Exception as e:
            self.logger.error(f"종목 코드 조회 중 오류: {str(e)}")
            return []

    def _handler_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        """
        TR 데이터 수신 이벤트 처리
        
        Args:
            screen_no (str): 화면번호
            rqname (str): 사용자 구분명
            trcode (str): TR 코드
            record_name (str): 레코드명
            next (str): 연속조회 유무
            unused1-4: 미사용
        """
        try:
            self.logger.debug(f"TR 데이터 수신: {rqname}, {trcode}")
            
            if rqname == "주식기본정보요청" and trcode == "opt10001":
                # OPT10001 TR 응답 처리
                columns = [
                    "종목코드", "종목명", "결산월", "액면가", "자본금", "상장주식", "신용비율", 
                    "연중최고", "시가총액", "시가총액비중", "외인소진률", "대용가", "PER", "EPS", 
                    "ROE", "PBR", "EV", "BPS", "매출액", "영업이익", "당기순이익", "250최고", 
                    "250최저", "시가", "고가", "저가", "상한가", "하한가", "기준가", "예상체결가", 
                    "예상체결수량", "250최고가일", "250최고가대비율", "250최저가일", "250최저가대비율", 
                    "현재가", "대비기호", "전일대비", "등락율", "거래량", "거래대비", "액면가단위", 
                    "유통주식", "유통비율"
                ]
                
                self.tr_data = {}
                for col in columns:
                    value = self.ocx.dynamicCall(
                        "GetCommData(QString, QString, int, QString)", 
                        trcode, rqname, 0, col
                    ).strip()
                    self.tr_data[col] = value
                    self.logger.debug(f"{col}: {value}")
                    
                self.logger.debug(f"종목 정보 수신 완료: {self.tr_data}")
                
            if self.tr_event_loop is not None:
                self.tr_event_loop.exit()
                
        except Exception as e:
            self.logger.error(f"TR 데이터 처리 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            if self.tr_event_loop is not None:
                self.tr_event_loop.exit()

    def _handler_msg(self, screen_no, rqname, trcode, msg):
        """
        TR 메시지 수신 이벤트 처리
        
        Args:
            screen_no (str): 화면번호
            rqname (str): 사용자 구분명
            trcode (str): TR 코드
            msg (str): 서버 메시지
        """
        self.logger.info(f"TR 메시지 수신: {msg} (화면번호: {screen_no}, TR: {trcode}, RQ: {rqname})")

    def _handler_real_data(self, code, real_type, data):
        """
        실시간 데이터 수신 이벤트 처리
        
        Args:
            code (str): 종목코드
            real_type (str): 실시간 타입
            data (str): 데이터
        """
        try:
            # 로깅 추가: 실시간 데이터 수신 확인
            self.logger.debug(f"실시간 데이터 수신: 종목코드={code}, 타입={real_type}")
            
            if real_type == "주식체결":
                # 현재가 정보 생성
                price_data = {
                    "current_price": abs(int(self.ocx.dynamicCall("GetCommRealData(QString, int)", [code, int(self.fids["현재가"])]))),
                    "price_change": int(self.ocx.dynamicCall("GetCommRealData(QString, int)", [code, int(self.fids["전일대비"])])),
                    "change_rate": float(self.ocx.dynamicCall("GetCommRealData(QString, int)", [code, int(self.fids["등락율"])])),
                    "volume": int(self.ocx.dynamicCall("GetCommRealData(QString, int)", [code, int(self.fids["거래량"])]))
                }
                
                # 가격 정보 시그널 발생
                self.logger.debug(f"가격 정보 시그널 발생: {code}, {price_data}")
                self.price_updated.emit(code, price_data)
                
            elif real_type == "주식호가잔량":
                # 호가 정보 생성
                hoga_data = {
                    "ask_prices": [],   # 매도호가
                    "bid_prices": [],   # 매수호가
                    "ask_volumes": [],  # 매도호가수량
                    "bid_volumes": []   # 매수호가수량
                }
                
                # 5단계 호가 정보 조회
                for i in range(1, 6):
                    ask_price = abs(int(self.ocx.dynamicCall("GetCommRealData(QString, int)", [code, int(self.fids[f"매도호가{i}"])])))
                    bid_price = abs(int(self.ocx.dynamicCall("GetCommRealData(QString, int)", [code, int(self.fids[f"매수호가{i}"])])))
                    ask_volume = int(self.ocx.dynamicCall("GetCommRealData(QString, int)", [code, int(self.fids[f"매도호가수량{i}"])]))
                    bid_volume = int(self.ocx.dynamicCall("GetCommRealData(QString, int)", [code, int(self.fids[f"매수호가수량{i}"])]))
                    
                    hoga_data["ask_prices"].append(ask_price)
                    hoga_data["bid_prices"].append(bid_price)
                    hoga_data["ask_volumes"].append(ask_volume)
                    hoga_data["bid_volumes"].append(bid_volume)
                
                # 호가 정보 시그널 발생
                self.logger.debug(f"호가 정보 시그널 발생: {code}, {hoga_data}")
                self.hoga_updated.emit(code, hoga_data)
            
        except Exception as e:
            self.logger.error(f"실시간 데이터 처리 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

    def search_stocks(self, keyword):
        """
        종목 검색 (코드 또는 이름으로 검색)
        
        Args:
            keyword (str): 검색어 (종목코드 또는 종목명)
            
        Returns:
            list: [(종목코드, 종목명)] 형식의 검색 결과 리스트
        """
        try:
            if not keyword or len(keyword.strip()) < 1:
                self.logger.warning("검색어가 비어있습니다.")
                return []
                
            self.logger.info(f"종목 검색 시작: 키워드='{keyword}', 캐시된 종목 수={len(self.code_cache)}")
            
            # 캐시가 비어있으면 초기화 시도
            if not self.code_cache:
                self.logger.warning("종목 코드 캐시가 비어있습니다. 초기화를 시도합니다.")
                self._init_code_cache()
                
                # 초기화 후에도 비어있으면 빈 결과 반환
                if not self.code_cache:
                    self.logger.error("종목 코드 캐시 초기화 실패. 검색을 수행할 수 없습니다.")
                    return []
            
            results = []
            keyword = keyword.upper().strip()
            
            # 종목코드가 정확히 일치하는 경우 우선 처리
            if keyword in self.code_cache:
                name = self.code_cache[keyword]
                results.append((keyword, name))
                self.logger.info(f"정확한 종목코드 일치: [{keyword}] {name}")
                return results
            
            # 부분 일치 검색
            for code, name in self.code_cache.items():
                if keyword in code or keyword in name.upper():
                    results.append((code, name))
            
            # 결과 정렬 (종목명 기준)
            results = sorted(results, key=lambda x: x[1])
            
            self.logger.info(f"검색 결과: {len(results)}개 종목")
            if len(results) > 0:
                self.logger.info(f"첫 번째 검색 결과: [{results[0][0]}] {results[0][1]}")
            
            return results
                
        except Exception as e:
            self.logger.error(f"종목 검색 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return [] 