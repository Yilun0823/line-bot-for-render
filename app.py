# 運行以下程式需安裝模組: line-bot-sdk, flask, pyquery
# 安裝方式，輸入指令:
# pip install line-bot-sdk flask pyquery
# 運行應用程式:
# python app.py
from flask import Flask, request, abort
from linebot import (
    LineBotApi,
    WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    StickerMessage,
    LocationMessage,
)

from modules.reply import faq, menu
from modules.currency import get_exchange_table

import os
import openai

table = get_exchange_table()
print("table", table)

app = Flask(__name__)

channel_secret = os.getenv("CHANNEL_SECRET")
channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print("#" * 40)
    app.logger.info("Request body: " + body)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("無效的簽名。請檢查您的通道訪問權杖/通道秘密。")
        abort(400)
    print("#" * 40)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text

    if user_msg.lower() in ["menu", "選單", "home", "主選單"]:
        bot_msg = menu
    elif user_msg in table:
        buy = table[user_msg]["buy"]
        sell = table[user_msg]["sell"]
        bot_msg = TextSendMessage(text=f"{user_msg}\n買價:{buy}\n賣價:{sell}")
    else:
        openai_response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=user_msg,
            max_tokens=50
        )
        bot_msg = TextSendMessage(text=openai_response.choices[0].text)

    line_bot_api.reply_message(
        event.reply_token,
        bot_msg
    )

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    sticker_id = event.message.sticker_id
    package_id = event.message.package_id
    keywords = ", ".join(event.message.keywords)
    
    line_bot_api.reply_message(
        event.reply_token,
        [
            StickerMessage(package_id="6325", sticker_id="10979904"),
            TextSendMessage(text="您剛剛傳了一張貼圖。以下是該貼圖的相關信息："),
            TextSendMessage(text=f"package_id 是 {package_id}，sticker_id 是 {sticker_id}。"),
            TextSendMessage(text=f"關鍵詞為：{keywords}。"),
        ]
    )

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    latitude = event.message.latitude
    longitude = event.message.longitude
    address = event.message.address
    
    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text="您剛剛傳了一個位置訊息。"),
            TextSendMessage(text=f"緯度：{latitude}。"),
            TextSendMessage(text=f"經度：{longitude}。"),
            TextSendMessage(text=f"地址：{address}。"),
            LocationMessage(title="這是您傳送的位置。", address=address, latitude=latitude, longitude=longitude)
        ]
    )

if __name__ == "__main__":
    print("[伺服器應用程式開始運行]")
    port = int(os.environ.get('PORT', 5001))
    print(f"[Flask即將運行於連接端口：{port}]")
    print(f"若在本地測試，請執行命令以開啟測試隧道：./ngrok http {port}")
    app.run(host="0.0.0.0", port=port)
