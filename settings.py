import requests
import urllib3
from bs4 import BeautifulSoup

from .secrets import (
    BASE_URL,
    ADMIN_USER,
    ADMIN_PASS,
)



ADMIN_URL = "{}/admin/".format(BASE_URL)
LOGIN_URL = "{}/admin/login/".format(BASE_URL)
USERADD_URL = "{}/admin/auth/user/add/".format(BASE_URL)

LOGIN_DATA = {"username": ADMIN_USER, "password": ADMIN_PASS}

CSRFTOKEN_FIELD = "csrfmiddlewaretoken"


class Client:

    def __init__(self):
        self.session = requests.session()

    def get_soup(self, resp):
        return BeautifulSoup(resp.content, features="html.parser")

    def get_form(self, url):
        resp = self.session.get(url)
        soup = self.get_soup(resp)
        forms = soup.findAll("form")
        if len(forms) != 1:
            for form in forms:
                print(form.prettify())
            raise Exception("Multiple forms!")
        [form] = forms
        return resp, form

    def get_default_data(self, form):
        default_data = {}
        for elem in form.findAll("input"):
            name = elem.get("name")
            value = elem.get("value")
            if name is not None and value is not None:
                default_data[name] = value
        return default_data

    def post_form(self, url, data=None):
        resp, form = self.get_form(url)

        updated_data = self.get_default_data(form)
        updated_data.update(data or {})

        encoded_data = urllib3.parse.urlencode(updated_data, doseq=True)
        resp = self.session.post(url, encoded_data)

        if resp.status_code != 200:
            print("Status wasn't 200: {}".format(resp.status_code))
        else:
            soup = self.get_soup(resp)
            errornotes = soup.select(".errornote")
            if errornotes:
                for errornote in errornotes:
                    print(errornote.prettify())
            errorlists = soup.select(".errorlist")
            if errorlists:
                for errorlist in errorlists:
                    print(errorlist.parent.prettify())

        return resp

    def login(self):
        return self.post_form(LOGIN_URL, LOGIN_DATA)

    def useradd(self, username, password):
        data = {"username": username, "password1": password, "password2": password}
        return self.post_form(USERADD_URL, data)


c = Client()
c.login()
