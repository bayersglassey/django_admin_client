
## Usage

In a fresh virtualenv,

    pip install -r requirements.txt

Create a secrets.py containing at least:

    BASE_URL = "http://localhost:8000"
    ADMIN_USER = "<username of a superuser>"
    ADMIN_PASS = "<password of that superuser>"

Then run `ipython` and:

    from settings import *

    # Add a user via Django admin
    resp = c.useradd("testuser", "testpass")
