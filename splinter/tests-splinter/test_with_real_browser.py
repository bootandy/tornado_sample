# Acceptance Test Framework: http://splinter.cobrateam.info/

import unittest
from splinter.browser import Browser

print 'If you want to setup something do it here'

@unittest.skip('Splinter samples')
class SplinterSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.browser = Browser()

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()

    def test_visiting_google_com_returns_a_page_with_Google_in_title(self):
        self.browser.visit('http://www.google.com/')
        self.assertIn('Google', self.browser.title)

    def test_filling_Splinter_in_the_search_box_returns_Splinter_website(self):
        self.browser.visit('http://www.google.com/')
        self.browser.fill('q', 'Splinter python test')
        search_button = self.browser.find_by_name('btnG').first
        while not search_button.visible:
            # waits for the JavaScript to put the button on the page
            pass
        search_button.click()
        self.assertTrue(self.browser.is_text_present('splinter.cobrateam.info'))


class SplinterWebAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.browser = Browser()

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()

    def test_message_send(self):
        """ Start the server on http://localhost:8888/
        create a login with name: andy password: andy for this test to work"""

        self.browser.visit('http://localhost:8888/login')
        self.browser.fill('email', 'andy')
        self.browser.fill('password', 'andy')
        self.browser.find_by_name('login').click()

        # Press the Login Button:
        self.assertTrue(self.browser.is_text_present('Hello andy'),
                        'Could not Login - You must create a user with name: andy password: andy first')

        #Look for the 'send new message' link and click it:
        self.browser.find_link_by_text('send new message').click()
        self.assertTrue(self.browser.is_text_present('Message to:'))

        # Write a message
        self.browser.choose('to', 'andy')
        self.browser.fill('message', 'I am sending a message via splinter')
        self.browser.find_by_name('send').click()

        # Check the message appears when we are forward back to the home page
        self.assertTrue(self.browser.is_text_present('I am sending a message via splinter'))
        self.assertTrue(self.browser.is_text_present('Message Sent'))
