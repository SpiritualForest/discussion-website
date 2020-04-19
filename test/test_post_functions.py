import unittest
from backend.database import post_functions
from backend.models import Post, User, Community, db
from test.helpers import setup_test_environment, create_test_user, create_test_community, cleanup
from sqlalchemy import exc
from sqlalchemy.orm import exc as orm_exc

class TestPostFunctions(unittest.TestCase):
    setup_test_environment() 
    #### create_post(user_id, community_id, post_title, post_body) tests ####

    def test_create_post(self):
        # Test create_post()
        user = create_test_user()
        community = create_test_community()
        community.users.append(user)
        db.session.commit()
        # Now create a post and verify that it exists
        title = "The first ever test post!"
        body = "Some long ass fucking text just for testing and all that shit lolcrap."
        post_functions.create_post(user.id, community.id, title, body)
        # Now verify
        post = Post.query.filter(User.id == user.id).first()
        self.assertIsNotNone(post)
        self.assertIn(post, user.posts)
        self.assertIn(post, community.posts)

        # Cleanup
        cleanup(Post, Community, User)

    def test_create_post_banned_user(self):
        # Test create_post() with a banned user as the author
        # the user should not be able to post, and the function
        # should raise PermissionError.
        user = create_test_user()
        community = create_test_community()
        community.banned_users.append(user)
        db.session.commit()
        # Test
        self.assertRaises(PermissionError, post_functions.create_post, user.id, community.id, "Title", "post body")
        # Cleanup
        cleanup(Community, User)

    def test_create_post_non_existent_user(self):
        # Test create_post() with a non existent user
        # Pass None, -1, and other weird stuff.
        # None and non existent IDs should result in ValueError
        # Weird stuff should result in InterfaceError
        community = create_test_community()
        #community_functions.create_post(None, community.id, "Shit", "lol")
        self.assertRaises(ValueError, post_functions.create_post, None, community.id, "Fuck", "you")
        self.assertRaises(ValueError, post_functions.create_post, -1, community.id, "Test", "post")
        self.assertRaises(exc.InterfaceError, post_functions.create_post, [], community.id, "Testing", "lol")
        # Cleanup
        cleanup(Community)

    def test_create_post_non_existent_community(self):
        # Test create_post() with a non existent community.
        # Should raise ValueError for int and None,
        # exc.InterfaceError for weird not-None and not-int objects
        user = create_test_user()
        self.assertRaises(ValueError, post_functions.create_post, user.id, None, "Title", "Body")
        self.assertRaises(ValueError, post_functions.create_post, user.id, -1, "Title", "Body")
        self.assertRaises(exc.InterfaceError, post_functions.create_post, user.id, [], "Title", "Body")
        # Cleanup
        cleanup(User)

    #### delete_post(post_id) tests ####

    def test_delete_post(self):
        # First, real user, real community, real post
        user = create_test_user()
        community = create_test_community()
        post = Post(user_id=user.id, community_id=community.id, title="A Test Post", body="The body of a test post")
        db.session.add(post)
        db.session.commit()
        pid = post.id
        # Assert that the post exists
        self.assertIsNotNone(Post.query.filter(Post.id == pid).first())
        # Delete and assert that the post doesn't exist
        post_functions.delete_post(pid)
        self.assertIsNone(Post.query.filter(Post.id == pid).first())
        # Cleanup community and user
        cleanup(Community, User)

    def test_delete_post_non_existent_post(self):
        # Nothing is real in this one because we need the post to not exist.
        # Try with None, -1, []
        # None and -1 should get UnmappedInstanceError, [] should get the standard InterfaceError
        self.assertRaises(orm_exc.UnmappedInstanceError, post_functions.delete_post, None)
        self.assertRaises(orm_exc.UnmappedInstanceError, post_functions.delete_post, -1)
        self.assertRaises(exc.InterfaceError, post_functions.delete_post, [])
