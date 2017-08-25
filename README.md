# py_fake_server
[![Build Status](https://travis-ci.org/Telichkin/py_fake_server.svg?branch=master)](https://travis-ci.org/Telichkin/py_fake_server)
[![codecov](https://codecov.io/gh/Telichkin/py_fake_server/branch/master/graph/badge.svg)](https://codecov.io/gh/Telichkin/py_fake_server)
[![Python versions](https://img.shields.io/pypi/pyversions/py_fake_server.svg)](https://pypi.python.org/pypi/py_fake_server)

**py_fake_server** helps you create fake servers with pleasure. It provides
declarative API both for server creation and for checking expectation.
Let's look at some examples below!


## Install
`pip3 install py_fake_server`


## Getting Started

Here is a simple example showing how to create a dummy test with py_fake_server.

```python
# dummy_test.py

import requests
from py_fake_server import FakeServer


def test_simple_example():
    server = FakeServer(host="localhost", port=8081)
    server.start()
    server. \
        on_("get", "/hello"). \
        response(status=200, body="Hello, World!", content_type="text/plain")
    
    response = requests.get(server.base_uri + "/hello")
    
    assert server. \
        was_requested("get", "/hello"). \
        exactly_once().check()
        
```


# A more complex example

Here is a more interesting example that demonstrates checking body, cookies, content-type, and working with more than one response from server. Imagine, that we're testing api-gateway that should check a user authentication in an auth microservice before update the user information in a portfolio microservice. And we don't want to up and run both auth and portfolio microservices, but we can use py_fake_servers instead.

```python
# more_complex_test.py
import pytest
import requests
from py_fake_server import FakeServer

API_GATEWAY_BASE_URI = "http://localhost:8080"


@pytest.fixture(scope="session")
def auth_server():
    server = FakeServer(host="localhost", port=8081)
    server.start()
    yield server
    server.stop()


@pytest.fixture(scope="session")
def portfolio_server():
    server = FakeServer(host="localhost", port=8082)
    server.start()
    yield server
    server.stop()


@pytest.fixture(scope="function", autouse=True)
def servers_cleanup(auth_server, portfolio_server):
    auth_server.clear()
    portfolio_server.clear()
    yield
    auth_server.clear()
    portfolio_server.clear()


def test_more_complex_example(auth_server: FakeServer, portfolio_server: FakeServer):
    auth_server. \
        on_("post", "/auth"). \
        response(status=204)

    portfolio_server. \
        on_("patch", "/portfolios/34"). \
        response(status=204)

    requests.patch(API_GATEWAY_BASE_URI + "/users/34/portfolio",
                   json={"description": "Brand new Description"},
                   cookies={"token": "auth-token-with-encrypted-user-id-34"})

    assert auth_server. \
        was_requested("post", "/auth"). \
        exactly_once(). \
        for_the_first_time(). \
        with_cookies({"token": "auth-token-with-encrypted-user-id-34"}).check()

    assert portfolio_server. \
        was_requested("patch", "/portfolios/34"). \
        exactly_once(). \
        for_the_first_time(). \
        with_json({"description": "Brand new Description"}). \
        with_content_type("application/json").check()
        
```


## License
MIT License

Copyright (c) 2017 Roman Telichkin

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
