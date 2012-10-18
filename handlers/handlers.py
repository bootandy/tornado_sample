import base64
from bson.objectid import ObjectId
import os
import bcrypt
import hashlib
import urllib

import tornado.auth
import tornado.escape
import tornado.gen
import tornado.httpserver
import logging
import pymongo.json_util
import json
import urlparse
import time
from tornado.ioloop import IOLoop
from tornado.web import asynchronous, RequestHandler, Application
from tornado.httpclient import AsyncHTTPClient

class BaseHandler(RequestHandler):

    def get_login_url(self):
        return u"/login"

    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if user_json:
            return tornado.escape.json_decode(user_json)
        else:
            return None

    # Allows us to get the previous URL
    def get_referring_url(self):
        try:
            _, _, referer, _, _, _ = urlparse.urlparse(self.request.headers.get('Referer'))
            if referer:
                return referer
        # Test code will throw this if there was no 'previous' page
        except AttributeError:
            pass
        return '/'


    def get_flash(self):
        flash = self.get_secure_cookie('flash')
        self.clear_cookie('flash')
        return flash

    def get_essentials(self):
        mp = {k:''.join(v) for k,v in self.request.arguments.iteritems()}
        print mp


class NotificationHandler(BaseHandler):
    def get(self):
        messages = self.application.syncdb.messages.find()
        self.render("notification.html", messages=messages, notification='hello' )

class SlidyHandler(BaseHandler):
    def get(self):
        messages = self.application.syncdb.messages.find()
        self.render("slidy.html", messages=messages, notification=self.get_flash() )

class PopupHandler(BaseHandler):
    def get(self):
        messages = self.application.syncdb.messages.find()
        self.render("popup.html", notification=self.get_flash() )

class MenuTagsHandler(BaseHandler):
    def get(self):
        self.render("menu_tags.html", notification=self.get_flash() )

class LoginHandler(BaseHandler):
    def get(self):
        messages = self.application.syncdb.messages.find()
        self.render("login.html", notification=self.get_flash() )

    def post(self):
        email = self.get_argument("email", "")
        password = self.get_argument("password", "")

        user = self.application.syncdb['users'].find_one( { 'user': email } )

        # Warning bcrypt will block IO loop:
        if user and user['password'] and bcrypt.hashpw(password, user['password']) == user['password']:
            self.set_current_user(email)
            self.redirect("hello")
        else:
            self.set_secure_cookie('flash', "Login incorrect")
            self.redirect(u"/login")

    def set_current_user(self, user):
        print "setting "+user
        if user:
            self.set_secure_cookie("user", tornado.escape.json_encode(user))
        else:
            self.clear_cookie("user")


class RegisterHandler(LoginHandler):
    def get(self):
        self.render("register.html", next=self.get_argument("next","/"))

    def post(self):
        email = self.get_argument("email", "")

        already_taken = self.application.syncdb['users'].find_one( { 'user': email } )
        if already_taken:
            error_msg = u"?error=" + tornado.escape.url_escape("Login name already taken")
            self.redirect(u"/login" + error_msg)

        # Warning bcrypt will block IO loop:
        password = self.get_argument("password", "")
        hashed_pass = bcrypt.hashpw(password, bcrypt.gensalt(8))

        user = {}
        user['user'] = email
        user['password'] = hashed_pass

        auth = self.application.syncdb['users'].save(user)
        self.set_current_user(email)

        self.redirect("hello")

