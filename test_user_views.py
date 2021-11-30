"""User View tests.
    to run these tests, copy and paste into your terminal:
    FLASK_ENV=production python -m unittest test_user_views.py
"""

import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database)

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        self.client = app.test_client()

        # Set up user1
        self.testuser1 = User.signup(username="testuser1",
                                    email="test1@test.com",
                                    password="testuser1",
                                    image_url=None)
        self.testuser1_id = 123456
        self.testuser1.id = self.testuser1_id

        # Set up user2
        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None)
        self.testuser2_id = 654321
        self.testuser2.id = self.testuser2_id

        # Set up user3 and 4
        self.testuser3 = User.signup(username="qwerty",
                                    email="qwerty@test.com",
                                    password="qwerty",
                                    image_url=None)
        self.testuser4 = User.signup(username="warbler",
                                    email="warbler@test.com",
                                    password="warbler",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

########### TESTS ON USER VIEWS: SIGNUP/LOGIN ###########

    def test_user_signup(self):
        """Does user signup route work with valid credentials?"""
        with self.client as c:
            resp = c.post('/signup', data={"username": "signmeup",
                                            "password": "pass123",
                                            "email": "signup@test.com",
                                            "image_url": None}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@signmeup", str(resp.data))

            u = User.query.filter_by(username = "signmeup").first()
            with c.session_transaction() as sess:
                self.assertEqual(sess[CURR_USER_KEY], u.id)

    def test_user_invalid_signup(self):
        """Does user signup route work with repeat username?"""
        with self.client as c:
            resp = c.post('/signup', data={"username": "testuser1",
                                            "password": "pass123",
                                            "email": "signup@test.com",
                                            "image_url": None})
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Username already taken", str(resp.data))

    def test_user_login(self):
        """Does user login route work with valid credentials?"""
        with self.client as c:
            resp = c.post('/login', data={"username":"testuser1",
                                        "password":"testuser1"},
                                        follow_redirects=True)
            with c.session_transaction() as sess:
                self.assertEqual(sess[CURR_USER_KEY], 123456)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser1", str(resp.data))
            self.assertIn("Hello, testuser1!", str(resp.data))

    def test_user_login_invalid_password(self):
        """Does user signup route work with invalid password?"""
        with self.client as c:
            resp = c.post('/login', data={"username":"testuser1",
                                        "password":"testuser2"})
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid credentials", str(resp.data))

    def test_user_login_invalid_username(self):
        """Does user signup route work with invalid username?"""
        with self.client as c:
            resp = c.post('/login', data={"username":"userdoesnotexist",
                                        "password":"testuser1"})
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid credentials", str(resp.data))

########### TESTS ON USER VIEWS: SHOW USERS ###########

    def test_show_users(self):
        """ Can user see list of all users"""
        with self.client as c:
            resp = c.get('/users')
            self.assertEqual(resp.status_code, 200)

            self.assertIn("@testuser1", str(resp.data))
            self.assertIn("@testuser2", str(resp.data))
            self.assertIn("@qwerty", str(resp.data))
            self.assertIn("@warbler", str(resp.data))

    def test_show_users_search(self):
        """ Can user see list of users with query from search bar?"""
        with self.client as c:
            resp = c.get('/users?q=test')
            self.assertEqual(resp.status_code, 200)

            self.assertIn("@testuser1", str(resp.data))
            self.assertIn("@testuser2", str(resp.data))

            self.assertNotIn("@qwerty", str(resp.data))
            self.assertNotIn("@warbler", str(resp.data))

########### TESTS ON USER VIEWS: SHOW USER PROFILE ###########

    def test_show_other_user_profile(self):
        """Can user see other users profile?"""
        with self.client as c:
            resp = c.get(f'/users/{self.testuser2_id}')
            self.assertEqual(resp.status_code, 200)

            self.assertIn("@testuser2", str(resp.data))

    def test_show_other_user_profile_invalid(self):
        """Can user see an invalid users profile?"""
        with self.client as c:
            resp = c.get('/users/9845456')
            self.assertEqual(resp.status_code, 404)

########### TESTS ON USER VIEWS: USER FOLLOWING/FOLLOWERS ###########

    def test_user_following_valid(self):
        """Can user view other user following list while logged in? """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1_id
                self.testuser2.following.append(self.testuser3)
                self.testuser2.following.append(self.testuser4)
                db.session.commit()

            resp = c.get(f'/users/{self.testuser2_id}/following')
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@qwerty", str(resp.data))
            self.assertIn("@warbler", str(resp.data))
            self.assertNotIn("@testuser1", str(resp.data))

    def test_user_following_unauthorized(self):
        """Can user view other user following list while logged out? """
        with self.client as c:
            self.testuser2.following.append(self.testuser3)
            db.session.commit()

            resp = c.get(f'/users/{self.testuser2_id}/following', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))

    def test_user_followers_valid(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1_id
                self.testuser3.following.append(self.testuser2)
                self.testuser4.following.append(self.testuser2)
                db.session.commit()

            resp = c.get(f'/users/{self.testuser2_id}/followers')
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@qwerty", str(resp.data))
            self.assertIn("@warbler", str(resp.data))
            self.assertNotIn("@testuser1", str(resp.data))

    def test_user_followers_unauthorized(self):
        """Can user view other user following list while logged out? """
        with self.client as c:
            self.testuser2.followers.append(self.testuser3)
            db.session.commit()

            resp = c.get(f'/users/{self.testuser2_id}/followers', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))

########### TESTS ON USER VIEWS: UN/FOLLOW USERS ###########

    def test_user_follow_valid(self):
        """Can user follow other user while logged in? """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1_id

            resp = c.post(f'/users/follow/{self.testuser2_id}', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@qwerty", str(resp.data))
            self.assertNotIn("@warbler", str(resp.data))
            self.assertIn("@testuser2", str(resp.data))

    def test_user_follow_unauthorized(self):
        """Can user follow other user while logged out? """
        with self.client as c:
            resp = c.post(f'/users/follow/{self.testuser2_id}', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))

    def test_user_unfollow_valid(self):
        """Can user unfollow other user while logged in? """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1_id
                self.testuser1.following.append(self.testuser2)
                self.testuser1.following.append(self.testuser4)
                db.session.commit()

            resp = c.post(f'/users/stop-following/{self.testuser2_id}', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@testuser2", str(resp.data))
            self.assertIn("@warbler", str(resp.data))

    def test_user_follow_unauthorized(self):
        """Can user unfollow other user while logged out? """
        with self.client as c:
            resp = c.post(f'/users/stop-following/{self.testuser2_id}', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))
        
########### TESTS ON USER VIEWS: EDIT USER PROFILE ###########

    def test_edit_user_profile(self):
        """Can user edit own profile?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1_id

            resp = c.post('/users/profile', data={"password": "testuser1",
                                            "bio":"This is a test bio!",
                                            "location": "San Francisco, CA"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser1", str(resp.data))
            self.assertIn("This is a test bio!", str(resp.data))
            self.assertIn("San Francisco, CA", str(resp.data))
            self.assertIn("Successfully updated profile!", str(resp.data))
    
    def test_edit_user_profile_invalid_password(self):
        """Can user edit own profile with invalid password?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1_id

            resp = c.post('/users/profile', data={"password": "testuser2",
                                            "bio":"This is a test bio!",
                                            "location": "San Francisco, CA"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid password.", str(resp.data))

    def test_edit_user_profile_unauthorized(self):
        """Can user edit profile logged out?"""
        with self.client as c:
            resp = c.post('/users/profile', data={"password": "testuser1",
                                            "bio":"This is a test bio!",
                                            "location": "San Francisco, CA"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))

########### TESTS ON USER VIEWS: DELETE USER PROFILE ###########

    def test_delete_user(self):
        """Can user delete profile?"""
        u = User.signup("tempuser", "tempuser@test.com", "tempuser123", None)
        u.id = 8521114
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 8521114
            resp = c.post('/users/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Successfully deleted account.", str(resp.data))

    def test_delete_user_unauthorized(self):
        """Can user delete profile logged out?"""
        with self.client as c:
            resp = c.post('/users/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))

########### TESTS ON USER VIEWS: USER LIKES ###########

    def test_list_liked_messages(self):
        """ Can user see liked messages of other users? """
        msg = Message(id = 9874544,
                    text= "Message message, text text!",
                    user_id = self.testuser2_id)
        db.session.add(msg)
        db.session.commit()

        self.testuser3.likes.append(msg)
        db.session.commit()

        with self.client as c:
            resp = c.get(f'/users/{self.testuser3.id}/likes')
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Message message, text text!", str(resp.data))
            self.assertIn("@testuser2", str(resp.data))
    
    def test_list_liked_messages_404(self):
        """Can user view an invalid users likes?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1_id

            resp = c.get('/users/99999999/likes')
            self.assertEqual(resp.status_code, 404)

    def test_like_message(self):
        """Can user like a message while logged in? """
        msg = Message(id = 341579,
                    text= "Another test message! Gasp!",
                    user_id = self.testuser1_id)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser2_id

            # First like the messsage
            resp = c.post('/users/add_like/341579', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            # Then go to users liked messages to see if it's there
            resp = c.get(f'/users/{self.testuser2_id}/likes')
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Another test message! Gasp!", str(resp.data))
            self.assertIn("@testuser1", str(resp.data))
            

    def test_like_own_message(self):
        """Can user like their own message? """
        msg = Message(id = 5846137,
                    text= "Another test message! Gasp!",
                    user_id = self.testuser1_id)
        db.session.add(msg)
        db.session.commit()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1_id
            resp = c.post('/users/add_like/5846137', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("You cannot like your own message.", str(resp.data))

    def test_like_message_unauthorized(self):
        """Can user like a message while logged out? """
        msg = Message(id = 341579,
                    text= "Another test message! Gasp!",
                    user_id = self.testuser1_id)
        db.session.add(msg)
        db.session.commit()
        
        with self.client as c:
            resp = c.post('/users/add_like/341579', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))