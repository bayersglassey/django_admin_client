import re
import requests
from bs4 import BeautifulSoup



LOGIN_URL = "/admin/login/"
USER_URL = "/admin/auth/user/"
GROUP_URL = "/admin/auth/group/"


# Some fields which aren't model fields, so need to be
# filtered out of the dicts we generate
CSRFTOKEN_FIELD = "csrfmiddlewaretoken"
CHANGEFORM_FIELDS = [
    CSRFTOKEN_FIELD,
    "_addanother", "_continue", "_save",
]


class Client:

    def __init__(self, base_url, admin_username, admin_password, lockdown_password=None):
        self.base_url = base_url
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.lockdown_password = lockdown_password
        self.session = requests.session()

    def expand_url(self, url, **kwargs):
        return self.base_url + url.format(**kwargs)

    def get_add_url(self, url):
        return "{}{}".format(self.expand_url(url), "add/")

    def get_change_url(self, url, id):
        return "{}{}{}".format(self.expand_url(url), id, "/change/")

    def get_delete_url(self, url, id):
        return "{}{}{}".format(self.expand_url(url), id, "/delete/")

    def get_soup(self, resp):
        return BeautifulSoup(resp.content, features="html.parser")

    def get_form(self, soup, select=None):
        forms = soup.select(select or "form")
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
            name = elem.get("name")
            if name is None: continue

            type = elem["type"]
            if type in ["checkbox", "radio"]:
                value = "checked" in elem.attrs
            else:
                value = elem.get("value")

            default_data[name] = value

        for elem in form.findAll("textarea"):
            name = elem.get("name")
            if name is None: continue

            value = elem.text
            default_data[name] = value

        for elem in form.findAll("select"):
            name = elem.get("name")
            if name is None: continue

            multi = "multiple" in elem.attrs

            selected_values = []
            options = elem.findAll("option")
            for option in options:
                if "selected" not in option.attrs: continue
                value = option.get("value")
                selected_values.append(value)

            if multi:
                value = selected_values
            elif len(selected_values):
                value = selected_values[0]
            elif len(options):
                value = options[0].get("value")
            else:
                value = None
            default_data[name] = value

        return default_data

    def encode_data(self, data):
        """Encodes data as if we were a browser POSTing a form.
        For instance, converts True/False to "on"/None, mimicking
        the standard browser behaviour for <input type="checkbox">."""
        encoded_data = {}
        for key, values in data.items():
            encoded_values = []
            if not isinstance(values, (list, tuple)):
                values = [values]
            for value in values:
                if isinstance(value, bool):
                    encoded_value = "on" if value else None
                else:
                    encoded_value = value
                encoded_values.append(encoded_value)
            encoded_data[key] = encoded_values
        return encoded_data

    def post_form(self, url, data=None, select=None):
        resp = self.session.get(url)
        soup = self.get_soup(resp)
        lockdown = soup.select("#lockdown")
        if lockdown:
            print('Detected lockdown')
            form = self.get_form(soup)
            updated_data = self.get_default_data(form)
            updated_data.update({'password': self.lockdown_password})
            encoded_data = self.encode_data(updated_data)
            resp = self.session.post(url, encoded_data)

            if resp.status_code != 200:
                raise Exception("Lockdown status wasn't 200!", resp)

            resp = self.session.get(url)
            soup = self.get_soup(resp)
            lockdown = soup.select("#lockdown")
            assert not lockdown, lockdown

        form = self.get_form(soup, select)

        updated_data = self.get_default_data(form)
        updated_data.update(data or {})
        encoded_data = self.encode_data(updated_data)

        headers = {
            "Referer": url,
        }
        resp = self.session.post(url, encoded_data, headers=headers)

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

    def get_list_elem(self, url):
        resp = self.session.get(url)
        soup = self.get_soup(resp)
        return soup.find(attrs={"id": "result_list"})

    def get_change_regex(self, url):
        return re.compile(url + r"(?P<id>[0-9]+)" + "/change/")

    def get_change_links(self, url):
        list_elem = self.get_list_elem(self.expand_url(url))
        regex = self.get_change_regex(url)
        return list_elem.findAll(attrs={"href": regex})

    def get_ids(self, url):
        links = self.get_change_links(url)
        regex = self.get_change_regex(url)
        return [
            int(re.fullmatch(regex, link["href"]).groupdict()["id"])
            for link in links]

    def get_change_id(self, url, change_url):
        regex = self.get_change_regex(url)
        return int(re.fullmatch(regex, change_url).groupdict()["id"])

    def get_object_data(self, soup):
        form = self.get_form(soup)
        data = self.get_default_data(form)

        # Scrub fields which just belong to the changeform, not the model
        for field in CHANGEFORM_FIELDS:
            if field in data:
                del data[field]

        return data

    def get_object(self, url, id):
        change_url = self.get_change_url(url, id)
        resp = self.session.get(change_url)
        soup = self.get_soup(resp)
        return self.get_object_data(soup)

    def add_object(self, url, data):
        add_url = self.get_add_url(url)
        resp = self.post_form(add_url, data)
        return self.get_change_id(url, resp.url.replace(self.base_url, "", 1))

    def change_object(self, url, id, data):
        change_url = self.get_change_url(url, id)
        resp = self.post_form(change_url, data)
        soup = self.get_soup(resp)
        return self.get_object_data(soup)

    def delete_object(self, url, id):
        delete_url = self.get_delete_url(url, id)
        return self.post_form(delete_url)

    def register_model(self, name, url):
        # I'm not usually into Python magic, but in this case it's kind of fun.
        # Usage:
        #
        #     # Assuming a model called Thing living in app "myapp":
        #
        #     client = Client()
        #     client.register_model("thing", "/admin/myapp/thing/")
        #
        #     # Pick an existing thing
        #     thing_ids = client.get_things()
        #     thing_id = thing_ids[0]
        #
        #     # Examine it
        #     thing_data = client.get_thing(thing_id)
        #
        #     # Etc...

        def get_Xs():
            return self.get_ids(url)

        def get_X(id):
            return self.get_object(url, id)

        def add_X(data):
            return self.add_object(url, data)

        def change_X(id, data):
            return self.change_object(url, id, data)

        def delete_X(id):
            return self.delete_object(url, id)

        setattr(self, "get_{}s".format(name), get_Xs)
        setattr(self, "get_{}".format(name), get_X)
        setattr(self, "add_{}".format(name), add_X)
        setattr(self, "change_{}".format(name), change_X)
        setattr(self, "delete_{}".format(name), delete_X)


    ###########################################################################
    # HELPER METHODS FOR SPECIFIC MODELS
    # (Can probably be replaced by register_model magic?..)

    def get_users(self):
        return self.get_ids(USER_URL)

    def get_user(self, id):
        return self.get_object(USER_URL, id)

    def add_user(self, username, password):
        data = {"username": username, "password1": password, "password2": password}
        return self.add_object(USER_URL, data)

    def change_user(self, id, data):
        return self.change_object(USER_URL, id, data)

    def delete_user(self, id):
        return self.delete_object(USER_URL, id)
