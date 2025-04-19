from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import requests
import datetime
import yfinance as yf
from ta.momentum import StochasticOscillator  # 用 ta 套件替代 talib

app = Flask(__name__)

# 環境變數
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))
USER_ID = os.getenv("USER_ID")

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    message_text = event.message.text
    reply_text = f"你說的是：{message_text}\n你的 LINE User ID 是：\n{user_id}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# 替代 talib 的 KD 計算函式
def fetch_kd(stock_id):
    try:
        df = yf.download(stock_id, period="3mo", interval="1d")
        df.dropna(inplace=True)

        stoch = StochasticOscillator(high=df['High'], low=df['Low'], close=df['Close'], window=9, smooth_window=3)
        df['K'] = stoch.stoch()
        df['D'] = stoch.stoch_signal()

        if df['K'].isna().all() or df['D'].isna().all():
            raise ValueError("KD 資料為空")

        return df['K'].iloc[-1], df['D'].iloc[-1]
    except Exception as e:
        print(f"[ERROR] 抓取 KD 失敗：{e}")
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

@app.route("/test_kd", methods=["GET"])
def test_kd():
    notify_kd()
    return "KD 通知測試已發送"

if __name__ == "__main__":
    app.run()
