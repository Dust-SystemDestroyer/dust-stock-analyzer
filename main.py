import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import os

# 1. 이메일 발송 함수
def send_mail(content):
    # [수정 포인트] 본인의 정보로 채워줘
    send_email = "gh3gus1205@gmail.com" 
    recv_email = "gh3gus1205@gmail.com" 
    password = os.getenv('GMAIL_PW') # <--- 아까 성공했던 그 비번!

    smtp_name = "smtp.gmail.com"
    smtp_port = 587
    msg = MIMEMultipart()
    msg['Subject'] = f"🚀 [Dust AI v2] 데이터 지표 강화 주식 리포트"
    msg['From'] = send_email
    msg['To'] = recv_email
    msg.attach(MIMEText(content, 'plain'))

    try:
        s = smtplib.SMTP(smtp_name, smtp_port)
        s.starttls()
        s.login(send_email, password)
        s.sendmail(send_email, recv_email, msg.as_string())
        s.close()
        return "이메일 발송 성공!"
    except Exception as e:
        return f"이메일 발송 실패: {e}"

# 2. 분석 및 리포트 생성 함수
def run_analysis():
    # 분석할 종목 (원하는 대로 추가 가능)
    # 미국 유망 기업 10개 + 한국 유망 기업 10개 (총 20개)
    tickers = [
    # --- 미국 (US) ---
    'AAPL',  # 애플 (IT/하드웨어)
    'TSLA',  # 테슬라 (전기차/AI)
    'NVDA',  # 엔비디아 (반도체/AI)
    'MSFT',  # 마이크로소프트 (클라우드/AI)
    'META',  # 메타 (소셜/광고)
    'O',     # 리얼티 인컴 (부동산 리츠 - 더스트의 전공 분야!)
    'JPM',   # JP모건 (금융 - 회계적 관점에서 중요)
    'GOOGL', # 알파벳 (검색/AI)
    'AMZN',  # 아마존 (이커머스/클라우드)
    'SCHD',  # Schwab US Dividend Equity (배당 성장 ETF)

    # --- 한국 (KRX) ---
    '005930', # 삼성전자 (반도체)
    '000660', # SK하이닉스 (반도체)
    '035420', # NAVER (플랫폼)
    '035720', # 카카오 (플랫폼)
    '005380', # 현대차 (자동차)
    '207940', # 삼성바이오로직스 (바이오)
    '068270', # 셀트리온 (바이오)
    '105560', # KB금융 (금융)
    '055550', # 신한지주 (금융)
    '402340'  # SK스퀘어 (투자/ICT)
]
    report_content = "안녕하세요 더스트, 데이터 지표(MA5, 거래량)가 강화된 AI 분석 결과입니다.\n"
    report_content += "="*45 + "\n"
    
    found_recommendation = False

    for t in tickers:
        try:
            # 데이터 로드 (최근 2년치)
            df = fdr.DataReader(t, '2023-01-01')
            
            # [데이터 질 향상] 이동평균선 추가
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df = df.dropna()

            if len(df) < 50: continue

            # 학습 데이터 준비 (종가, 5일이평선, 거래량)
            x, y = [], []
            process_df = df.tail(300) # 최근 300일 데이터만 사용 (속도 향상)
            for i in range(len(process_df) - 1):
                features = [
                    process_df.iloc[i]['Close'], 
                    process_df.iloc[i]['MA5'], 
                    process_df.iloc[i]['Volume']
                ]
                x.append(features)
                y.append(process_df.iloc[i+1]['Close'])

            # 데이터 분할 및 학습
            train_x, test_x, train_y, test_y = train_test_split(x, y, test_size=0.2, random_state=42)
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(train_x, train_y)
            score = model.score(test_x, test_y)

            # 내일 가격 예측
            today_features = [[
                process_df.iloc[-1]['Close'], 
                process_df.iloc[-1]['MA5'], 
                process_df.iloc[-1]['Volume']
            ]]
            pred = model.predict(today_features)[0]
            today_price = process_df.iloc[-1]['Close']
            next_date = (process_df.index[-1] + pd.Timedelta(days=1)).strftime('%Y-%m-%d')

            # 상승 예측 시에만 리포트 기록
            if pred > today_price:
                found_recommendation = True
                change_rate = ((pred - today_price) / today_price) * 100
                report_content += f"[{next_date}] {t} 추천!\n"
                report_content += f" - 현재가: ${today_price:,.2f}\n"
                report_content += f" - 예측가: ${pred:,.2f} ({change_rate:+.2f}%)\n"
                report_content += f" - 모델 정확도(R²): {score:.2f}\n"
                report_content += "-"*35 + "\n"
        
        except Exception as e:
            print(f"{t} 분석 중 오류 발생: {e}")

    if not found_recommendation:
        report_content += "오늘은 상승이 예측되는 종목이 없습니다.\n"
    
    report_content += "\n본 자료는 AI 예측치이며 투자 판단의 책임은 본인에게 있습니다."
    
    # 최종 메일 발송
    print("분석 완료! 메일을 전송합니다...")
    result = send_mail(report_content)
    print(result)

# 🚀 [핵심] 여기서 실제로 시동을 건다!
if __name__ == "__main__":

    run_analysis()

