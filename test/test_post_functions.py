import unittest
from backend.database import post_functions
from backend.models import Post, User, Community, PostVote, db
from test.helpers import setup_test_environment, create_test_user, create_test_community, create_test_post, cleanup
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
        post = create_test_post(community, user)
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

    #### upvote(post_id) and downvote(post_id) ####
    # TODO: test it with erroneus input
    def test_upvote(self):
        user = create_test_user()
        community = create_test_community()
        post = create_test_post(community, user)
        # Upvote it and check the karma
        post_functions.upvote(user.id, post.id)
        # Should be 1
        self.assertEqual(post.karma, 1)
        vote_obj = PostVote.query.filter(PostVote.user_id == user.id, PostVote.post_id == post.id).first()
        self.assertIsNotNone(vote_obj)
        self.assertTrue(vote_obj.vote_type) # True vote_type means upvote
        self.assertIn(vote_obj, user.post_votes)
        self.assertIn(vote_obj, post.votes)
        self.assertEqual(len(user.post_votes), 1)
        self.assertEqual(len(post.votes), 1)
        # Cleanup
        cleanup(Post, PostVote, Community, User)

    def test_downvote(self):
        user = create_test_user()
        community = create_test_community()
        post = create_test_post(community, user)
        # Start at 0, should be downvoted to -1
        post_functions.downvote(user.id, post.id)
        self.assertEqual(post.karma, -1)
        # Get the vote object
        vote_obj = PostVote.query.filter(PostVote.user_id == user.id, PostVote.post_id == post.id).first()
        self.assertIsNotNone(vote_obj)
        self.assertFalse(vote_obj.vote_type) # Assert that it's a downvote type
        self.assertIn(vote_obj, user.post_votes)
        self.assertIn(vote_obj, post.votes)
        self.assertEqual(len(user.post_votes), 1)
        self.assertEqual(len(post.votes), 1)
        # Cleanup
        cleanup(Post, PostVote, Community, User)

    def test_unvote_with_upvote(self):
        # Upvote a post and then unvote it and verify that it has been unvoted
        user = create_test_user()
        community = create_test_community()
        post = create_test_post(community, user)
        # Now manually upvote the post and verify that it has been upvoted
        vote = PostVote(user_id=user.id, post_id=post.id, vote_type=True)
        user.post_votes.append(vote)
        post.votes.append(vote)
        post.karma += 1
        db.session.add(vote)
        db.session.commit()
        vote = PostVote.query.filter(PostVote.user_id == user.id, PostVote.post_id == post.id).first()
        self.assertIsNotNone(vote)
        self.assertTrue(vote.vote_type)
        self.assertEqual(post.karma, 1)
        self.assertEqual(len(user.post_votes), 1)
        self.assertEqual(len(post.votes), 1)
        # Now unvote it and verify it no longer exists and the post's karma is reset to 0
        post_functions.unvote(user.id, post.id)
        vote = PostVote.query.filter(PostVote.user_id == user.id, PostVote.post_id == post.id).first()
        self.assertIsNone(vote)
        self.assertEqual(post.karma, 0)
        self.assertEqual(len(user.post_votes), 0)
        self.assertEqual(len(post.votes), 0)
        # cleanup
        cleanup(Post, PostVote, Community, User)

    def test_unvote_with_downvote(self):
        # Downvote a post and then unvote it
        user = create_test_user()
        community = create_test_community()
        post = create_test_post(community, user)
        vote = PostVote(user_id=user.id, post_id=post.id, vote_type=False) # False means -1
        user.post_votes.append(vote)
        post.votes.append(vote)
        post.karma -= 1
        db.session.commit()
        # Now verify
        vote = PostVote.query.filter(PostVote.user_id == user.id, PostVote.post_id == post.id).first()
        self.assertIsNotNone(vote)
        self.assertEqual(post.karma, -1)
        # Unvote it
        post_functions.unvote(user.id, post.id)
        vote = PostVote.query.filter(PostVote.user_id == user.id, PostVote.post_id == post.id).first()
        self.assertIsNone(vote)
        self.assertEqual(post.karma, 0)
        self.assertEqual(len(user.post_votes), 0)
        self.assertEqual(len(post.votes), 0)
        # cleanup
        cleanup(Post, PostVote, Community, User)

    def test_upvote_non_existent_post(self):
        # Try to upvote a post that doesn't exist
        user = create_test_user()
        self.assertRaises(ValueError, post_functions.upvote, user.id, -1)
        self.assertRaises(ValueError, post_functions.upvote, user.id, None)
        self.assertRaises(exc.InterfaceError, post_functions.upvote, user.id, [])
        cleanup(User)

    def test_downvote_non_existent_post(self):
        user = create_test_user()
        self.assertRaises(ValueError, post_functions.downvote, user.id, -1)
        self.assertRaises(ValueError, post_functions.downvote, user.id, None)
        self.assertRaises(exc.InterfaceError, post_functions.downvote, user.id, [])
        cleanup(User)

    #### edit_post(post_id, title, body) ####

    def test_edit_post(self):
        user, community = create_test_user(), create_test_community()
        post = create_test_post(community, user)
        # Now edit the post
        edit_title, edit_body = "Edited title", "Edited body"
        post_functions.edit_post(post.id, edit_title, edit_body)
        self.assertEqual(post.title, edit_title)
        self.assertEqual(post.body, edit_body)
        # cleanup
        cleanup(Post, Community, User)

    def test_edit_post_non_existent_post(self):
        # Try to edit a post that doesn't exist.
        # We don't need the test community and user for this, because the post shouldn't exist.
        self.assertRaises(AttributeError, post_functions.edit_post, -1, "title", "body")
        self.assertRaises(AttributeError, post_functions.edit_post, None, "title", "body")
        self.assertRaises(exc.InterfaceError, post_functions.edit_post, [], "title", "body")

    def test_edit_post_empty_title_and_body(self):
        # Edit a post, but supply an empty title and body as parameters.
        user, community = create_test_user(), create_test_community()
        post = create_test_post(community, user)
        # Edit the post, but provide no title and then no body
        self.assertRaises(ValueError, post_functions.edit_post, post.id, None, "test")
        self.assertRaises(ValueError, post_functions.edit_post, post.id, "test", None)
        self.assertRaises(ValueError, post_functions.edit_post, post.id, "", "test")
        self.assertRaises(ValueError, post_functions.edit_post, post.id, "test", "")
        cleanup(Post, Community, User)
