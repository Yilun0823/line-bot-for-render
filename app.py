# 運行以下程式需安裝模組: line-bot-sdk, flask, pyquery
# 安裝方式，輸入指令:
# pip install line-bot-sdk flask pyquery
# 運行應用程式:
# python app.py
from flask import Flask, request, abort

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    StickerMessage,
    LocationMessage,
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    StickerMessageContent,
    LocationMessageContent,
)

from modules.reply import faq, menu
from modules.currency import get_exchange_table

import os
import openai

# 獲取貨幣匯率表
table = get_exchange_table()
print("table", table)

# 創建 Flask 應用
app = Flask(__name__)

line_bot_api = None
handler = None
configuration = None

# 設置 Line Bot 配置
channel_secret = os.getenv("CHANNEL_SECRET")
channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")

# 設置 OpenAI API 密鑰
openai.api_key = "OPENAI_API_KEY"

# 創建 Configuration 對象
configuration = Configuration(access_token=channel_access_token)

# 創建 WebhookHandler 對象
handler = WebhookHandler(channel_secret)

@app.route("/", methods=['POST'])
def callback():
    # 獲取 X-Line-Signature 頭部值
    signature = request.headers['X-Line-Signature']
    # 獲取請求體作為文本
    body = request.get_data(as_text=True)
    print("#" * 40)
    app.logger.info("Request body: " + body)
    # 處理 Webhook 請求體
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    print("#" * 40)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        # 當使用者傳入文字訊息時
        line_bot_api = MessagingApi(api_client)
        user_msg = event.message.text

        if user_msg in faq:
            bot_msg = faq[user_msg]
        elif user_msg.lower() in ["menu","選單","home","主選單"]:
            bot_msg = menu
        elif user_msg in table:
            buy = table[user_msg]["buy"]
            sell = table[user_msg]["sell"]
            bot_msg = TextMessage(text=f"{user_msg}\n買價:{buy}\n賣價:{sell}")

        # 如果沒有匹配的回答，使用 OpenAI GPT-3.5 生成回答
        if bot_msg is None:
            generated_text = generate_text(user_msg)
            bot_msg = TextMessage(text=generated_text)

        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    bot_msg
                ]
            )
        )

# 使用 OpenAI GPT-3.5 模型生成回答的函數
def generate_openai_response(user_input):
    response = openai.Completion.create(
        engine="davinci",  # 選擇 GPT-3 的引擎，可以嘗試 curie 或其他
        prompt=user_input,  # 輸入提示
        max_tokens=50  # 最大生成的標記數
    )
    return response.choices[0].text.strip()

def generate_text(prompt):
    try:
        response = openai.Completion.create(
            engine="davinci",  # 使用 GPT-3.5 的 davinci 引擎
            prompt=prompt,
            max_tokens=50  # 生成的最大標記數
        )
        generated_text = response.choices[0].text.strip()
        return generated_text
    except Exception as e:
        return "抱歉，出了點問題，無法生成回答。"
if __name__ == "__main__":
    print("[服務器應用程序開始運行]")
    # 獲取遠程環境使用的連接端口，若在本地測試則默認開啟於 port=5001
    port = int(os.environ.get('PORT', 5001))
    print(f"[Flask即將運行於連接端口:{port}]")
    print(f"若在本地測試請輸入指令開啟測試通道: ./ngrok http {port} ")
    # 啟動應用程序
    # 本地測試使用 127.0.0.1，debug=True
    # Heroku 部署使用 0.0.0.0
    app.run(host="0.0.0.0", port=port)
