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
        "cookie_secret":    base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
            #'xsrf_cookies': True,
            'debug':True,
            #'debug':False,
            'log_file_prefix':"tornado.log",
            }

        tornado.web.Application.__init__(self, handlers, **settings) # debug=True ,
        
        # Connect to mongodb
        #self.db = asyncmongo.Client(pool_id='mydb', host=MONGO_SERVER, port=27017, dbname='thanks')

        # sync is easy for now
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