class TwitterLoginHandler(LoginHandler,
                          tornado.auth.TwitterMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("oauth_token", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authorize_redirect()

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Twitter auth failed")
        print "Auth worked"
        #user_details = self.application.syncdb['users'].find_one( {'twitter': tw_user['username'] } )
        # Create user if user not found

        self.set_current_user(tw_user['username'])
        self.redirect("hello")


class FacebookLoginHandler(LoginHandler, tornado.auth.FacebookGraphMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument('code', False):
            self.get_authenticated_user(
                redirect_uri=self.settings['facebook_registration_redirect_url'],
                client_id=self.application.settings['facebook_app_id'],
                client_secret=self.application.settings['facebook_secret'],
                code=self.get_argument('code'),
                callback=self.async_callback(self._on_login)
            )
            return
        self.authorize_redirect(redirect_uri=self.settings['facebook_registration_redirect_url'],
                                client_id=self.settings['facebook_app_id'],
                                extra_params={'scope': 'offline_access'})  # read_stream,

    def _on_login(self, fb_user):
        #user_details = self.application.syncdb['users'].find_one( {'facebook': fb_user['id']} )
        # Create user if user not found
        self.set_current_user(fb_user['id'])
        self.redirect("hello")


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(u"/login")


class HelloHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        messages = self.get_messages()
        self.render("hello.html", user=self.get_current_user(), messages=messages, notification=self.get_flash() )

    def get_messages(self):
        return self.application.syncdb.messages.find()

    def post(self):
        return self.get()


class EmailMeHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        http_client = AsyncHTTPClient()
        mail_url = self.settings["mandrill_url"] + "/messages/send.json"
        mail_data = {
            "key": self.settings["mandrill_key"],
            "message": {
                "html": "html email from tornado sample app <b>bold</b>",
                "text": "plain text email from tornado sample app",
                "subject": "from tornado sample app",
                "from_email": "hello@retechnica.com",
                "from_name": "Hello Team",
                "to":[{"email": "sample@retechnica.com"}]
            }
        }

        # mail_data = {
        #     "key": self.settings["mandrill_key"],
        # }
        #mail_url = self.settings["mandrill_url"] + "/users/info.json"

        body = tornado.escape.json_encode(mail_data)
        response = yield tornado.gen.Task(http_client.fetch, mail_url, method='POST', body=body)
        logging.info(response)
        logging.info(response.body)

        if response.code == 200:
            self.set_secure_cookie('flash', "sent")
            self.redirect('/')
        else:
            self.set_secure_cookie('flash', "FAIL")
            self.redirect('/')


class MessageHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        users = self.application.syncdb['users'].find()
        self.render("message.html", user=self.get_current_user(), users=users, notification=self.get_flash() )

    def post(self):
        sent_to = self.get_argument('to')
        sent_from = self.get_current_user()
        message = self.get_argument("message")
        msg = {}
        msg['from'] = sent_from
        msg['to'] = sent_to
        msg['message'] = message

        if self.save_message(msg):
            self.set_secure_cookie('flash', "Message Sent")
            self.redirect(u"/hello")
        else:
            print "error_msg"

    def save_message(self, msg):
        return self.application.syncdb['messages'].insert(msg)


class FacebookDemoHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("fb_demo.html", user=self.get_current_user(), fb_app_id=self.settings['facebook_app_id'] )


class GravatarHandler(BaseHandler):
    def build_grav_url(self, email):

        #default = "http://thumbs.dreamstime.com/thumblarge_540/1284957171JgzjF1.jpg"
        # random patterned background:
        default = 'identicon'
        size = 40

        # construct the url
        gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?"
        gravatar_url += urllib.urlencode({'d':default, 's':str(size)})
        return gravatar_url

    def get(self):
        email = self.get_argument('email', "sample@gmail.com")
        self.render("grav.html", user=self.get_current_user(), email=email, icon=self.build_grav_url(email))



class WildcardPathHandler(BaseHandler):
    def initialize(self):
        self.supported_path = ['good', 'nice']

    """ prepare() called just before either get or post
    like a later version of init() """
    def prepare(self):
        print self.request.path
        action = self.request.path.split('/')[-2]
        if action not in self.supported_path:
            self.write('<html><body>I dont like that url</body></html>')
            self.finish()
            return

    def get(self, action):
        self.write('<html><body>I am happy you went to '+action+'</body></html>')
        self.finish()

    def post(self, action):
        self.write('<html><body>I am happy you went to '+action+'</body></html>')
        self.finish()


class ReferBackHandler(BaseHandler):
    def get(self):
        print 'returning back to previous page'
        self.set_secure_cookie("flash", "returning back to previous page")
        self.redirect(self.get_referring_url())


"""
async demo - creates a constantly loading webpage which updates from a file.
'tail -f data/to_read.txt' >> webpage
"""
class TailHandler(BaseHandler):
    @asynchronous
    def get(self):
        self.file = open('data/to_read.txt', 'r')
        self.pos = self.file.tell()

        def _read_file():
            # Read some amout of bytes here. You can't read until newline as it
            # would block
            line = self.file.read(40)
            last_pos = self.file.tell()
            if not line:
                self.file.close()
                self.file = open('data/to_read.txt', 'r')
                self.file.seek(last_pos)
                pass
            else:
                self.write(line)
                self.flush()

            IOLoop.instance().add_timeout(time.time() + 1, _read_file)
        _read_file()


class DataPusherHandler(BaseHandler):
    #@asynchronous
    def get(self):
        data = self.application.syncdb['data_pusher'].find()
        self.render("data_pusher.html", user=self.get_current_user(), data=data)

    def post(self):
        print 'POST DataPusherHandler'
        user = self.get_current_user()
        if not user:
            user = 'not logged in '
        message = self.get_argument("message")
        msg = {}
        msg['message'] = user + ' : '+message

        self.application.syncdb['data_pusher'].insert(msg)
        self.write('done')
        self.finish()
        return
        #self.redirect('/pusher')


class DataPusherRawHandler(BaseHandler):
    def get(self):
        def _read_data():
            m_id = self.get_argument('id','')
            print m_id
            if m_id:
                data = list(self.application.syncdb['data_pusher'].find(
                    {'_id' : {'$gt':ObjectId(m_id)} }))
            else:
                data = list(self.application.syncdb['data_pusher'].find())

            s = json.dumps(data, default=pymongo.json_util.default)
            self.write(s)
            self.flush()
        _read_data()
