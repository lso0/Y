from seleniumbase import BaseCase
BaseCase.main(__name__, __file__)


class RecorderTest(BaseCase):
    def test_recording(self):
        self.open("https://app.revenuecat.com/loginhttps://app.revenuecat.com/login")
        self.open_if_not_url("https://app.revenuecat.com/login")
        self.type("input#email", "wiktor11gal@gmail.com")
        self.click('button[data-test="login-button"]')
        self.type("input#password", "rueiwoqp10229..")
        self.click('form[name="login"] > div > div:nth-of-type(3)')
        self.click('button[data-test="login-button"]')
        self.click('a[rel="noopener noreferrer"] > div > div')
        self.click('button:contains("Create new project")')
        self.type("input#project-name", "newprojectname3")
        self.click('button[data-test="add-project-button"]')
        self.click('span:contains("API Keys")')
        self.click('button[data-testid="ApiKey-New-action-link"]')
        self.type("input#label", "newapikey3")
        self.click('li:contains("V2")')
        self.click('li:contains("Read & write")')
        self.click('li:contains("Read & write")')
        self.click('li:contains("Read & write")')
        self.click('button:contains("Generate")')
        self.click('use[href="/icons/eye.svg#base"]')
        self.click('use[href="/icons/copy.svg#base"]')
