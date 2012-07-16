import base64
from bson.objectid import ObjectId
import os
import bcrypt

import tornado.auth
import tornado.escape
import tornado.gen
import tornado.httpserver
import logging

class BaseHandler(tornado.web.RequestHandler):

    def get_login_url(self):
        return u"/login"

    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if user_json:
            return tornado.escape.json_decode(user_json)
        else:
            return None


class NotificationHandler(BaseHandler):
    def get(self):
        messages = self.application.syncdb.messages.find()
        self.render("notification.html", messages=messages, notification=self.get_argument("notification","") )

class SlidyHandler(BaseHandler):
    def get(self):
        messages = self.application.syncdb.messages.find()
        self.render("slidy.html", messages=messages, notification=self.get_argument("notification","") )

class PopupHandler(BaseHandler):
    def get(self):
        messages = self.application.syncdb.messages.find()
        self.render("popup.html", notification=self.get_argument("notification","") )

class LoginHandler(BaseHandler):

    def get(self):
        messages = self.application.syncdb.messages.find()
        self.render("login.html", notification=self.get_argument("notification","") )

    def post(self):
        email = self.get_argument("email", "")
        password = self.get_argument("password", "")

        user = self.application.syncdb['users'].find_one( { 'user': email } )
        
        # Warning bcrypt will block IO loop:
        if user and user['password'] and bcrypt.hashpw(password, user['password']) == user['password']:
            self.set_current_user(email)
            self.redirect("hello")
        else:
            error_msg = u"?notification=" + tornado.escape.url_escape("Login incorrect.")
            self.redirect(u"/login" + error_msg)

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
        self.render("hello.html", user=self.get_current_user(), messages=messages, notification=self.get_argument("notification","") )
    
    def get_messages(self):
        return self.application.syncdb.messages.find()

    def post(self):
        return self.get()

class MessageHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        users = self.application.syncdb['users'].find()
        self.render("message.html", user=self.get_current_user(), users=users, notification=self.get_argument("notification","") )

    def post(self):
        sent_to = self.get_argument('to')
        sent_from = self.get_current_user()
        message = self.get_argument("message")
        msg = {}
        msg['from'] = sent_from
        msg['to'] = sent_to
        msg['message'] = message
        
        if self.save_message(msg):
            self.redirect(u"/hello?notification=" + tornado.escape.url_escape("Message Sent"))
        else:
            print "error_msg"

    def save_message(self, msg):
        return self.application.syncdb['messages'].insert(msg)

class FacebookDemoHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("fb_demo.html", user=self.get_current_user(), fb_app_id=self.settings['facebook_app_id'] )
