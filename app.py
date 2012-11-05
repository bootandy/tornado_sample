# Python imports

# Tornado imports
import pymongo
import uuid
import datetime
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options
from tornado.web import url

from handlers.handlers import *


define("port", default=8888, type=int)
define("config_file", default="app_config.yml", help="app_config file")

#MONGO_SERVER = '192.168.1.68'
MONGO_SERVER = 'localhost'

# Application class
class Application(tornado.web.Application):
    def __init__(self, **overrides):
        #self.config = self._get_config()
        handlers = [
        url(r'/', HelloHandler, name='index'),
        url(r'/hello', HelloHandler, name='hello'),
        url(r'/email', EmailMeHandler, name='email'),
        url(r'/message', MessageHandler, name='message'),
        url(r'/grav', GravatarHandler, name='grav'),
        url(r'/menu', MenuTagsHandler, name='menu'),
        url(r'/slidy', SlidyHandler, name='slidy'),
        url(r'/notification', NotificationHandler, name='notification'),
        url(r'/fb_demo', FacebookDemoHandler, name='fb_demo'),
        url(r'/popup', PopupHandler, name='popup_demo'),
        url(r'/tail', TailHandler, name='tail_demo'),
        url(r'/pusher', DataPusherHandler, name='push_demo'),
        url(r'/pusher_raw', DataPusherRawHandler, name='push_raw_demo'),
        url(r'/matcher/([^\/]+)/', WildcardPathHandler),
        url(r'/back_to_where_you_came_from', ReferBackHandler, name='referrer'),
        url(r'/thread', ThreadHandler, name='thread_handler'),

        url(r'/login', LoginHandler, name='login'),
        url(r'/twitter_login', TwitterLoginHandler, name='twitter_login'),
        url(r'/facebook_login', FacebookLoginHandler, name='facebook_login'),
        url(r'/register', RegisterHandler, name='register'),
        url(r'/logout', LogoutHandler, name='logout'),

        ]

        #xsrf_cookies is for XSS protection add this to all forms: {{ xsrf_form_html() }}
        settings = {
            'static_path': os.path.join(os.path.dirname(__file__), 'static'),
            'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
            "cookie_secret":    base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
            'twitter_consumer_key': 'KEY',
            'twitter_consumer_secret' :'SECRET',
            'facebook_app_id': '180378538760459',
            'facebook_secret': '7b82b89eb6aa0d3359e2036e4d1eedf0',
            'facebook_registration_redirect_url': 'http://localhost:8888/facebook_login',
            'mandrill_key': 'KEY',
            'mandrill_url': 'https://mandrillapp.com/api/1.0/',

            'xsrf_cookies': False,
            'debug':True,
            'log_file_prefix':"tornado.log",
        }

        tornado.web.Application.__init__(self, handlers, **settings) # debug=True ,

        self.syncconnection = pymongo.Connection(MONGO_SERVER, 27017)

        if 'db' in overrides:
            self.syncdb = self.syncconnection [overrides['db']]
        else:
            self.syncdb = self.syncconnection ["test-thank"]

        #self.syncconnection.close()

# to redirect log file run python with : --log_file_prefix=mylog
def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
