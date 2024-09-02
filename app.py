from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# 初始化 Line Bot API 和 Webhook Handler
line_bot_api = LineBotApi(os.getenv('line_bot_api'))
handler = WebhookHandler(os.getenv('handler'))

# 连接 MongoDB
client = MongoClient(os.getenv('mongo_uri'))
db = client['line_bot_db']  # 你可以设置数据库名称为 line_bot_db
collection = db['messages']  # 设置集合名称为 messages

# 监听所有来自 /callback 的 POST 请求
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 处理收到的消息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text
    
    # 将消息保存到 MongoDB
    record = {
        "user_id": user_id,
        "message": user_message
    }
    collection.insert_one(record)
    
    # 回应用户
    reply_message = "您的信息已保存！"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
