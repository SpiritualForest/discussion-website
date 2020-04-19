# Test the community_functions module
import unittest
from backend.database import community_functions
from backend.models import User, Community, db
from sqlalchemy import exc
from sqlalchemy.orm import exc as orm_exc
from test.helpers import setup_test_environment, create_test_user, create_test_community, cleanup

class TestCommunityFunctions(unittest.TestCase):
    setup_test_environment()
    
    ##### create_community(name, description, owner_user_id) tests ####
    
    def test_create_community(self):
        # Test the create_community() function
        # Expected exceptions:
        # exc.IntegrityError in case the unique constraint is violated due to duplicate communities
        # exc.FlushError if the owner user is a None object
        # AttributeError if trying to add a non-User object to the community
        user = create_test_user()
        community_functions.create_community(name="TestCommunity", description="For testing", owner_user_id=user.id)
        # Now verify that the community was created
        com_obj = Community.query.filter(Community.name == "TestCommunity").first()
        self.assertIsNotNone(com_obj)
        self.assertIn(user, com_obj.users)
        self.assertIn(user, com_obj.owners)
        # Clean up
        cleanup(Community, User)

    def test_create_community_non_existent_user(self):
        # Test the community with a user that doesn't exist
        self.assertRaises(orm_exc.FlushError, community_functions.create_community, name="TestCommunity", description="Testing", owner_user_id=100)

    def test_create_community_already_exists(self):
        # Create a community with a name that already exists in the database.
        # This should result in sqlalchemy.exc.IntegrityError due to a
        # violation of the unique constraint for the name column
        user = create_test_user()
        # Create a mock community without adding users
        test_com = create_test_community()
        name = test_com.name
        self.assertRaises(exc.IntegrityError, community_functions.create_community, name=name, description="Testing", owner_user_id=user.id)
        # Clean up
        db.session.rollback()
        cleanup(User, Community)
    
    #### join(user_id, community_id) tests ####

    def test_join(self):
        # a user joins the community
        user = create_test_user()
        community = create_test_community()
        community_functions.join(user.id, community.id)
        self.assertIn(user, community.users)
        # Cleanup
        cleanup(User, Community)

    def test_join_non_existent_community(self):
        # a user tries to join a non existent community
        # should raise AttributeError because community is None
        user = create_test_user()
        # Pass actual None
        self.assertRaises(AttributeError, community_functions.join, user.id, None)
        # Pass an ID that won't be in the database
        self.assertRaises(AttributeError, community_functions.join, user.id, -1)
        # Pass some weird not-None and not-int object - raises InterfaceError
        self.assertRaises(exc.InterfaceError, community_functions.join, user.id, [])
        # Cleanup
        cleanup(User)

    def test_join_non_existent_user(self):
        # call join() with a user_id of None, -1, and so forth.
        community = create_test_community()
        self.assertRaises(orm_exc.FlushError, community_functions.join, -1, community.id)
        self.assertRaises(exc.InterfaceError, community_functions.join, {}, community.id)
        # Cleanup
        cleanup(Community)

    #### leave(user_id, community_id) tests ####

    def test_leave(self):
        # Test that the leave() function clears the user from all the relationship groups
        user = create_test_user()
        community = create_test_community()
        # First add the user to all the relationship groups
        subgroups = ("users", "owners", "admins", "moderators")
        for subgroup in subgroups:
            obj = getattr(community, subgroup)
            obj.append(user)
        db.session.commit()
        # Now verify that the user is in there
        for subgroup in subgroups:
            obj = getattr(community, subgroup)
            self.assertIn(user, obj)
        # Now leave and then assert that the user isn't in any of groups
        community_functions.leave(user.id, community.id)
        for subgroup in subgroups:
            obj = getattr(community, subgroup)
            self.assertNotIn(user, obj)
        # Cleanup
        cleanup(Community, User)

    def test_leave_non_existent_community(self):
        # Test leave() with a non existent community
        user = create_test_user()
        self.assertRaises(AttributeError, community_functions.leave, user.id, None)
        self.assertRaises(AttributeError, community_functions.leave, user.id, -1)
        self.assertRaises(exc.InterfaceError, community_functions.leave, user.id, [])
        # Cleanup
        cleanup(User)

    def test_leave_non_existent_user(self):
        # Real community, None user
        community = create_test_community()
        self.assertRaises(ValueError, community_functions.leave, -1, community.id)
        self.assertRaises(ValueError, community_functions.leave, None, community.id)
        self.assertRaises(exc.InterfaceError, community_functions.leave, [], community.id)
        # Cleanup
        cleanup(Community)

    #### delete_community(community_id) tests ####

    def test_delete_community(self):
        community = create_test_community()
        cid = community.id
        user = create_test_user()
        community.users.append(user)
        community.admins.append(user)
        db.session.commit()
        # Now assert that the user has these relationships
        self.assertIn(community, user.communities)
        self.assertIn(community, user.admin)
        # Now delete the community and assert that the relationship have been deleted
        community_functions.delete_community(cid)
        self.assertNotIn(community, user.communities)
        self.assertNotIn(community, user.admin)
        # Assert that the community object is None
        community = Community.query.filter(Community.id == cid).first()
        self.assertIsNone(community)
        # Cleanup
        cleanup(User)

    def test_delete_community_non_existent_community(self):
        # Test delete_community() with None, -1, []
        community = create_test_community()
        self.assertRaises(AttributeError, community_functions.delete_community, None)
        self.assertRaises(AttributeError, community_functions.delete_community, -1)
        self.assertRaises(exc.InterfaceError, community_functions.delete_community, [])
        cleanup(Community)
