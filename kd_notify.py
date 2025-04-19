import os
import yfinance as yf
import talib
from linebot import LineBotApi
from linebot.models import TextSendMessage

line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
USER_ID = os.getenv("USER_ID")

def fetch_kd(stock_id):
    df = yf.download(stock_id, period="3mo", interval="1d")
    df.dropna(inplace=True)
    low = df["Low"]
    high = df["High"]
    close = df["Close"]
    k, d = talib.STOCH(high, low, close)
    return k[-1], d[-1]

def notify_kd():
    for stock_id, name in [("0050.TW", "0050"), ("0056.TW", "0056")]:
        try:
            k, d = fetch_kd(stock_id)
            if k < 20 or k > 80:
                status = "超賣" if k < 20 else "過熱"
                message = f"{name} KD 指標提醒：\nK={k:.2f}, D={d:.2f}，已{status}區，請注意。"
                line_bot_api.push_message(USER_ID, TextSendMessage(text=message))
        except Exception as e:
            print(f"錯誤：{e}")

if __name__ == "__main__":
    notify_kd()
