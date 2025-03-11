"""
기술적 지표 계산 모듈

이 모듈은 주식 차트에 사용되는 다양한 기술적 지표를 계산하는 함수를 제공합니다.
"""

import numpy as np
import pandas as pd

def moving_average(data, period=20):
    """
    이동평균선 계산
    
    Args:
        data (numpy.ndarray): 가격 데이터
        period (int): 이동평균 기간
        
    Returns:
        numpy.ndarray: 이동평균 데이터
    """
    if len(data) < period:
        return np.array([np.nan] * len(data))
        
    ma = np.zeros_like(data)
    for i in range(len(data)):
        if i < period - 1:
            ma[i] = np.nan
        else:
            ma[i] = np.mean(data[max(0, i-period+1):i+1])
    
    return ma

def exponential_moving_average(data, period=20):
    """
    지수 이동평균선 계산
    
    Args:
        data (numpy.ndarray): 가격 데이터
        period (int): 이동평균 기간
        
    Returns:
        numpy.ndarray: 지수 이동평균 데이터
    """
    if len(data) < period:
        return np.array([np.nan] * len(data))
        
    ema = np.zeros_like(data)
    ema[period-1] = np.mean(data[:period])
    
    k = 2 / (period + 1)
    
    for i in range(period, len(data)):
        ema[i] = data[i] * k + ema[i-1] * (1-k)
    
    for i in range(period-1):
        ema[i] = np.nan
    
    return ema

def bollinger_bands(data, period=20, std_dev=2):
    """
    볼린저 밴드 계산
    
    Args:
        data (numpy.ndarray): 가격 데이터
        period (int): 이동평균 기간
        std_dev (float): 표준편차 배수
        
    Returns:
        tuple: (중간선, 상단선, 하단선)
    """
    if len(data) < period:
        empty = np.array([np.nan] * len(data))
        return empty, empty, empty
        
    # 중간선 (이동평균)
    middle = moving_average(data, period)
    
    # 표준편차
    std = np.zeros_like(data)
    for i in range(len(data)):
        if i < period - 1:
            std[i] = np.nan
        else:
            std[i] = np.std(data[max(0, i-period+1):i+1])
    
    # 상단선, 하단선
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    
    return middle, upper, lower

def macd(data, fast_period=12, slow_period=26, signal_period=9):
    """
    MACD (Moving Average Convergence Divergence) 계산
    
    Args:
        data (numpy.ndarray): 가격 데이터
        fast_period (int): 빠른 EMA 기간
        slow_period (int): 느린 EMA 기간
        signal_period (int): 시그널 EMA 기간
        
    Returns:
        tuple: (MACD 라인, 시그널 라인, 히스토그램)
    """
    if len(data) < slow_period + signal_period:
        empty = np.array([np.nan] * len(data))
        return empty, empty, empty
        
    # 빠른 EMA, 느린 EMA
    fast_ema = exponential_moving_average(data, fast_period)
    slow_ema = exponential_moving_average(data, slow_period)
    
    # MACD 라인
    macd_line = fast_ema - slow_ema
    
    # 시그널 라인
    signal_line = exponential_moving_average(macd_line, signal_period)
    
    # 히스토그램
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def rsi(data, period=14):
    """
    RSI (Relative Strength Index) 계산
    
    Args:
        data (numpy.ndarray): 가격 데이터
        period (int): RSI 기간
        
    Returns:
        numpy.ndarray: RSI 데이터
    """
    if len(data) < period + 1:
        return np.array([np.nan] * len(data))
        
    # 가격 변화
    delta = np.zeros_like(data)
    delta[1:] = data[1:] - data[:-1]
    delta[0] = 0
    
    # 상승, 하락 구분
    gain = np.zeros_like(delta)
    loss = np.zeros_like(delta)
    
    gain[delta > 0] = delta[delta > 0]
    loss[delta < 0] = -delta[delta < 0]
    
    # 평균 상승, 평균 하락
    avg_gain = np.zeros_like(data)
    avg_loss = np.zeros_like(data)
    
    # 첫 번째 평균
    avg_gain[period] = np.mean(gain[1:period+1])
    avg_loss[period] = np.mean(loss[1:period+1])
    
    # 나머지 평균
    for i in range(period+1, len(data)):
        avg_gain[i] = (avg_gain[i-1] * (period-1) + gain[i]) / period
        avg_loss[i] = (avg_loss[i-1] * (period-1) + loss[i]) / period
    
    # RSI 계산
    rs = np.zeros_like(data)
    rsi_values = np.zeros_like(data)
    
    for i in range(period, len(data)):
        if avg_loss[i] == 0:
            rs[i] = 100
        else:
            rs[i] = avg_gain[i] / avg_loss[i]
        
        rsi_values[i] = 100 - (100 / (1 + rs[i]))
    
    # 기간 이전의 값은 NaN으로 설정
    for i in range(period):
        rsi_values[i] = np.nan
    
    return rsi_values

