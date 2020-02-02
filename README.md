
# Django Admin Client


## Overview

Just a helper class so you can use the Django admin as a poor man's REST API.
Might be useful for writing integration tests for a bunch of interconnected Django services...


## Getting Started

In a fresh virtualenv,

    pip install -r requirements.txt


Create a settings.py containing at least the following settings (with values set appropriately):

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
    resp = c.add_user("testuser", "testpass")
