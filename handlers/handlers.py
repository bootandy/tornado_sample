import base64
from bson.objectid import ObjectId
import os
import bcrypt

import tornado.auth
import tornado.escape
import tornado.httpserver


class BaseHandler(tornado.web.RequestHandler):

    def get_login_url(self):
        return u"/login"

    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if user_json:
            return tornado.escape.json_decode(user_json)
        else:
            return None


class LoginHandler(BaseHandler):

    def get(self):
        self.render("login.html", next=self.get_argument("next","/"), message=self.get_argument("error","") )

    def post(self):
        email = self.get_argument("email", "")
        password = self.get_argument("password", "")

        user = self.application.syncdb['users'].find_one( { 'user': email } )
        
        if user and user['password'] and bcrypt.hashpw(password, user['password']) == user['password']:
            self.set_current_user(email)
            self.redirect("hello")
        else:
            error_msg = u"?error=" + tornado.escape.url_escape("Login incorrect.")
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


        password = self.get_argument("password", "")
        hashed_pass = bcrypt.hashpw(password, bcrypt.gensalt(8))

        user = {}
        user['user'] = email
        user['password'] = hashed_pass

        auth = self.application.syncdb['users'].save(user)
        self.set_current_user(email)

        self.redirect("hello")


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(u"/login")

class HelloHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        messages = self.get_messages()
        self.render("hello.html", user=self.get_current_user(), messages=messages )

    def get_messages(self):
        return self.application.syncdb.messages.find()

    def post(self):
        return self.get()

class MessageHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        users = self.application.syncdb['users'].find()
        self.render("message.html", user=self.get_current_user(), users=users )

    def post(self):
        sent_to = self.get_argument('to')
        sent_from = self.get_current_user()
        message = self.get_argument("message")
        msg = {}
        msg['from'] = sent_from
        msg['to'] = sent_to
        msg['message'] = message
        
        if self.save_message(msg):
            self.redirect(u"/hello")
        else:
            print "error_msg"

    def save_message(self, msg):
        return self.application.syncdb['messages'].insert(msg)