def stochastic(high_data, low_data, close_data, k_period=14, d_period=3):
    """
    스토캐스틱 계산
    
    Args:
        high_data (numpy.ndarray): 고가 데이터
        low_data (numpy.ndarray): 저가 데이터
        close_data (numpy.ndarray): 종가 데이터
        k_period (int): %K 기간
        d_period (int): %D 기간
        
    Returns:
        tuple: (%K, %D)
    """
    if len(close_data) < k_period + d_period:
        empty = np.array([np.nan] * len(close_data))
        return empty, empty
        
    # %K 계산
    k = np.zeros_like(close_data)
    
    for i in range(k_period-1, len(close_data)):
        high_max = np.max(high_data[i-k_period+1:i+1])
        low_min = np.min(low_data[i-k_period+1:i+1])
        
        if high_max == low_min:
            k[i] = 50
        else:
            k[i] = 100 * (close_data[i] - low_min) / (high_max - low_min)
    
    # 기간 이전의 값은 NaN으로 설정
    for i in range(k_period-1):
        k[i] = np.nan
    
    # %D 계산 (단순 이동평균)
    d = moving_average(k, d_period)
    
    return k, d

def ichimoku_cloud(high_data, low_data, close_data, tenkan_period=9, kijun_period=26, senkou_span_b_period=52, displacement=26):
    """
    일목균형표 계산
    
    Args:
        high_data (numpy.ndarray): 고가 데이터
        low_data (numpy.ndarray): 저가 데이터
        close_data (numpy.ndarray): 종가 데이터
        tenkan_period (int): 전환선 기간
        kijun_period (int): 기준선 기간
        senkou_span_b_period (int): 선행스팬 B 기간
        displacement (int): 이격 기간
        
    Returns:
        tuple: (전환선, 기준선, 선행스팬 A, 선행스팬 B, 후행스팬)
    """
    if len(close_data) < max(tenkan_period, kijun_period, senkou_span_b_period) + displacement:
        empty = np.array([np.nan] * len(close_data))
        return empty, empty, empty, empty, empty
        
    # 데이터 길이
    length = len(close_data)
    
    # 전환선 (Tenkan-sen)
    tenkan_sen = np.zeros_like(close_data)
    for i in range(tenkan_period-1, length):
        high_max = np.max(high_data[i-tenkan_period+1:i+1])
        low_min = np.min(low_data[i-tenkan_period+1:i+1])
        tenkan_sen[i] = (high_max + low_min) / 2
    
    # 기준선 (Kijun-sen)
    kijun_sen = np.zeros_like(close_data)
    for i in range(kijun_period-1, length):
        high_max = np.max(high_data[i-kijun_period+1:i+1])
        low_min = np.min(low_data[i-kijun_period+1:i+1])
        kijun_sen[i] = (high_max + low_min) / 2
    
    # 선행스팬 A (Senkou Span A)
    senkou_span_a = np.zeros_like(close_data)
    for i in range(kijun_period-1, length):
        if i + displacement < length:
            senkou_span_a[i+displacement] = (tenkan_sen[i] + kijun_sen[i]) / 2
    
    # 선행스팬 B (Senkou Span B)
    senkou_span_b = np.zeros_like(close_data)
    for i in range(senkou_span_b_period-1, length):
        if i + displacement < length:
            high_max = np.max(high_data[i-senkou_span_b_period+1:i+1])
            low_min = np.min(low_data[i-senkou_span_b_period+1:i+1])
            senkou_span_b[i+displacement] = (high_max + low_min) / 2
    
    # 후행스팬 (Chikou Span)
    chikou_span = np.zeros_like(close_data)
    for i in range(length):
        if i - displacement >= 0:
            chikou_span[i-displacement] = close_data[i]
    
    # 기간 이전의 값은 NaN으로 설정
    for i in range(tenkan_period-1):
        tenkan_sen[i] = np.nan
    
    for i in range(kijun_period-1):
        kijun_sen[i] = np.nan
    
    return tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span

