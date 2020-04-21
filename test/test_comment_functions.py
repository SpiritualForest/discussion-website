import unittest
from backend.database import comment_functions
from backend.models import User, Community, Post, Comment, db
from test.helpers import setup_test_environment, cleanup
from test.helpers import create_test_user, create_test_community, create_test_post
from sqlalchemy import exc
from sqlalchemy.orm import exc as orm_exc

class TestUserFunctions(unittest.TestCase):
    setup_test_environment()
    
    #### create_comment(user_id, post_id, title, body) ####
    def test_create_comment(self):
        # Create a comment and verify it exists
        user = create_test_user()
        community = create_test_community()
        post = create_test_post(user, community)
        # Create it
        comment_functions.create_comment(user.id, post.id, "Testing comment!")
        # Verify that it exists
        comment = Comment.query.filter(Comment.id == 1).first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.post, post)
        self.assertEqual(comment.user, user)
        # Cleanup
        cleanup(User, Community, Post, Comment)

    def test_create_comment_non_existent_user(self):
        # Create a comment with a non existent user
        # We still have to create one real user at least,
        # so that we can create the post
        user = create_test_user()
        community = create_test_community()
        post = create_test_post(user, community)

        # Should raise ValueError when the user is None
        self.assertRaises(ValueError, comment_functions.create_comment, None, post.id, "Test comment")
        self.assertRaises(ValueError, comment_functions.create_comment, -1, post.id, "Test")
        # Should raise InterfaceError when passed some weird object like [], {}, etc
        self.assertRaises(exc.InterfaceError, comment_functions.create_comment, [], post.id, "Test comment")
        
        # Cleanup
        cleanup(User, Community, Post, Comment)

    def test_create_comment_non_existent_post(self):
        # Trying to create a comment on a post that doesn't exist
        user = create_test_user()
        # No need to create a community or post.
        self.assertRaises(AttributeError, comment_functions.create_comment, user.id, -1, "Test")
        self.assertRaises(AttributeError, comment_functions.create_comment, user.id, None, "Test")
        self.assertRaises(exc.InterfaceError, comment_functions.create_comment, user.id, [], "test")

        cleanup(User)

    #### delete_comment(comment_id) ####
    def test_delete_comment(self):
        user = create_test_user()
        community = create_test_community()
        post = create_test_post(user, community)
        # Manually create the comment
        comment = Comment(user_id=user.id, post_id=post.id, text="Fucking comment lol shit")
        db.session.add(comment)
        db.session.commit()
        cid = comment.id
        # Now verify first that it exists, and then delete it and verify that it doesn't
        comment = Comment.query.filter(Comment.id == cid).first()
        self.assertIsNotNone(comment)
        # Delete
        comment_functions.delete_comment(cid)
        # verify it's None
        comment = Comment.query.filter(Comment.id == cid).first()
        self.assertIsNone(comment)
        # Cleanup
        cleanup(Post, Community, User)

    def test_delete_comment_non_existent_comment(self):
        # Try to delete None, -1, []
        self.assertRaises(orm_exc.UnmappedInstanceError, comment_functions.delete_comment, None)
        self.assertRaises(orm_exc.UnmappedInstanceError, comment_functions.delete_comment, -1)
        self.assertRaises(exc.InterfaceError, comment_functions.delete_comment, [])
