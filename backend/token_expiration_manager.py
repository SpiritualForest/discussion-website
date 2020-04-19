# Our automatic token expiration manager.
# Used to create sessions and CSRF tokens that expire automatically.
# But, can be used to store anything that should "expire" at a later time.
from datetime import datetime, timedelta

class TokenExpirationManager:
    def __init__(self, **kwargs):
        self.expirations = {} # <datetime>: set() of token_tag
        self.tokens = {} # token_tag: tokenObj
        self.token_expiration_time = {} # token_tag: <datetime> for the expirations group
        self.session_timeout = kwargs["session_timeout"] # datetime.timedelta() object
        self.expiration_proximity = kwargs["expiration_proximity"] #datetime.timedelta() object

    def add_token(self, token, tokenObj):
        self.tokens[token] = tokenObj
        self.token_expiration_time[token] = datetime.utcnow() + self.session_timeout
        self.update_expiration_time(token)

    def expire_token(self, token):
        # Remove an individual token manually
        expiration_time = self.token_expiration_time[token]
        self.expirations[expiration_time].remove(token)
        del self.token_expiration_time[token]
        del self.tokens[token]
        # Do not remove an empty expiration group set here,
        # it will be caught by purge_expired_tokens() and removed
        # next time that method is called.

    def update_expiration_time(self, token):
        # Call this method when a token has been used
        # or a new token has been created
        current_expiration = self.token_expiration_time[token]
        if self.expirations.get(current_expiration):
            # Older token, remove its previous expiration time
            self.expirations[current_expiration].remove(token)
        new_expiration = datetime.utcnow() + self.session_timeout
        for expiration_time in self.expirations:
            # We divide the tokens into various expiration sets based on the token's
            # initial expiration time's proximity to the group's expiration time.
            # Then when we want to remove expired tokens, we don't have to check every
            # individual token's expiration time. We just check if the entire group's expiration time
            # has elapsed, and then delete the whole group if it did.
            # This way we can save some CPU time and speed up our execution time, at the expense of memory usage.
            difference = (new_expiration - expiration_time).total_seconds()
            if difference < self.expiration_proximity.total_seconds():
                # Found an existing expiration group whose expiration time is close enough
                # to the token's personal expiration time.
                # The token will expire alongside the group it is in.
                self.expirations[expiration_time].add(token)
                self.token_expiration_time[token] = expiration_time
                break
        else:
            # No existing expiration group is sufficient for this token,
            # so we create a new one
            self.expirations[new_expiration] = {token}
            self.token_expiration_time[token] = new_expiration
    
    def get_expiration_time(self, token):
        return self.token_expiration_time.get(token)

    def get_token_object(self, token):
        # The token is active, which means we update its expiration
        # time to a later time, so that it won't suddenly expire
        # in the middle of a user's session.
        tokenObj = self.tokens.get(token)
        if tokenObj is None:
            # This token doesn't actually exist, return None
            return None
        self.update_expiration_time(token)
        return tokenObj

    def purge_expired_tokens(self):
        # Check all token groups whose expiration time has elapsed
        # and remove them
        removed_sets = []
        purged = 0
        for group_expiration_time in self.expirations:
            # All times are UTC
            utcnow = datetime.utcnow()
            if utcnow >= group_expiration_time:
                # Purge these sessions
                removed_sets.append(group_expiration_time)
                current_set = set(self.expirations[group_expiration_time])
                purged += len(current_set)
                for token in current_set:
                    # Remove the token from everywhere
                    self.expire_token(token)
        # Now remove all the empty sets from the expirations dict
        for removed_set in removed_sets:
            del self.expirations[removed_set]
        if purged > 0:
            print("Purged {} expired tokens from {} groups.".format(purged, len(removed_sets)))
