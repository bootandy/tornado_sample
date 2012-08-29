# Runs tests using lib/http_test_client which caches cookie values allowing us to login

from tests.lib.http_test_client import *
from tornado.testing import LogTrapTestCase, AsyncHTTPTestCase,AsyncTestCase, AsyncHTTPClient
from app import Application
import bcrypt
from tornado.ioloop import IOLoop 
import sys 


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
