import getpass
import logging
import os
import requests

from abc import ABC, abstractmethod
from selenium import webdriver


class HttpGetResponse:
    def __init__(self, text, url):
        self.text = text
        self.url = url


class Driver(ABC):
    def __init__(self, timeout):
        self.timeout = timeout

    @abstractmethod
    def get(self, url) -> HttpGetResponse:
        pass


class SeleniumDriver(Driver):
    def __init__(self, timeout):
        super().__init__(timeout)
        self.did_warn = False

        self.driver_path = '/usr/bin/chromedriver'
        if not os.path.exists(self.driver_path):
            raise Exception(f'not found: {self.driver_path}')

        self.options = webdriver.ChromeOptions()
        self.options.headless = True
        if getpass.getuser() == 'root':
            self.options.add_argument('--no-sandbox')  # required if root

    def get(self, url) -> HttpGetResponse:
        if not self.did_warn:
            logging.warning('warning: using selenium webdriver for scraping... this feature is under active development')
            self.did_warn = True

        # headless chromium crashes somewhat regularly...
        # for now, we will start a fresh instance every time
        driver = webdriver.Chrome(self.driver_path, options=self.options)
        try:
            driver.get(url)
            return HttpGetResponse(driver.page_source, url)
        finally:
            driver.close()
            driver.quit()


class RequestsDriver(Driver):
    def get(self, url) -> HttpGetResponse:
        headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36'}
        r = requests.get(url, headers=headers, timeout=self.timeout)
        if not r.ok:
            raise Exception(f'got response with status code {r.status_code} for {url}')
        return HttpGetResponse(r.text, r.url)


class DriverRepo:
    def __init__(self, timeout):
        self.requests = RequestsDriver(timeout)
        self.selenium = SeleniumDriver(timeout)


def init_drivers(config):
    return DriverRepo(config.refresh_interval)
