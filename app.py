# Python imports
import base64
from bson.objectid import ObjectId
import os
import bcrypt

# Tornado imports
import pymongo
import re
import uuid
import datetime
import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options
from tornado.web import url


define("port", default=8888, type=int)
define("config_file", default="app_config.yml", help="app_config file")

#MONGO_SERVER = '192.168.1.68'
MONGO_SERVER = 'localhost'

# Application class
class Application(tornado.web.Application):
  def __init__(self):
    #self.config = self._get_config()
    handlers = [
    url(r'/', LoginHandler, name='index'),
    url(r'/hello', HelloHandler, name='hello'),
    url(r'/message', MessageHandler, name='message'),
    url(r'/login', LoginHandler, name='login'),
    url(r'/register', RegisterHandler, name='register'),
    url(r'/logout', LogoutHandler, name='logout'),
    ]

    #xsrf_cookies is for XSS protection add this to all forms: {{ xsrf_form_html() }}
    settings = {
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
    "cookie_secret":  base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
      #'xsrf_cookies': True,
      'debug':True,
      #'debug':False,
      'log_file_prefix':"tornado.log",
      }

    tornado.web.Application.__init__(self, handlers,**settings) # debug=True ,
    # Connect to mongodb
    #self.db = asyncmongo.Client(pool_id='mydb', host=MONGO_SERVER, port=27017, dbname='thanks')

    # sync is easy for now
    self.syncconnection = pymongo.Connection(MONGO_SERVER, 27017)
    self.syncdb = self.syncconnection ["test-thank"]

    #self.syncconnection.close()


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
    self.render(  "register.html", next=self.get_argument("next","/"))

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
  def get(self):
    if self.get_secure_cookie("user"):
      messages = self.application.syncdb.messages.find()
      self.render("hello.html", user=self.get_current_user(), messages=messages )
    else:
      self.redirect(u"/login")

class MessageHandler(BaseHandler):
  def get(self):
    if self.get_secure_cookie("user"):
      
      users = self.application.syncdb['users'].find()

      self.render("message.html", user=self.get_current_user(), users=users )
    else:
      self.redirect(u"/login")

  def post(self):
    if self.get_secure_cookie("user"):
      sent_to = self.get_argument('to')
      sent_from = self.get_current_user()
      message = self.get_argument("message")
      msg = {}
      msg['from'] = sent_from
      msg['to'] = sent_to
      msg['message'] = message
      if self.application.syncdb['messages'].insert(msg):
        self.redirect(u"/hello")
      else:
        print "error_msg"


    else:
      self.redirect(u"/login")



# to redirect log file run python with : --log_file_prefix=mylog
def main():
  tornado.options.parse_command_line()
  http_server = tornado.httpserver.HTTPServer(Application())
  http_server.listen(options.port)
  tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
  main()
