"""Message View tests.
    to run these tests, copy and paste into your terminal:
    FLASK_ENV=production python -m unittest test_message_views.py
"""

import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 123456
        self.testuser.id = self.testuser_id
        db.session.commit()


        self.testmessage = Message(text="Like this message", user_id=self.testuser_id)
        self.testmessage.id = 999
        db.session.add(self.testmessage)
        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
    
########### TESTS ON MESSAGE VIEWS: SHOW MESSAGE ###########

    def test_show_message(self):
        """ Can you view a valid message? """
        m = Message(
            id = 24235,
            text= "Message message, text text!",
            user_id = self.testuser_id
        )
        db.session.add(m)
        db.session.commit()

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            
            resp = c.get('/messages/999')
            self.assertEqual(resp.status_code, 200)

            m = Message.query.get(24235)
            resp = c.get(f'/messages/{m.id}')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(m.text, str(resp.data))

    def test_show_message_invalid(self):
        """ Can you view a message with an invalid id?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            
            resp = c.get('/messages/123456')
            self.assertEqual(resp.status_code, 404)

########### TESTS ON MESSAGE VIEWS: ADD MESSAGE ###########

    def test_add_message(self):
        """Can user add a message?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post("/messages/new", data={"text": "Hello"})
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.filter(Message.id != 999).first()
            self.assertEqual(msg.text, "Hello")

    def test_add_message_loggedin(self):
        """ Can user add a message if user is logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            
            resp = c.post('/messages/new', data={"text": "This is a message"})
            self.assertEqual(302, resp.status_code)

            msg = Message.query.filter(Message.id != 999).first()
            self.assertEqual(msg.text, "This is a message")

    def test_add_message_loggedout(self):
        """ Can user add a message if user is logged out?"""
        with self.client as c:
            resp = c.post('/messages/new', data={"text": "Hello World"}, follow_redirects=True)
            self.assertEqual(200, resp.status_code)
            self.assertIn("Access unauthorized.", str(resp.data))

    def test_add_message_invalid_user(self):
        """ Can user add a message if user is invalid?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 5684
        
            resp = c.post('/messages/new', data={"text": "This should not work"}, follow_redirects=True)
            self.assertEqual(200, resp.status_code)
            self.assertIn("Access unauthorized.", str(resp.data))

########### TESTS ON MESSAGE VIEWS: DELETE MESSAGE ###########

    def test_delete_message_loggedin(self):
        """ Can user delete a message if user is logged in?"""
        m = Message(
            id = 78546,
            text= "Message message, text text!",
            user_id = self.testuser_id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post(f'/messages/78546/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            m = Message.query.get(78546)
            self.assertIsNone(m)

    def test_delete_message_loggedout(self):
        """ Can user delete a message if user is logged out?"""
        m = Message(
            id = 456789,
            text= "Another message but it won't get deleted!",
            user_id = self.testuser_id
        )
        db.session.add(m)
        db.session.commit()
        with self.client as c:

            resp = c.post(f'/messages/456789/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))

            m = Message.query.get(456789)
            self.assertIsNotNone(m)

    def test_delete_message_unauthorized(self):
        """ Can logged in user delete another users message?"""
        u = User.signup(username="unauth",
                        email="unauth@unauth.com",
                        password="unauth123",
                        image_url=None)
        u.id = 941653

        m = Message(
            id = 674851,
            text= "Another message but it won't get deleted!",
            user_id = self.testuser_id
        )
        db.session.add_all([u, m])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 941653

            resp = c.post(f'/messages/674851/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))

            m = Message.query.get(674851)
            self.assertIsNotNone(m)