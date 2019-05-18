import datetime
import time
import unittest

from config import application
from config.database import Model
from masonite.app import App
from masonite.auth import Auth, MustVerifyEmail, Sign
from masonite.helpers import password as bcrypt_password
from masonite.helpers.routes import get
from masonite.request import Request
from masonite.snippets.auth.controllers.ConfirmController import \
    ConfirmController
from masonite.testing import DatabaseTestCase
from masonite.testsuite.TestSuite import generate_wsgi
from masonite.view import View


class User(Model, MustVerifyEmail):
    __guarded__ = []

# class MockUser():

#     __auth__ = 'email'
#     password = '$2a$04$SXAMKoNuuiv7iO4g4U3ZOemyJJiKAHomUIFfGyH4hyo4LrLjcMqvS'
#     users_password = 'pass123'
#     email = 'user@email.com'
#     name = 'testuser123'
#     id = 1

#     def where(self, column, name):
#         return self

#     def or_where(self, column, name):
#         return self

#     def first(self):
#         return self

#     def save(self):
#         pass

#     def find(self, id):
#         if self.id == id:
#             return self
#         return False


class TestAuth(DatabaseTestCase):

    def setUp(self):
        super().setUp()
        self.container = App()
        self.app = self.container
        User.create({
            'name': 'testuser123',
            'email': 'user@email.com',
            'password': bcrypt_password('secret')
        })
        self.app.bind('Container', self.app)
        view = View(self.container)
        self.request = Request(generate_wsgi())
        self.app.bind('Request', self.request)
        # self.auth = Auth(self.request, MockUser())
        self.container.bind('View', view.render)
        self.container.bind('ViewClass', view)
        self.app.bind('Application', application)
        self.app.bind('Auth', Auth)
        self.auth = self.app.make('Auth', User)

    def test_auth(self):
        self.assertTrue(self.auth)

    def test_login_user(self):
        self.assertTrue(self.auth.login('user@email.com', 'secret'))
        self.assertTrue(self.request.get_cookie('token'))

    # def test_login_user_with_list_auth_column(self):
    #     self.assertTrue(self.auth.login('testuser123', 'secret'))
    #     self.assertTrue(self.request.get_cookie('token'))

    def test_get_user(self):
        self.assertTrue(self.auth.login_by_id(1))

    def test_get_user_returns_false_if_not_loggedin(self):
        self.auth.login('user@email.com', 'wrong_secret')
        self.assertFalse(self.auth.user())

    def test_logout_user(self):
        self.auth.login('user@email.com', 'secret')
        self.assertTrue(self.request.get_cookie('token'))

        self.auth.logout()
        self.assertFalse(self.request.get_cookie('token'))
        self.assertFalse(self.auth.user())

    def test_login_user_fails(self):
        self.assertFalse(self.auth.login('user@email.com', 'bad_password'))

    def test_login_user_success(self):
        self.assertTrue(self.auth.login('user@email.com', 'secret'))

    def test_login_by_id(self):
        self.assertTrue(self.auth.login_by_id(1))
        self.assertTrue(self.request.get_cookie('token'))
        self.assertFalse(self.auth.login_by_id(2))

    def test_login_once_does_not_set_cookie(self):
        self.assertTrue(self.auth.once().login_by_id(1))
        self.assertIsNone(self.request.get_cookie('token'))

    # def test_user_is_mustverify_instance(self):
    #     self.assertIsInstance(self.auth.once().login_by_id(1), MustVerifyEmail)
    #     self.assertNotIsInstance(self.auth.once().login_by_id(1), MustVerifyEmail)

    def test_confirm_controller_success(self):
        params = {'id': Sign().sign('{0}::{1}'.format(1, time.time()))}
        self.request.set_params(params)
        user = self.auth.once().login_by_id(1)
        self.request.set_user(user)

        self.app.bind('Request', self.request)
        self.app.make('Request').load_app(self.app)

        # Create the route
        route = get('/email/verify/@id', ConfirmController.confirm_email)

        ConfirmController.get_user = User

        # Resolve the controller constructor
        controller = self.app.resolve(route.controller)

        # Resolve the method
        response = self.app.resolve(getattr(controller, route.controller_method))

        self.assertEqual(response.rendered_template, 'confirm')

    def test_confirm_controller_failure(self):
        timestamp_plus_11 = datetime.datetime.now() - datetime.timedelta(minutes=11)

        params = {'id': Sign().sign('{0}::{1}'.format(1, timestamp_plus_11.timestamp()))}
        self.request.set_params(params)
        user = self.auth.once().login_by_id(1)
        self.request.set_user(user)

        self.app.bind('Request', self.request)
        self.app.make('Request').load_app(self.app)

        # Create the route
        route = get('/email/verify/@id', ConfirmController.confirm_email)

        ConfirmController.get_user = User

        # Resolve the controller constructor
        controller = self.app.resolve(route.controller)

        # Resolve the method
        response = self.app.resolve(getattr(controller, route.controller_method))

        self.assertEqual(response.rendered_template, 'error')
