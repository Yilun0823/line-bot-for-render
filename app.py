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

from modules.currency import get_exchange_table

import os
import openai

# 請確保您的 OpenAI API 金鑰正確設定在環境變數 OPENAI_API_KEY 中
openai.api_key = os.getenv("OPENAI_API_KEY")

table = get_exchange_table()
print("table", table)

app = Flask(__name__)

channel_secret = os.getenv("CHANNEL_SECRET")
channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")

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
        bot_msg = TextSendMessage(text="這是選單的內容。")  # 修改成您想要的選單內容
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

# 下面是處理貼圖和位置訊息的函數，您可以根據需求進行修改，如果不需要可以保留空白

if __name__ == "__main__":
    print("[伺服器應用程式開始運行]")
    port = int(os.environ.get('PORT', 5001))
    print(f"[Flask即將運行於連接端口：{port}]")
    print(f"若在本地測試，請執行命令以開啟測試隧道：./ngrok http {port}")
    app.run(host="0.0.0.0", port=port)
