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

from modules.reply import faq,menu
from modules.currency import get_exchange_table

import os

table=get_exchange_table()
print("table",table)

app = Flask(__name__)

channel_serect=os.getenv("CHANNEL_SECRET")
channel_access_token=os.getenv("CHANNEL_ACCESS_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_serect)

@app.route("/", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    print("#" * 40)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    print("#" * 40)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
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
        # 使用 OpenAI API 進行文字生成
        openai_response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=user_msg,
            max_tokens=50
        )
        bot_msg = TextSendMessage(text=openai_response.choices[0].text)


        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    bot_msg
                ]
            )
        )

@handler.add(MessageEvent, message=StickerMessageContent)
def handle_sticker_message(event):
    with ApiClient(configuration) as api_client:
        # 當使用者傳入貼圖時
        line_bot_api = MessagingApi(api_client)
        sticker_id = event.message.sticker_id
        package_id = event.message.package_id
        keywords = ", ".join(event.message.keywords)
        # 可以使用的貼圖清單
        # https://developers.line.biz/en/docs/messaging-api/sticker-list/
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    StickerMessage(package_id="6325", sticker_id="10979904"),
                    TextMessage(text=f"You just sent a sticker. Here is the information of the sticker:"),
                    TextMessage(text=f"package_id is {package_id}, sticker_id is {sticker_id}."),
                    TextMessage(text=f"The keywords are {keywords}."),
                ]
            )
        )

@handler.add(MessageEvent, message=LocationMessageContent)
def handle_location_message(event):
    with ApiClient(configuration) as api_client:
        # 當使用者傳入地理位置時
        line_bot_api = MessagingApi(api_client)
        latitude = event.message.latitude
        longitude = event.message.longitude
        address = event.message.address
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text=f"You just sent a location message."),
                    TextMessage(text=f"The latitude is {latitude}."),
                    TextMessage(text=f"The longitude is {longitude}."),
                    TextMessage(text=f"The address is {address}."),
                    LocationMessage(title="Here is the location you sent.", address=address, latitude=latitude, longitude=longitude)
                ]
            )
        )

# 如果應用程式被執行執行
if __name__ == "__main__":
    print("[伺服器應用程式開始運行]")
    # 取得遠端環境使用的連接端口，若是在本機端測試則預設開啟於port=5001
    port = int(os.environ.get('PORT', 5001))
    print(f"[Flask即將運行於連接端口:{port}]")
    print(f"若在本地測試請輸入指令開啟測試通道: ./ngrok http {port} ")
    # 啟動應用程式
    # 本機測試使用127.0.0.1, debug=True
    # Heroku部署使用 0.0.0.0
    app.run(host="0.0.0.0", port=port)