def on_balance_volume(close_data, volume_data):
    """
    OBV (On Balance Volume) 계산
    
    Args:
        close_data (numpy.ndarray): 종가 데이터
        volume_data (numpy.ndarray): 거래량 데이터
        
    Returns:
        numpy.ndarray: OBV 데이터
    """
    if len(close_data) < 2:
        return np.array([np.nan] * len(close_data))
        
    obv = np.zeros_like(close_data)
    obv[0] = volume_data[0]
    
    for i in range(1, len(close_data)):
        if close_data[i] > close_data[i-1]:
            obv[i] = obv[i-1] + volume_data[i]
        elif close_data[i] < close_data[i-1]:
            obv[i] = obv[i-1] - volume_data[i]
        else:
            obv[i] = obv[i-1]
    
    return obv

def average_directional_index(high_data, low_data, close_data, period=14):
    """
    ADX (Average Directional Index) 계산
    
    Args:
        high_data (numpy.ndarray): 고가 데이터
        low_data (numpy.ndarray): 저가 데이터
        close_data (numpy.ndarray): 종가 데이터
        period (int): ADX 기간
        
    Returns:
        tuple: (ADX, +DI, -DI)
    """
    if len(close_data) < period * 2:
        empty = np.array([np.nan] * len(close_data))
        return empty, empty, empty
        
    # 데이터 길이
    length = len(close_data)
    
    # True Range (TR)
    tr = np.zeros_like(close_data)
    tr[0] = high_data[0] - low_data[0]
    
    for i in range(1, length):
        hl = high_data[i] - low_data[i]
        hc = abs(high_data[i] - close_data[i-1])
        lc = abs(low_data[i] - close_data[i-1])
        tr[i] = max(hl, hc, lc)
    
    # Directional Movement (DM)
    plus_dm = np.zeros_like(close_data)
    minus_dm = np.zeros_like(close_data)
    
    for i in range(1, length):
        up_move = high_data[i] - high_data[i-1]
        down_move = low_data[i-1] - low_data[i]
        
        if up_move > down_move and up_move > 0:
            plus_dm[i] = up_move
        else:
            plus_dm[i] = 0
            
        if down_move > up_move and down_move > 0:
            minus_dm[i] = down_move
        else:
            minus_dm[i] = 0
    
    # Smoothed TR and DM
    smoothed_tr = np.zeros_like(close_data)
    smoothed_plus_dm = np.zeros_like(close_data)
    smoothed_minus_dm = np.zeros_like(close_data)
    
    # 첫 번째 평균
    smoothed_tr[period] = np.sum(tr[1:period+1])
    smoothed_plus_dm[period] = np.sum(plus_dm[1:period+1])
    smoothed_minus_dm[period] = np.sum(minus_dm[1:period+1])
    
    # 나머지 평균
    for i in range(period+1, length):
        smoothed_tr[i] = smoothed_tr[i-1] - (smoothed_tr[i-1] / period) + tr[i]
        smoothed_plus_dm[i] = smoothed_plus_dm[i-1] - (smoothed_plus_dm[i-1] / period) + plus_dm[i]
        smoothed_minus_dm[i] = smoothed_minus_dm[i-1] - (smoothed_minus_dm[i-1] / period) + minus_dm[i]
    
    # Directional Indicators (DI)
    plus_di = np.zeros_like(close_data)
    minus_di = np.zeros_like(close_data)
    
    for i in range(period, length):
        if smoothed_tr[i] == 0:
            plus_di[i] = 0
            minus_di[i] = 0
        else:
            plus_di[i] = 100 * smoothed_plus_dm[i] / smoothed_tr[i]
            minus_di[i] = 100 * smoothed_minus_dm[i] / smoothed_tr[i]
    
    # Directional Index (DX)
    dx = np.zeros_like(close_data)
    
    for i in range(period, length):
        if plus_di[i] + minus_di[i] == 0:
            dx[i] = 0
        else:
            dx[i] = 100 * abs(plus_di[i] - minus_di[i]) / (plus_di[i] + minus_di[i])
    
    # Average Directional Index (ADX)
    adx = np.zeros_like(close_data)
    
    # 첫 번째 ADX
    adx[period*2-1] = np.mean(dx[period:period*2])
    
    # 나머지 ADX
    for i in range(period*2, length):
        adx[i] = (adx[i-1] * (period-1) + dx[i]) / period
    
    # 기간 이전의 값은 NaN으로 설정
    for i in range(period*2-1):
        adx[i] = np.nan
        
    for i in range(period):
        plus_di[i] = np.nan
        minus_di[i] = np.nan
    
    return adx, plus_di, minus_di

