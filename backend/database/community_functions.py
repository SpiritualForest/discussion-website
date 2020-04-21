from backend.models import Community, User, db
from sqlalchemy import exc
from sqlalchemy.orm import exc as orm_exc

# NOTE: we only have to call db.session.rollback() to 
# rollback changes that occurred when trying to commit changes to the database.
# Other Python exceptions like TypeError, ValueError, and so forth, do not require a rollback,
# as they usually occur at a stage before trying to commit changes.

# NOTE: we use exception handling to handle errors
# All these functions require a user to be logged in
# before they are called, so the user_id parameters
# are guaranteed to be of a validated, logged in user.
# Still check for orm_exc.FlushError just in case we missed something earlier on.
# exc.InterfaceError can occur before committing changes to the database if the object
# cannot be mapped to some SQL type. For example, a Python list [] object will cause this exception to be raised.

def create_community(name, description, owner_user_id):
    # Create a community <name> with <description>
    # and set the the user whose ID is supplied as the owner
    community = Community(name=name, description=description)
    user_obj = User.query.filter(User.id == owner_user_id).first()
    # Will raise AttributeError if the user is not None, but is some other type of object like a string or int.
    community.users.append(user_obj)
    community.owners.append(user_obj)
    # Committing the changes will raise IntergrityError
    # if a community with this name already exists in the database.
    # It will raise FlushError if the user object is None.
    try:
        db.session.add(community)
        db.session.commit()
    except (exc.IntegrityError, orm_exc.FlushError) as e:
        # Something went wrong, rollback the changes
        # and re-raise the exception so that we can actually
        # inform the user of the failure.
        db.session.rollback()
        raise e

def delete_community(community_id):
    # delete the community
    # first we gotta remove all the community->user relationships
    # if community_id is [], set(), {}, etc, will raise exc.InterfaceError
    community = Community.query.filter(Community.id == community_id).first()
    for relationship in Community.deletion_relationships:
        # if community is None, will raise AttributeError
        list_obj = getattr(community, relationship)
        list_obj.clear()
    # Now that all the relationships have been deleted,
    # we delete the community itself
    db.session.delete(community)
    db.session.commit()

def add_user(user_id, community_id, key):
    # Generalized function to append a user object to a community list object.
    # The following attributes are available:
    # users, moderators, admins, owners, bans
    user_obj = User.query.filter(User.id == user_id).first()
    community_obj = Community.query.filter(Community.id == community_id).first()
    list_object = getattr(community_obj, key) # raises AttributeError if not found
    list_object.append(user_obj)
    try:
        db.session.commit()
    except (orm_exc.FlushError, exc.InterfaceError):
        # FlushError: user was None
        # InterfaceError: user_obj was some object that couldn't be mapped to an SQL type
        # AttributeError: raised on list_object.append() if the user was some non-user object, but not None
        db.session.rollback()
        raise

def delete_user(user_id, community_id, key):
    # Generalized function like add_user(), but for removal of users from lists.
    user_obj = User.query.filter(User.id == user_id).first() # Raises InterfaceError if user_id is some weird object
    community_obj = Community.query.filter(Community.id == community_id).first()
    list_object = getattr(community_obj, key) # raises AttributeError if not found
    try:
        # .remove() raises ValueError in case the user isn't in the list
        list_object.remove(user_obj)
        db.session.commit()
    except orm_exc.FlushError:
        db.session.rollback()
        raise

def join(user_id, community_id):
    # the user with <user_id> joins the community <community_id>
    # apparently if relationship already exists,
    # nothing happens and no error occurs, the user simply isn't added again.
    add_user(user_id, community_id, "users")

# FIXME: this can potentially render the group without any owners
# Make this function not callable without explicit confirmation from the user
# if they are a mod, admin, or owner of the group.
def leave(user_id, community_id):
    # AttributeError if community is None
    for relationship in Community.user_departure_relationships:
        # Remove the user from all other subgroups except bans
        delete_user(user_id, community_id, relationship)

def ban_user(user_id, community_id):
    # This should not be callable if the banning user
    # is not a moderator, admin, or owner in the group.
    # Trying to access .banned_users will raise AttributeError if community is None
    add_user(user_id, community_id, "banned_users")

def unban_user(user_id, community_id):
    # Should not be callable if the user is not 
    # a mod/admin/owner in the group
    # .banned_users will raise AttributeError if community is None
    delete_user(user_id, community_id, "banned_users")

def add_moderator(user_id, community_id):
    add_user(user_id, community_id, "moderators")

def add_admin(user_id, community_id):
    add_user(user_id, community_id, "admins")

def delete_moderator(user_id, community_id):
    delete_user(user_id, community_id, "moderators")

def delete_admin(user_id, community_id):
    delete_user(user_id, community_id, "admins")

# TODO: add_owner()
