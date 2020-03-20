from flask import Flask, request, abort, send_file
import os

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, BeaconEvent,
)

app = Flask(__name__)
statusDict  = {}
status = 0

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

@app.route("/")
def hello_world():
    return "hello world!"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
    event.reply_token,[
        TextSendMessage(text=event.message.text),
    ])

@handler.add(BeaconEvent)
def handle_beacon(event):
    print(event)

    # LINEユーザー名の取得
    user_id = event.source.user_id
    try:
        user_name = line_bot_api.get_profile(user_id).display_name
    except LineBotApiError as e:
        user_name = "Unknown"

    line_bot_api.reply_message(
        event.reply_token,[
            TextSendMessage(text='beaconを検出しました. event.type={}, hwid={}, device_message(hex string)={}, user_name={}'.format(event.beacon.type, event.beacon.hwid, event.beacon.dm, user_name)),
        ])

if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
