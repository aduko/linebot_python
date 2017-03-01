
#line bot

from __future__ import unicode_literals

import errno
import os
import sys
import tempfile
from argparse import ArgumentParser

from flask.ext.sqlalchemy import SQLAlchemy

from flask import Flask, request, abort, render_template, redirect, url_for

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageTemplateAction,
    ButtonsTemplate, URITemplateAction, PostbackTemplateAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent
)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]

db = SQLAlchemy(app)

# モデル作成
class User(db.Model):
    #id           = db.Column(db.Integer, primary_key=True)
    u_id      = db.Column(db.String(80), primary_key=True)
    u_name    = db.Column(db.String(80), unique=True)
    u_status  = db.Column(db.String(80))
    u_img_uri = db.Column(db.String(80))

    def __init__(self, u_id, u_name, u_status):
        self.u_id      = u_id
        self.u_name    = u_name
        self.u_status  = u_status
        # 0 = inital
        # 1 = グループを作る
        # 2 = 予定を立てる
        #self.u_img_uri = u_img_uri

    def __repr__(self):
        return '<User %r>' % self.u_name

class Groups(db.Model):
    g_id   = db.Column(db.Integer, primary_key=True)
    g_name = db.Column(db.String(80))

    #def __init__(self, g_id, g_name):
        #self.g_name = g_name
        #self.g_id   = g_id

    def __repr__(self):
        return '<Group name %r>' % self.group_name

class Group_user(db.Model):
    guid  = db.Column(db.Integer,primary_key=True )
    u_id  = db.Column(db.String,db.ForeignKey('user.u_id'))
    g_id  = db.Column(db.Integer,db.ForeignKey('groups.g_id'))
    admin = db.Column(db.Boolean)

    #def __init_(self, guid, u_id, g_id, admin):
    #    self.guid = guid
    #    self.u_id = u_id
    #    self.g_id = g_id
    #    self.admin = admin

class e_ans(db.Model):
    ans_id = db.Column(db.Integer, primary_key=True)
    u_id   = db.Column(db.String, db.ForeignKey('user.u_id'))
    e_id   = db.Column(db.Integer, db.ForeignKey('e_req.e_id'))
    ans1   = db.Column(db.String(80))
    ans2   = db.Column(db.String(80))
    ans3   = db.Column(db.String(80))
    ans4   = db.Column(db.String(80))
    ans5   = db.Column(db.String(80))

    def __init_(self, ans_id, u_id, e_id, ans1, ans2, ans3, ans4, ans5):
        self.ans_id = ans_id
        self.u_id   = u_id
        self.e_id   = e_id
        self.ans1   = ans1
        self.ans2   = ans2
        self.ans3   = ans3
        self.ans4   = ans4
        self.ans5   = ans5

class e_req(db.Model):
    e_id    = db.Column(db.Integer, primary_key=True)
    e_title = db.Column(db.String(80))
    e_date  = db.Column(db.DateTime)
    r_date  = db.Column(db.DateTime)
    t_date  = db.Column(db.DateTime)
    # type = day, week, mouth
    type    = db.Column(db.String(80))
    qes1    = db.Column(db.String(80))
    qes2    = db.Column(db.String(80))
    qes3    = db.Column(db.String(80))
    qes4    = db.Column(db.String(80))
    qes5    = db.Column(db.String(80))

    def __init__(self, e_id, e_title, e_date, r_date, t_date, type, qes1, qes2, qes3, qes4, qes5):
        self.e_id   = e_id
        self.e_title = e_title
        self.e_date = e_date
        self.r_date = r_date
        self.t_date = t_date
        self.type   = type
        self.qes1   = qes1
        self.qes2   = qes2
        self.qes3   = qes3
        self.qes4   = qes4
        self.qes5   = qes5
        
# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

# function for create tmp dir for download content
def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise


@app.route('/')
def index():
    title = "ようこそ"
    message = "test"
    # index.html をレンダリングする
    return render_template('index.html',
                           message=message, title=title)

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

