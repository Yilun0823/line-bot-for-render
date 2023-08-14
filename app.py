from flask import Flask, request, abort
from linebot import (
    WebhookHandler, LineBotApi
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, StickerMessage, LocationMessage,
    TextSendMessage, StickerSendMessage, LocationSendMessage,
)
import openai
import os

# 請確保已經設定好 OPENAI_API_KEY
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_exchange_table():
    # 在這裡實現您的取得匯率資料的邏輯
    # 返回匯率資料表格
    exchange_table = {
        "USD": {"buy": 28.5, "sell": 28.8},
        "JPY": {"buy": 0.26, "sell": 0.28},
        # ...
    }
    return exchange_table

table = get_exchange_table()

app = Flask(__name__)

channel_secret = os.getenv("CHANNEL_SECRET")
channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text
    bot_msg = TextSendMessage(text=f"Hello 你剛才說的是: {user_msg}")

    if user_msg in table:
        buy = table[user_msg]["buy"]
        sell = table[user_msg]["sell"]
        bot_msg = TextSendMessage(text=f"{user_msg}\n買價:{buy}\n賣價:{sell}")
    elif user_msg.lower() in ["menu", "選單", "home", "主選單"]:
        bot_msg = TextSendMessage(text="這是選單回應")
    else:
        # 使用 OpenAI API 進行對話生成
        openai_response = openai.Completion.create(
            engine="davinci",  # 使用適合的引擎
            prompt=user_msg,
            max_tokens=50
        )
        bot_msg = TextSendMessage(text=openai_response.choices[0].text)
    
    line_bot_api.reply_message(event.reply_token, bot_msg)

if __name__ == "__main__":
    app.run(host="0.0.0.0")
