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

# 環境変数取得
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

    # LINEユーザー名の取得
    user_id = event.source.user_id
    try:
        user_name = line_bot_api.get_profile(user_id).display_name
    except LineBotApiError as e:
        user_name = "Unknown"

    slack_info = slackweb.Slack(url=WEB_HOOK_LINKS)

    # 先生を召喚する
    if "先生" in event.message.text or "話" in event.message.text or "呼" in event.message.text or "召喚" in event.message.text:
        teacher_name = ""
        mention = "!channel"
        # どの先生を呼び出すのか特定する
        if "でんでん" in event.message.text or "でせ" in event.message.text or "田重田" in event.message.text or "たじゅうた" in event.message.text:
            teacher_name = "でんでん"
            mention = "@tajuta"
        elif "まっちゃん" in event.message.text or "ませ" in event.message.text or "松尾" in event.message.text or "まつお" in event.message.text:
            teacher_name = "まっちゃん"
            mention = "@k.matsuo"
        elif "つばさ" in event.message.text or "つせ" in event.message.text:
            teacher_name = "つばさ"
            mention = "@tu"
        elif "うちだ" in event.message.text or "うせ" in event.message.text or "内田" in event.message.text or "ぷーさん" in event.message.text:
            teacher_name = "うちだ"
            mention = "@susumu.uchida"
        elif "さめ" in event.message.text or "シャーク" in event.message.text or "鮫" in event.message.text:
            teacher_name = "さめしま"
            mention = "@kana.sameshima"
        elif "よっしー" in event.message.text or "吉田" in event.message.text or "よしだ" in event.message.text:
            teacher_name = "よしだ"
            mention = "@moe.yoshida"
        elif "うえお" in event.message.text or "上尾" in event.message.text or "ゆかもん" in event.message.text:
            teacher_name = "うえお"
            mention = "@yuka.ueo"
        elif "おかだ" in event.message.text or "岡田" in event.message.text or "おかT" in event.message.text or "だー" in event.message.text:
            teacher_name = "おかだ"
            mention = "@kouta.okada"
        elif "しみず" in event.message.text or "清水" in event.message.text or "たろう" in event.message.text:
            teacher_name = "しみず"
            mention = "@tarou.shimizu"
        elif "よしも" in event.message.text or "吉本" in event.message.text or "ちか" in event.message.text:
            teacher_name = "よしもと"
            mention = "@chika.yoshimoto"

        line_bot_api.reply_message(
        event.reply_token,[
            TextSendMessage(text=teacher_name + "先生を呼び出しているのでちょっとまっててね。（すぐにお返事できない場合があるよ）"),
        ])
        # Slackにメッセージを送信
        send_msg = "[{user_name}] {message}\n".format(user_name=user_name, message=event.message.text) \
                + "<{mention}> {user_name}さんが{teacher_name}先生と話したがっています。LINE Official Accountの設定をチャットモードに切り替えて対応してください。\n".format(mention=mention, user_name=user_name, teacher_name=teacher_name) \
                + "`※対応が終わったらbotモードに切り替えて、Webhookの設定を必ずオンにしてください。`"
        slack_info.notify(text=send_msg)
        # 先生を個別に呼び出す場合はダイレクトメッセージも送る
        if not teacher_name == "":
            slack_info.notify(text=send_msg, channel="#board-of-directors")

    # Talk APIを使って会話する
    else:
        r = requests.post(TALK_API_URL,{'apikey':TALK_API_KEY,'query':event.message.text})
        data = json.loads(r.text)
        if data['status'] == 0:
            t = data['results']
            ret = t[0]['reply']
        else:
            ret = '・・・・・・・・・'

        line_bot_api.reply_message(
        event.reply_token,[
            TextSendMessage(text=ret),
        ])

        # botとの会話内容をSlackに連携
        if TALK_PUSH_FLAG == "true":
            send_msg = "[{user_name}] {message}\n".format(user_name=user_name, message=event.message.text) \
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
