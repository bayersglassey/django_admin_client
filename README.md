
# Django Admin Client


## Overview

Just a helper class so you can use the Django admin as a poor man's REST API.
Might be useful for writing integration tests for a bunch of interconnected Django services...

Under the hood, it's all [requests](https://2.python-requests.org/en/master/) and
[beautiful soup](https://www.crummy.com/software/BeautifulSoup/).


## Getting Started

In a fresh virtualenv,

    pip install -r requirements.txt


Create a settings.py containing at least the following settings (with values set
appropriately for a running Django server):

    BASE_URL = "http://localhost:8000"
    ADMIN_USER = "username"
    ADMIN_PASS = "password"


Then in a Python shell,

    from settings import *
    from admin_client import Client

    # Create a client and log in to the Django admin
    c = Client(BASE_URL, ADMIN_USER, ADMIN_PASS)
    c.login()

    # Now, for example, to add a user via Django admin:
    user_id = c.add_user("testuser", "testpass")

    # Get a user's data as a dict:
    user_data = c.get_user(user_id)

    # Update a user's data:
    user_data["is_staff"] = True
    user_data["email"] = "test@example.com"
    user_data = c.change_user(user_id, user_data)

    # Update a user's groups (if you know some valid Group ids):
    user_data["groups"] = [1, 2]
    user_data = c.change_user(user_id, user_data)

    # Delete a user:
    c.delete_user(user_id)


Currently only the User model is directly supported, and even that's a bit hacky.
For instance, to get the user's data, we're just parsing the change form with beautiful soup.
