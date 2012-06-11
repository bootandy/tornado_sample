# encoding: utf-8
import os, os.path, sys
import tornado.web
import tornado.testing
import mox
from app import HelloHandler
from app import Application
from app import MessageHandler



class TestAuthenticatedHandlers(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        self.mox = mox.Mox()
        return Application(db='test')
 
    def tearDown(self):
        self.mox.UnsetStubs()
        self.mox.ResetAll()
 
    def test_new_admin(self):
        resp = self.fetch('/login')
        self.assertEqual(resp.code, 200)
 
    def test_get_past_login_page(self):
        self.mox.StubOutWithMock(HelloHandler, 'get_current_user', use_mock_anything=True)
        HelloHandler.get_current_user().AndReturn("test_user")
        HelloHandler.get_current_user().AndReturn("test_user")
        self.mox.ReplayAll()
        resp = self.fetch('/hello')
        self.assertEqual(resp.code, 200)
        self.assertIn( "Hello test_user", resp.body )
        self.mox.VerifyAll()

    def test_view_message(self):
        self.mox.StubOutWithMock(HelloHandler, 'get_current_user', use_mock_anything=True)
        HelloHandler.get_current_user().AndReturn("test_user")
        HelloHandler.get_current_user().AndReturn("test_user")
        
        self.mox.StubOutWithMock(HelloHandler, 'get_messages', use_mock_anything=True)
        HelloHandler.get_messages().AndReturn( [ {'from':'alice', 'to':'bob', 'message':'a mocked message'} ])

        self.mox.ReplayAll()
        resp = self.fetch('/hello')
        self.assertEqual(resp.code, 200)
        self.assertIn( "<td>a mocked message</td>", resp.body )
        self.mox.VerifyAll()

