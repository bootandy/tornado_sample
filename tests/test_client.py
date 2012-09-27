# Runs tests using lib/http_test_client which caches cookie values allowing us to login

from tests.lib.http_test_client import *
from tornado.testing import LogTrapTestCase, AsyncHTTPTestCase,AsyncTestCase, AsyncHTTPClient
from app import Application
import bcrypt
from tornado.ioloop import IOLoop 
import sys 

from mock import MagicMock, Mock
from handlers.handlers import FacebookLoginHandler
from mox import Mox


class BaseHTTPTestCase(AsyncHTTPTestCase, HTTPClientMixin, LogTrapTestCase):
    def get_app(self):
        return Application(db='testdb')
 
    def _create_user(self, email, password):
        hashed_pass = bcrypt.hashpw(password, bcrypt.gensalt(8))
        user = {}
        user['user'] = email
        user['password'] = hashed_pass
        self.get_app().syncdb['users'].save(user)

    def setUp(self):
       super(BaseHTTPTestCase, self).setUp()
       self.client = TestClient(self)

# Tests based around remembering the user id after login.
class HandlersTestCase(BaseHTTPTestCase):
    def setUp(self):
        super(HandlersTestCase, self).setUp()
        self._create_user('test_user', 'secret') 

    def test_homepage(self):
        response = self.client.get('/login')
        self.assertEqual(response.code, 200)
        self.assertTrue('please login' in response.body)

        data = {'email': 'test_user', 'password': 'secret'}
        response = self.client.post('/login', data)
        self.assertEqual(response.code, 302)

        response = self.client.get('/hello')
        self.assertEqual(response.code, 200)
        self.assertTrue('please login' not in response.body)
        self.assertTrue('Hello test_user' in response.body)


class AsyncHandlerTestCase(BaseHTTPTestCase):
    def setUp(self):
        super(AsyncHandlerTestCase, self).setUp()
        self._create_user('test_user', 'secret') 

    def test_email(self):
        self.client = AsyncHTTPClient(self.io_loop)
        response = self.fetch('/email' )
        self.assertEqual(response.code, 200)
        self.assertIn('notification', response.effective_url )

    def get_new_ioloop(self): 
        return IOLoop.instance() 


# class MockHandlerTestCase(BaseHTTPTestCase):
#     def setUp(self):
#         super(MockHandlerTestCase, self).setUp()

#     # def test_fb_call(self):
#     #     response = self.fetch('/facebook_login?code=123' )
        
#     #     mock = Mock()
#     #     mock['fb_user'] = {}
#     #     self.authorize_redirect(mock)

#     #     self.assertEqual(response.code, 302)
#     #     self.assertIn('https://graph.facebook.com/oauth/access_token', response.effective_url )

#     def test_fb_return_call(self):
#         r = HTTPRequest('/facebook_login',  follow_redirects=True,
#                               headers='', method='GET', body='')
#         handler = FacebookLoginHandler(self.get_app(), r)
#         handler._on_login( {'_id':'asdf'})


#     def get_new_ioloop(self): 
#         return IOLoop.instance() 


class FbTestCase(BaseHTTPTestCase):
    #@patch('my_tornado_server.mongo_db_connection.query')
    # def test_a_random_handler_returns_some_json(self):

    #     r = HTTPRequest('/fb')
    #     request = Mock(follow_redirects=True, headers=True, method='GET', body={})
    #     #request.remote_ip  = '123.123.1.1'
    #     request.supports_http_1_1.return_value = True
    #     # Set any other attributes on the request that you need
    #     #mock_mongo_query.return_value = ['pink', 'orange', 'purple']

    #     handler = FacebookLoginHandler(self.get_app(), r)
    #     handler.write = Mock()

    #     handler.get('/facebook_login?code=123')

    #     print handler.write.call_args_list
    #     self.assertEqual(handler.write.call_args_list, json.dumps({'some': 'data'}))

    def get_new_ioloop(self): 
        return IOLoop.instance() 

    def test_can_handler_get(self):
        mox = Mox()

        application_mock = mox.CreateMockAnything()
        application_mock.ui_methods = {}
        application_mock.ui_modules = {}

        request_mock = mox.CreateMockAnything()
        request_mock.supports_http_1_1().AndReturn(True)
        request_mock.stream = 'asdf'
        request_mock.connecion = 'qqq'
        #request_mock.connecion.stream = 'asdf'

        process_request_mock = mox.CreateMockAnything()
        process_request_mock('GET',**{'arg':'should-be-args'})

        FacebookLoginHandler.authorize_redirect().AndReturn("hi there")

        mox.ReplayAll()

        try:
            handler = FacebookLoginHandler(self.get_app(), request_mock)
            handler.process_request = process_request_mock

            handler.get(arg='should-be-args')

            mox.VerifyAll()
        finally:
            mox.UnsetStubs()
