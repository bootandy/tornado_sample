import mox

import uuid

from tornado.testing import AsyncHTTPTestCase
import tornado.web
import tornado.testing

from handlers.handlers import *


class TestPictureUploadHandler(AsyncHTTPTestCase):
    # def setUp(self):
    #     super(TestPictureUploadHandler, self).setUp()

    def get_app(self):
        app_settings = {
            'static_path': os.path.join(os.path.dirname(__file__), 'static'),
            'template_path': os.path.join(os.path.dirname(__file__), '../templates'),
            "cookie_secret": base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
        }

        app = tornado.web.Application([
            (r'/hello', HelloHandler),
        ], **app_settings)

        return app

    def test_image_upload(self):
        self.mox = mox.Mox()

        self.mox.StubOutWithMock(HelloHandler, 'get_current_user')
        HelloHandler.get_current_user().AndReturn('testuser')
        HelloHandler.get_current_user().AndReturn('testuser')
        self.mox.StubOutWithMock(HelloHandler, 'get_messages')
        HelloHandler.get_messages().AndReturn([])

        #home.HomePublicHandler.user_details = defaultdict(str)

        self.mox.ReplayAll()

        resp = self.fetch('/hello')
        #resp = self.post('/upload_picture')
        self.assertEqual(resp.code, 200)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()
