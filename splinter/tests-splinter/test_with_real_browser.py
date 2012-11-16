# from splinter import Browser

# browser = Browser('zope.testbrowser')
# # Chrome or Firefox support Javascript. Zope doesn't but is faster
# #browser = Browser()

# browser.visit('http://uk.yahoo.com/')
# browser.fill('p', 'splinter - python acceptance testing for web applications')
# browser.find_by_id('search-submit').click()

# if browser.is_text_present('splinter.cobrateam.info'):
#     print "Yes, the official website was found!"
# else:
#     print "No, it wasn't found... We need to improve our SEO techniques"

# browser.quit()

import unittest
from splinter.browser import Browser

print 'Setup database'

class TestGoogleSearch(unittest.TestCase):
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

