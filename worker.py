import time
import os
import yfinance as yf
import talib
from linebot import LineBotApi
from linebot.models import TextSendMessage

line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
USER_ID = os.getenv("USER_ID")

def fetch_kd(stock_id):
    try:
        df = yf.download(stock_id, period="3mo", interval="1d")
        df.dropna(inplace=True)
        low = df["Low"]
        high = df["High"]
        close = df["Close"]
        k, d = talib.STOCH(high, low, close)
        return k[-1], d[-1]
    except Exception as e:
        print(f"[ERROR] KD 計算失敗：{e}")
        return None

def notify_kd():
    for stock_id, name in [("0050.TW", "0050"), ("0056.TW", "0056")]:
        result = fetch_kd(stock_id)
        print(f"[DEBUG] {name} KD 結果：{result}")
        if result:
            k, d = result
            if k < 20 or k > 80:
                status = "超賣" if k < 20 else "過熱"
                message = f"{name} KD 指標提醒：\nK={k:.2f}, D={d:.2f}，已{status}區，請注意。"
                try:
                    print(f"[DEBUG] 發送 LINE 訊息：{message}")
                    line_bot_api.push_message(USER_ID, TextSendMessage(text=message))
                except Exception as e:
                    print(f"[ERROR] 發送失敗：{e}")

# 每天固定時間執行（例如每 86400 秒）
while True:
    now = time.localtime()
    if now.tm_hour == 8 and now.tm_min == 0:  # 每天早上 8:00 通知
        print("[DEBUG] 執行每日 KD 通知")
        notify_kd()
        time.sleep(60)  # 避免重複發送
    time.sleep(30)
