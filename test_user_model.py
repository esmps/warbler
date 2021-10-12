"""User model tests.
    to run these tests, copy and paste into your terminal:
    python -m unittest test_user_model.py
"""

import os
from unittest import TestCase
from models import db, User, Message, Follows
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
        u2 = User.signup("testuser2", "test2@gmail.com", "password", None)
        u1.id = 111
        u2.id = 222

        db.session.commit()

        u1 = User.query.get(u1.id)
        u2 = User.query.get(u2.id)

        self.u1 = u1
        self.uid1 = u1.id
        self.u2 = u2
        self.uid2 = u2.id

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
    

########### TESTS ON USER MODEL ###########

    def test_repr(self):
        """Does calling __repr__ on an User object work?"""
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        self.assertEqual(f"{u}", f"<User #{u.id}: {u.username}, {u.email}>")

    def test_user_model(self):
        """Test basic user model works"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
    
    def test_user_follows(self):
        """Test user follows works"""

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)

    def test_user_is_following(self):
        """Test user is_following works"""
         
        self.u1.following.append(self.u2)
        db.session.commit()
        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))


    def test_user_is_followed_by(self):    
        """Test user is_followed_by works"""

        self.u1.following.append(self.u2)
        db.session.commit()
        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))

########### TESTS ON USER MODEL: SIGN UP ###########

    def test_user_signup(self):
        """ Test for valid user signup"""

        user = User.signup("test123", "test123@gmail.com", "password123", None)
        user.id = 333
        db.session.commit()

        user = User.query.get(user.id)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "test123")
        self.assertEqual(user.email, "test123@gmail.com")
        self.assertNotEqual(user.password, "password123")
        self.assertTrue(user.password.startswith("$2b$"))

    def test_invalid_username(self):
        """ Test for invalid username signup"""

        user = User.signup(None, "test123@gmail.com", "password", None)
        self.assertRaises(IntegrityError, db.session.commit)

    def test_invalid_email(self):

        """ Test for invalid email signup"""
        user = User.signup("test123", None, "password", None)
        self.assertRaises(IntegrityError, db.session.commit)

    def test_invalid_password(self):

        """ Test for invalid password signup"""
        with self.assertRaises(ValueError):
            User.signup(None, "test123@gmail.com", None, None)
        
        with self.assertRaises(ValueError):
            User.signup(None, "test123@gmail.com", "", None)

########### TESTS ON USER MODEL: AUTHENTICATE ###########

    def test_user_login(self):
        """ Test for valid user login"""

        user = User.authenticate("testuser1", "password")

        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser1")
        self.assertEqual(user.email, "test1@gmail.com")
    
    def test_invalid_login(self):
        """ Tests for invalid user login"""

        user = User.authenticate("test99", "password")
        self.assertFalse(user)

        user = User.authenticate("testuser1", "badpassword")
        self.assertFalse(user)