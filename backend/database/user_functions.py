# Handles the various user functions, such as registering a user
# logging in, deleting a user, changing settings, and so forth.

from backend.models import User, db
from passlib.hash import argon2
from random import choice  # for salt
from string import ascii_letters, digits, punctuation  # for salt
from sqlalchemy import exc

# sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: user.salt
# sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: user.email
# SQL Alchemy raises InterfaceError in case it is unable to map data to their columns, such as [] for string.

# NOTE: remember to call db.session.rollback() in the case of SQLAlchemy exceptions.

hash_config = {
        "salt_size": 64,
        "digest_size": 256,
        "rounds": 4,
        }

def generate_salt(length=128):
    characters = ascii_letters + digits + punctuation
    salt = "".join([choice(characters) for n in range(length)])
    return salt

def register_user(username, password, email):
    # Generate a random salt
    if password == "":
        # Check for password explicitly because
        # if we don't do this, and concatenate it with the salt,
        # the salt will become the hashed password.
        raise ValueError("password is empty")
    if username == "":
        # An empty string is technically still a string, and
        # will be treated as a valid value for the column by the database.
        raise ValueError("username is empty")
    salt = generate_salt()
    try:
        hash_result = argon2.using(**hash_config).hash(password + salt)
    except TypeError:
        # If the password is a non-string object, this exception will be raised.
        # For example, if the password argument is a list, or an int, or float, etc.
        raise TypeError("Password must be a unicode string.")

    # Now add the stuff
    # If any of the parameters passed the User() are some weird objects like [], {},
    # and so forth, exc.InterfaceError will be raised, because SQLAlchemy won't be able to bind
    # those data types to an SQL data type.
    # We do NOT have to rollback the database when this exception occurs.
    user_obj = User(username=username, password=hash_result, salt=salt, email=email)
    db.session.add(user_obj)

    # Committing the changes will raise IntegrityError in case the required fields are None,
    # or if they are duplicates in fields that require the unique constraint.
    # When this error occurs, we do have to rollback the database.
    try:
        db.session.commit()
    except exc.IntegrityError:
        db.session.rollback()
        raise

def verify_user(username, password):
    # Verify the user's password
    # argon2.verify(password, argon2_hash)
    # if the user doesn't exist, trying to access its attributes will throw an AttributeError
    user_obj = User.query.filter(User.username == username).first()
    salt = user_obj.salt
    hashed_password = user_obj.password  # the hash
    # If the password isn't a string object, argon2.verify() will throw a TypeError
    verified = argon2.using(**hash_config).verify(password + salt, hashed_password)
    return verified

def delete_user(user_id):
    # delete a user from the database
    # Since only the authenticated user is able to delete their own account,
    # we use user_id here instead of username, because we can get the user_id
    # also from the session handler, indicating that the user wants to delete their own account.
    # User.query.filter() will raise exc.InterfaceError if the user_id is some weird object like an empty dict or list
    user_obj = User.query.filter(User.id == user_id).first()
    for relationship in user_obj.deletion_relationships:
        # Get all the relationships the user is linked to and clear them.
        relationship_list_obj = getattr(user_obj, relationship)
        relationship_list_obj.clear()
    # Community relationships have been deleted, now delete the user itself
    db.session.delete(user_obj)
    db.session.commit()
