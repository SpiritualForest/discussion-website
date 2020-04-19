# Test the various User database functions
import unittest
from datetime import datetime
from backend.models import User, db, Community
from backend.database import user_functions
from passlib.hash import argon2
from sqlalchemy import exc
from sqlalchemy.orm import exc as orm_exc
from test.helpers import setup_test_environment, cleanup

# Set up the test environment
# Exceptions: self.assertRaises(ExpectedException, afunction, arg1, arg2)

# Special add_user method instead of the one in the helpers module because we need the hashing
def add_user():
    hash_config = user_functions.hash_config
    username = "Shit licker"
    password = "mypassword1234"
    salt = "the salt"
    # First register the user manually
    hash_result = argon2.using(**hash_config).hash(password + salt)
    user_obj = User(username=username, password=hash_result, salt=salt)
    db.session.add(user_obj)
    db.session.commit()
    return (username, password)

def create_test_community(name):
    com = Community(name=name, description="{} description".format(name))
    db.session.add(com)
    db.session.commit()
    return com

class TestUserFunctions(unittest.TestCase):
    setup_test_environment()
    def test_register_user(self):
        # register a user and verify its there
        username = "Some username"
        password = "password"
        email = "fuck@you.com"
        utcnow = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        user_functions.register_user(username, password, email)
        # Now verify manually
        user_obj = User.query.filter(User.username == username).first()
        self.assertIsNotNone(user_obj)
        self.assertEqual(user_obj.username, username)
        self.assertEqual(user_obj.id, 1)
        self.assertEqual(user_obj.email, email)
        self.assertEqual(user_obj.joined.strftime("%Y-%m-%d %H:%M:%S"), utcnow)
        # Cleanup
        cleanup(User)
    
    def test_register_user_not_unique(self):
        # Ensure that the register_user() function
        # raises exceptions when registering a user with
        # a non-unique username or email
        username = "Some username"
        password = "password"
        email = "fuck@you.com"
        user_functions.register_user(username, password, email)
        # Now try to register with the same username, but different email
        self.assertRaises(exc.IntegrityError, user_functions.register_user, username, password, "shit@off.com")
        # Rollback the database first
        db.session.rollback()
        self.assertRaises(exc.IntegrityError, user_functions.register_user, "shitname", password, email)
        db.session.rollback()
        # Cleanup
        cleanup(User)

    def test_register_user_unusual_password(self):
        # Ensure that register_user() raises a ValueError exception
        # when trying to register a using an empty password.
        # TypeError will be thrown when trying to register with a password 
        # that passes the "if not password" check, but isn't a unicode string.
        username = "Fuck off"
        email = "fuck@off.com"
        self.assertRaises(ValueError, user_functions.register_user, username, "", email)
        # Now try empty lists, empty dictionaries, etc. All should raise TypeError
        self.assertRaises(TypeError, user_functions.register_user, username, [], email)
        self.assertRaises(TypeError, user_functions.register_user, username, {}, email)
        self.assertRaises(TypeError, user_functions.register_user, username, None, email)
        # We don't have to rollback here because this exception is raised in the function before
        # trying to commit the changes to the database. 

    def test_register_user_unusual_username(self):
        # Test that exceptions are thrown when registering
        # with an empty username, None username, non-string username, etc.
        p = "password"
        e = "e@mail.com"
        # None username
        self.assertRaises(exc.IntegrityError, user_functions.register_user, None, p, e)
        db.session.rollback()
        # An empty string as a username should throw a ValueError
        self.assertRaises(ValueError, user_functions.register_user, "", p, e)
        # We do not rollback in this case because ValueError was raised before committing the changes.
        # Weird, non-string username
        self.assertRaises(exc.InterfaceError, user_functions.register_user, [], p, e)
        db.session.rollback()
        self.assertRaises(exc.InterfaceError, user_functions.register_user, {}, p, e)
        db.session.rollback()
        self.assertRaises(exc.InterfaceError, user_functions.register_user, {1, 2, 3}, p, e)
        db.session.rollback()

    def test_verify_user(self):
        username, password = add_user()
        # Now test that the passwords match
        self.assertTrue(user_functions.verify_user(username, password))
        # and don't match
        self.assertFalse(user_functions.verify_user(username, password + "shit"))
        # Cleanup
        cleanup(User)
        
    def test_verify_user_username_doesnt_exist(self):
        # Try to verify a user who doesn't exist
        # Should throw an AttributeError because the user object will be None
        username = "shit guy"
        password = "shit_password"
        self.assertRaises(AttributeError, user_functions.verify_user, username, password)
        # Now try some weird usernames
        self.assertRaises(exc.InterfaceError, user_functions.verify_user, {}, "shit")
        db.session.rollback()

    def test_verify_user_unusual_password(self):
        username, password = add_user()
        # argon2.verify() should raise TypeError in case the password isn't a unicode string
        self.assertRaises(TypeError, user_functions.verify_user, username, [])
        # Cleanup
        cleanup(User)

    def test_register_and_verify_user(self):
        username = "shitguy"
        password = "password"
        user_functions.register_user(username, password, "e@mail.com")
        self.assertTrue(user_functions.verify_user(username, password))
        # Cleanup
        cleanup(User)

    def test_delete_user(self):
        username, password = add_user()
        user_obj = User.query.filter(User.username == username).first()
        self.assertIsNotNone(user_obj)
        # Now delete
        user_functions.delete_user(user_obj.id)
        # Check that the user is None now
        user_obj = User.query.filter(User.username == username).first()
        self.assertIsNone(user_obj)

    def test_delete_user_none_user(self):
        # Test with None, IDs that don't exist, and weird objects
        self.assertRaises(AttributeError, user_functions.delete_user, None)
        self.assertRaises(AttributeError, user_functions.delete_user, -1)
        self.assertRaises(exc.InterfaceError, user_functions.delete_user, {})
        self.assertRaises(exc.InterfaceError, user_functions.delete_user, [])

    def test_delete_user_delete_community_relationships(self):
        # Test that when a user gets deleted, all their community relationships
        # are deleted before the user itself is deleted.
        username, password = add_user()
        user_obj = User.query.filter(User.username == username).first()
        communities = []
        for i in range(4):
            com = create_test_community("Test Community {}".format(i))
            communities.append(com)
            lists = (com.users, com.admins, com.owners, com.moderators, com.banned_users) 
            [list_object.append(user_obj) for list_object in lists]
            db.session.add(com)
        db.session.commit()
        # Now test that the user has been added to the community's relationship tables
        for com in communities:
            lists = (com.users, com.admins, com.owners, com.moderators, com.banned_users)
            # assert in
            [self.assertIn(user_obj, list_obj) for list_obj in lists]
        # Now delete the user and verify that the relationships no longer exist
        user_functions.delete_user(user_obj.id)
        for com in communities:
            lists = (com.users, com.admins, com.owners, com.moderators, com.banned_users)
            # assert not in
            [self.assertNotIn(user_obj, list_obj) for list_obj in lists]