def parabolic_sar(high_data, low_data, close_data, af_start=0.02, af_increment=0.02, af_max=0.2):
    """
    Parabolic SAR 계산
    
    Args:
        high_data (numpy.ndarray): 고가 데이터
        low_data (numpy.ndarray): 저가 데이터
        close_data (numpy.ndarray): 종가 데이터
        af_start (float): 초기 가속 계수
        af_increment (float): 가속 계수 증가분
        af_max (float): 최대 가속 계수
        
    Returns:
        numpy.ndarray: Parabolic SAR 데이터
    """
    if len(close_data) < 2:
        return np.array([np.nan] * len(close_data))
        
    # 데이터 길이
    length = len(close_data)
    
    # Parabolic SAR
    sar = np.zeros_like(close_data)
    
    # 초기값 설정
    trend = 1  # 1: 상승, -1: 하락
    ep = high_data[0]  # Extreme Point
    af = af_start  # Acceleration Factor
    
    # 첫 번째 SAR
    sar[0] = low_data[0]
    
    for i in range(1, length):
        # 이전 SAR
        sar[i] = sar[i-1] + af * (ep - sar[i-1])
        
        # 추세 전환 확인
        if trend == 1:  # 상승 추세
            # SAR가 현재 또는 이전 저가보다 높으면 추세 전환
            if sar[i] > low_data[i] or sar[i] > low_data[i-1]:
                trend = -1
                sar[i] = max(high_data[i], high_data[i-1])
                ep = low_data[i]
                af = af_start
            else:
                # 상승 추세 유지
                if high_data[i] > ep:
                    ep = high_data[i]
                    af = min(af + af_increment, af_max)
        else:  # 하락 추세
            # SAR가 현재 또는 이전 고가보다 낮으면 추세 전환
            if sar[i] < high_data[i] or sar[i] < high_data[i-1]:
                trend = 1
                sar[i] = min(low_data[i], low_data[i-1])
                ep = high_data[i]
                af = af_start
            else:
                # 하락 추세 유지
                if low_data[i] < ep:
                    ep = low_data[i]
                    af = min(af + af_increment, af_max)
    
    return sar 