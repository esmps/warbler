"""Message model tests.

    to run these tests, copy and paste into your terminal:

   python -m unittest test_message_model.py

"""

import os
from unittest import TestCase
from models import db, User, Message, Follows, Likes
from sqlalchemy.exc import IntegrityError

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        u1 = User.signup("testuser1", "test1@gmail.com", "password", None)
        u1.id = 111

        db.session.commit()

        u1 = User.query.get(u1.id)

        self.u1 = u1
        self.uid1 = u1.id

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
    

########### TESTS ON USER MODEL ###########

    def test_message_model(self):
        """Test basic message model works"""

        m = Message(text="Here is some text", timestamp=None, user_id=self.uid1)

        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(self.u1.messages), 1)
        self.assertEqual(self.u1.messages[0].text, "Here is some text")

    def test_message_likes(self):
        """Test if message likes works"""

        message = Message(text="Like this message", user_id=self.uid1)

        user = User.signup("likeuser", "test111@gmail.com", "password", None)
        user.id = 123
        
        db.session.add_all([message, user])
        db.session.commit()

        user.likes.append(message)
        db.session.commit()

        likes = Likes.query.filter(Likes.user_id == user.id).all()
        self.assertEqual(len(likes), 1)
        self.assertEqual(len(user.likes), 1)
        self.assertEqual(likes[0].message_id, message.id)