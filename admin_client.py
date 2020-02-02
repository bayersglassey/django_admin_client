import requests
from bs4 import BeautifulSoup



LOGIN_URL = "{base_url}/admin/login/"
ADD_USER_URL = "{base_url}/admin/auth/user/add/"
CHANGE_USER_URL = "{base_url}/admin/auth/user/{user_id}/change/"

CSRFTOKEN_FIELD = "csrfmiddlewaretoken"


class Client:

    def __init__(self, base_url, admin_username, admin_password):
        self.base_url = base_url
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.session = requests.session()

    def expand_url(self, url_template, **kwargs):
        return url_template.format(base_url=self.base_url, **kwargs)

    def get_soup(self, resp):
        return BeautifulSoup(resp.content, features="html.parser")

    def get_form(self, url, select="form"):
        resp = self.session.get(url)
        soup = self.get_soup(resp)
        forms = soup.select(select)
        if len(forms) == 0:
            raise Exception("No forms!")
        if len(forms) > 1:
            print("Multiple forms!")
            for form in forms:
                print(form.prettify())
            raise Exception("Multiple forms!")
        [form] = forms
        return form

    def get_default_data(self, form):
        default_data = {}
        for elem in form.findAll("input"):
            # TODO: support field types other than text input
            # (Also, I think we need to treat Django's filter_horizontal and
            # filter_vertical specially... not sure though, check the HTML
            # *source* before any JS has a chance to frig with it...)
            name = elem.get("name")
            value = elem.get("value")
            if name is not None and value is not None:
                default_data[name] = value
        return default_data

    def post_form(self, url, data=None, select=None):
        form = self.get_form(url)

        updated_data = self.get_default_data(form)
        updated_data.update(data or {})

        resp = self.session.post(url, updated_data)

        if resp.status_code != 200:
            raise Exception("Status wasn't 200!", resp)
        else:
            ok = True
            soup = self.get_soup(resp)
            errornotes = soup.select(".errornote")
            if errornotes:
                ok = False
                for errornote in errornotes:
                    print(errornote.prettify())
            errorlists = soup.select(".errorlist")
            if errorlists:
                ok = False
                for errorlist in errorlists:
                    print(errorlist.parent.prettify())
            if not ok:
                raise Exception("Form had errors!")

        return resp

    def login(self):
        url = self.expand_url(LOGIN_URL)
        data = {"username": self.admin_username, "password": self.admin_password}
        return self.post_form(url, data)

    def add_user(self, username, password):
        url = self.expand_url(ADD_USER_URL)
        data = {"username": username, "password1": password, "password2": password}
        return self.post_form(url, data)

    def change_user(self, user_id, data):
        url = self.expand_url(CHANGE_USER_URL, user_id=user_id)
        return self.post_form(url, data)

