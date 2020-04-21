# Discussion Website models file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy() # context initialized in main

# The various many-to-many user->community relationships
# Community memberships
memberships = db.Table("memberships",
        db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
        db.Column("community_id", db.Integer, db.ForeignKey("community.id"), primary_key=True)
        )
# Community bans
bans = db.Table("bans",
        db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
        db.Column("community_id", db.Integer, db.ForeignKey("community.id"), primary_key=True)
        )
# Community owners
owners = db.Table("owners",
        db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
        db.Column("community_id", db.Integer, db.ForeignKey("community.id"), primary_key=True)
        )
# Community admins
admins = db.Table("admins",
        db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
        db.Column("community_id", db.Integer, db.ForeignKey("community.id"), primary_key=True)
        )
# Community moderators
moderators = db.Table("moderators",
        db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
        db.Column("community_id", db.Integer, db.ForeignKey("community.id"), primary_key=True)
        )

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False) # hash
    salt = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String, unique=True) # nullable = False ?
    joined = db.Column(db.DateTime, default=datetime.utcnow)
    karma = db.Column(db.Integer, default=0) # User's rating based on their posts and comments
    # relationships
    posts = db.relationship("Post", backref="user") # user.posts; post.user
    comments = db.relationship("Comment", backref="user") # user.comments; comment.user
    # Now the various many-to-many user->community relationships
    # Memberships first: User.communities / Community.users
    communities = db.relationship("Community", secondary=memberships, lazy="subquery", backref=db.backref("users", lazy=True))
    # Groups in which the user is an owner: User.owner / Community.owners
    owner = db.relationship("Community", secondary=owners, lazy="subquery", backref=db.backref("owners", lazy=True))
    # Admin
    admin = db.relationship("Community", secondary=admins, lazy="subquery", backref=db.backref("admins", lazy=True))  
    # Moderator
    moderator = db.relationship("Community", secondary=moderators, lazy="subquery", backref=db.backref("moderators", lazy=True))
    # Banned: User.banned_on / Community.banned_users
    banned_on = db.relationship("Community", secondary=bans, lazy="subquery", backref=db.backref("banned_users", lazy=True))

    # This is just the names of the relationships for when we have to delete the user
    # or do something that requires this. Only done for extra modularity
    # and to avoid hard coding the string names inside database functions that require them.
    # We do not include the user's posts and comments here, because we want to keep those.
    # We will show [deleted] as the username when they're displayed.
    deletion_relationships = ("communities", "owner", "admin", "moderator", "banned_on")

    def __repr__(self):
        return "<User {}>".format(self.username)

class Community(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True) # Community name, "exjw"
    description = db.Column(db.String) # Community description, "a place for ex Jehovah's Witnesses"
    created = db.Column(db.DateTime, default=datetime.utcnow) # When the community was created
    # Community is private. Users must be approved by the mods to join.
    # Posts are not shown to users who aren't approved members, and posts cannot be created by non-members.
    is_private = db.Column(db.Boolean, default=False)
    # relationships
    posts = db.relationship("Post", backref="community")
    # When a user leaves the community, delete these relationships with the user
    user_departure_relationships = ("users", "owners", "admins", "moderators") # not bans 
    # When deleting the community, delete all relationships
    deletion_relationships = user_departure_relationships + ("banned_users", "posts")

    def __repr__(self):
        return "<Group {}>".format(self.name)

# TODO: edits
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey("community.id"), nullable=False)
    title = db.Column(db.String, nullable=False)
    karma = db.Column(db.Integer, default=0) # Post rating
    body = db.Column(db.Text, nullable=False) # Point to a filename that contains the post instead of storing it in the database?
    post_time = db.Column(db.DateTime, default=datetime.utcnow)
    is_pinned = db.Column(db.Boolean, default=False) # Post is pinned in the community index, showing at the top
    is_locked = db.Column(db.Boolean, default=False) # Post is locked - comments cannot be created, and votes cannot be cast
    # Relationship with comments
    # post_obj.comments; comment_obj.post
    comments = db.relationship("Comment", backref=db.backref("post", lazy=True), cascade="all, delete-orphan")

    def __repr__(self):
        return "<Post {}>".format(self.title)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.BigInteger, db.ForeignKey("post.id"), nullable=False)
    text = db.Column(db.Text) # Again, point to a filename that contains the comment instead?
    karma = db.Column(db.Integer, default=0) # Comment rating
    comment_time = db.Column(db.DateTime, default=datetime.utcnow)
    is_pinned = db.Column(db.Boolean, default=False) # comment is pinned in the thread, showing at the top
    # Parent relationships are defined in the parent classes (Post, User)

# FIXME: this is bad design. We'll keep it for now, but you should find a better way.
class PostVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False) # Voter
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False) # Post that was voted
    vote_type = db.Column(db.Boolean, nullable=False) # True is +1, False is -1
    voted_on = db.Column(db.DateTime, default=datetime.utcnow) # When
    # relationship with a user
    user = db.relationship("User", backref=db.backref("post_votes", lazy=True)) # postvote.user; user.post_votes
    post = db.relationship("Post", backref=db.backref("votes", lazy=True)) # postvote.post; post.votes

class CommentVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey("comment.id"), nullable=False)
    vote_type = db.Column(db.Boolean, nullable=False)
    voted_on = db.Column(db.DateTime, default=datetime.utcnow)
    # relationships etc
    user = db.relationship("User", backref=db.backref("comment_votes", lazy=True)) # commentvote.user; user.comment_votes
    comment = db.relationship("Comment", backref=db.backref("votes", lazy=True)) # commentvote.comment; comment.votes
