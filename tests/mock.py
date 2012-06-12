# Runs tests using mox which mocks the login phase

# encoding: utf-8
import os, os.path, sys
import tornado.web
import tornado.testing
import mox
import urllib
from app import Application
from handlers.handlers import *



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

    def test_post_message(self):
        self.mox.StubOutWithMock(MessageHandler, 'get_current_user', use_mock_anything=True)
        MessageHandler.get_current_user().AndReturn("test_user")
        
        self.mox.StubOutWithMock(HelloHandler, 'get_current_user', use_mock_anything=True)
        HelloHandler.get_current_user().AndReturn("test_user")
        HelloHandler.get_current_user().AndReturn("test_user")

        msg = { 'to':'alice', 'from':'test_user', 'message':'testing'}
        self.mox.StubOutWithMock(MessageHandler, 'save_message', use_mock_anything=True)
        MessageHandler.save_message(msg).AndReturn(True)

        self.mox.ReplayAll()
        args = { 'to':'alice', 'message':'testing'}
        resp = self.fetch('/message', method='POST', body=urllib.urlencode(args))
        self.assertEqual(resp.code, 200)
        self.mox.VerifyAll()