@handler.add(FollowEvent)
def handle_follow(event):
    if isinstance(event.source, SourceUser):
        profile = line_bot_api.get_profile(event.source.user_id)
        l_name    = profile.display_name
        l_user_id = profile.user_id
        
        # user_idが未登録ならユーザー追加
        if not db.session.query(User).filter(User.u_id == l_user_id).count():
            reg = User(l_user_id, l_name, "0", "")
            db.session.add(reg)
            db.session.commit()
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text='初めまして、'+profile.display_name+'さん。まずは使い方を確認してね。'))
        else:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text='こんにちは、'+profile.display_name+'さん。まずは使い方を確認してね。'))

@handler.add(UnfollowEvent)
def handle_unfollow():
    app.logger.info("また、お会いしましょう！")


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    if text == 'profile':
        if isinstance(event.source, SourceUser):
            profile = line_bot_api.get_profile(event.source.user_id)
            #print(profile)
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(
                        text='Display name: ' + profile.display_name
                    ),
                    TextSendMessage(
                        #text='Status message: ' + profile.status_message
                        text='Status message: ' + profile.user_id
                    )
                ]
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text="Bot can't use profile API without user ID"))
    elif text == 'bye':
        if isinstance(event.source, SourceGroup):
            line_bot_api.reply_message(
                event.reply_token, TextMessage(text='Leaving group'))
            line_bot_api.leave_group(event.source.group_id)
        elif isinstance(event.source, SourceRoom):
            line_bot_api.reply_message(
                event.reply_token, TextMessage(text='Leaving group'))
            line_bot_api.leave_room(event.source.room_id)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text="Bot can't leave from 1:1 chat"))
    elif text == 'confirm':
        confirm_template = ConfirmTemplate(text='Do it?', actions=[
            MessageTemplateAction(label='Yes', text='Yes!'),
            MessageTemplateAction(label='No', text='No!'),
        ])
        template_message = TemplateSendMessage(
            alt_text='Confirm alt text', template=confirm_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif text == 'buttons':
        buttons_template = ButtonsTemplate(
            title='My buttons sample', text='Hello, my buttons', actions=[
                URITemplateAction(
                    label='Go to line.me', uri='https://line.me'),
                PostbackTemplateAction(label='ping', data='ping'),
                PostbackTemplateAction(
                    label='ping with text', data='ping',
                    text='ping'),
                MessageTemplateAction(label='Translate Rice', text='米')
            ])
        template_message = TemplateSendMessage(
            alt_text='Buttons alt text', template=buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif text == 'carousel':
        carousel_template = CarouselTemplate(columns=[
            CarouselColumn(text='hoge1', title='fuga1', actions=[
                URITemplateAction(
                    label='Go to line.me', uri='https://line.me'),
                PostbackTemplateAction(label='ping', data='ping')
            ]),
            CarouselColumn(text='hoge2', title='fuga2', actions=[
                PostbackTemplateAction(
                    label='ping with text', data='ping',
                    text='ping'),
                MessageTemplateAction(label='Translate Rice', text='米')
            ]),
        ])
        template_message = TemplateSendMessage(
            alt_text='Buttons alt text', template=carousel_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif text == 'imagemap':
        pass
    elif text == '使い方':
        line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(
                        text='使い方を説明するね。みーとあっぷは、教えてもらったグループのスケジュール調整をするよ。ちょっぴりせっかちなので、フォローしたり締め切ったりします。'
                    ),
                    TextSendMessage(
                        text='まずは、グループを作るか友達からグループの合い言葉をおしえてもらってね。合い言葉をつぶやくとグループに入ることができるよ。ただし大人の事情で、一人で入れるグループは5個まで。一つのグループの定員は150人までだから気をつけてね。'
                    ),
                    TextSendMessage(
                        text='予定を立てるとき、5個まで候補を決めれるよ。候補は、"月/日/時"で”,”で区切って教えてね。たとえば候補が3月8日9時と3月10日12時の2つだったら、'
                    ),
                    TextSendMessage(
                        text='3/8/9,3/10/12'
                    ),
                    TextSendMessage(
                        text='っていう感じだよ。'
                    )
                ]
            )
    elif text == 'グループを作る':
        if isinstance(event.source, SourceUser):
            profile = line_bot_api.get_profile(event.source.user_id)
            #print(profile)
            l_name    = profile.display_name
            l_user_id = profile.user_id
            #reg = Users(l_name, l_user_id)
            #db.session.add(reg)
            #db.session.commit()

            if not db.session.query(User).filter(User.u_id == l_user_id).count():
                reg = User(l_user_id, l_name, "0", "")
                db.session.add(reg)
                db.session.commit()

            entry = User.query.filter(User.u_id == l_user_id).first()
            entry.u_status = '１'
            db.session.add(entry)
            db.session.commit()
            
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(
                        text='作りたいグループ名を教えて！')])

            app.logger.info( profile.display_name+" :flag: 1")
            # user_idが未登録ならユーザー追加
            #if not db.session.query(User).filter(User.u_id == l_user_id).count():
            #    reg = User(l_user_id, l_name, "", "")
            #    db.session.add(reg)
            #    db.session.commit()
                #line_bot_api.reply_message(
                #    event.reply_token, [
                #        TextSendMessage(
                #            text='Display name: ' + profile.display_name
                #        ),
                #        TextSendMessage(
                #            #text='Status message: ' + profile.status_message
                #            text='Status message: ' + profile.user_id
                #        )
                #    ]
                #)
            #else:
            #    line_bot_api.reply_message(
            #        event.reply_token, [
            #            TextSendMessage(
            #                text='もう登録されてるよ'
            #            )
            #        ]
            #    )

            
    else:
        if isinstance(event.source, SourceUser):
            profile = line_bot_api.get_profile(event.source.user_id)
            #print(profile)
            l_name    = profile.display_name
            l_user_id = profile.user_id
            #line_bot_api.reply_message(
            #    event.reply_token,
            #    TextMessage(text="Bot can't use profile API without user ID"))
            entry2 = User.query.filter(User.u_id == l_user_id).first()
            # グループ登録モード
            if entry2.u_status == '１':
                # グループ登録
                if not db.session.query(Groups).filter(Groups.g_name == text).count():
                    group_reg = Groups()
                    group_reg.g_name=text
                    db.session.add(group_reg)
                    db.session.commit()

                    l_groups = Groups.query.filter(Groups.g_name == text).first()
                    group_user_reg = Group_user()
                    group_user_reg.u_id = l_user_id
                    group_user_reg.g_id = l_groups.g_id
                    db.session.add(group_user_reg)
                    db.session.commit()

                    #entry = User.query.filter(User.u_id == l_user_id).first()
                    entry2.u_status = '0'
                    db.session.add(entry2)
                    db.session.commit()

                    line_bot_api.reply_message(
                        event.reply_token, [
                        TextSendMessage(
                        text=text+'っていうグループを作ったよ。'),
                        TextSendMessage(
                        text='次の合い言葉を友達に教えてね'),
                        TextSendMessage(
                        text='@addG+'+text+'+'+str(l_groups.g_id))])


                #グループ名が重複
                else:
                    line_bot_api.reply_message(
                        event.reply_token, [
                            TextSendMessage(
                                text='もう使われてるから、別のグループ名にしてね。')])
            else:
                entry = User.query.filter(User.u_id == l_user_id).first()
                entry.u_status = '0'
                db.session.add(entry)
                db.session.commit()

    #else:
    #    line_bot_api.reply_message(
    #        event.reply_token, TextSendMessage(text=event.message.text))
            





if __name__ == "__main__":
#    app.run()
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=443, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    # create tmp dir for download content
    make_static_tmp_dir()

    app.run(debug=options.debug, port=options.port)