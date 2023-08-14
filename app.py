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
print("table", table)

app = Flask(__name__)

channel_secret = os.getenv("CHANNEL_SECRET")
channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")

configuration = Configuration(access_token=channel_access_token)
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

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        user_msg = event.message.text
        bot_msg = TextMessage(text=f"Hello 你剛才說的是: {user_msg}")

        if user_msg in table:
            buy = table[user_msg]["buy"]
            sell = table[user_msg]["sell"]
            bot_msg = TextMessage(text=f"{user_msg}\n買價:{buy}\n賣價:{sell}")
        elif user_msg.lower() in ["menu", "選單", "home", "主選單"]:
            bot_msg = TextMessage(text="這是選單回應")
        else:
            # 使用 OpenAI API 進行對話生成
            openai_response = openai.Completion.create(
                engine="davinci",  # 使用適合的引擎
                prompt=user_msg,
                max_tokens=50
            )
            bot_msg = TextMessage(text=openai_response.choices[0].text)
    
        line_bot_api = MessagingApi(api_client)
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
        line_bot_api = MessagingApi(api_client)
        sticker_id = event.message.sticker_id
        package_id = event.message.package_id
        keywords = ", ".join(event.message.keywords)
        
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    StickerMessage(package_id="6325", sticker_id="10979904"),
                    TextMessage(text="You just sent a sticker. Here is the information of the sticker:"),
                    TextMessage(text=f"package_id is {package_id}, sticker_id is {sticker_id}."),
                    TextMessage(text=f"The keywords are {keywords}."),
                ]
            )
        )

@handler.add(MessageEvent, message=LocationMessageContent)
def handle_location_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        latitude = event.message.latitude
        longitude = event.message.longitude
        address = event.message.address
        
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text="You just sent a location message."),
                    TextMessage(text=f"The latitude is {latitude}."),
                    TextMessage(text=f"The longitude is {longitude}."),
                    TextMessage(text=f"The address is {address}."),
                    LocationMessage(title="Here is the location you sent.", address=address, latitude=latitude, longitude=longitude)
                ]
            )
        )

if __name__ == "__main__":
    print("[Server Application Starts]")
    port = int(os.environ.get('PORT', 5001))
    print(f"[Flask will run on port: {port}]")
    print(f"If testing locally, run the following command to open a test tunnel: ./ngrok http {port}")
    app.run(host="0.0.0.0", port=port)
