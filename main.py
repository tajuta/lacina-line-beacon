from flask import Flask, request, abort, send_file
import os
import slackweb
import requests
import json

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
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
WEB_HOOK_LINKS = os.environ["SLACK_WEB_HOOKS_URL"]
BOT_OAUTH = os.environ["SLACK_BOT_OAUTH"]

TALK_API_KEY =  os.environ["A3RT_API_KEY"]
TALK_API_URL = 'https://api.a3rt.recruit-tech.co.jp/talk/v1/smalltalk'
TALK_PUSH_FLAG = os.environ["LINE_TO_SLACK"]

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

    # Talk APIを使って会話する
    r = requests.post(TALK_API_URL,{'apikey':TALK_API_KEY,'query':event.message.text})
    data = json.loads(r.text)
    if data['status'] == 0:
        t = data['results']
        ret = t[0]['reply']
    else:
        ret = '・・・・・・・・・'

    # LINEユーザーに返答する
    line_bot_api.reply_message(
    event.reply_token,[
        TextSendMessage(text=ret),
    ])

    # botとの会話内容をSlackに連携
    if TALK_PUSH_FLAG == "true":
        # LINEユーザー名の取得
        user_id = event.source.user_id
        try:
            user_name = line_bot_api.get_profile(user_id).display_name
        except LineBotApiError as e:
            user_name = "Unknown"

        msg_type = "個別"
        room_id = "unknown"
        if event.source.type == "group":
            msg_type = "グループ"
            room_id = event.source.group_id

        slack_info = slackweb.Slack(url=WEB_HOOK_LINKS)

        send_msg = "[{user_name}]({msg_type})({room_id}) {message}\n".format(user_name=user_name, msg_type=msg_type, room_id=room_id, message=event.message.text) \
                    + "[みまもりラシーナ] {ret}\n".format(ret=ret)

        # メッセージの送信
        slack_info.notify(text=send_msg)

@handler.add(BeaconEvent)
def handle_beacon(event):
    print(event)

    # LINEユーザー名の取得
    user_id = event.source.user_id
    try:
        user_name = line_bot_api.get_profile(user_id).display_name
    except LineBotApiError as e:
        user_name = "Unknown"

    #line_bot_api.reply_message(
    #    event.reply_token,[
    #        TextSendMessage(text='beaconを検出しました. event.type={}, hwid={}, device_message(hex string)={}, user_name={}'.format(event.beacon.type, event.beacon.hwid, event.beacon.dm, user_name)),
    #    ])

    slack_info = slackweb.Slack(url=WEB_HOOK_LINKS)

    # slack側に投稿するメッセージの加工
    if event.beacon.type == "enter":
        send_msg = "{user_name}さんが入室しました。({user_id})\n".format(user_name=user_name,user_id=user_id)
    elif event.beacon.type == "leave":
        send_msg = "{user_name}さんが退室しました。({user_id})\n".format(user_name=user_name,user_id=user_id)

    # メッセージの送信
    slack_info.notify(text=send_msg)

if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
