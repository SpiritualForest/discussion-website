import unittest
from datetime import datetime, timedelta
from time import sleep # so we can delay some operations
from random import randint
from backend.token_expiration_manager import TokenExpirationManager

def strip_milliseconds(datetimeObj):
    year, month, day = datetimeObj.year, datetimeObj.month, datetimeObj.day
    hour, minute, second = datetimeObj.hour, datetimeObj.minute, datetimeObj.second
    return datetime(year, month, day, hour, minute, second)

class TestTokenExpirationManager(unittest.TestCase):
    def test_add_token(self):
        # Tokens set to expire a minute after being added, give or take < 5 seconds
        manager = TokenExpirationManager(session_timeout=timedelta(minutes=1), expiration_proximity=timedelta(seconds=5))
        tokens = ("t1", "t2", "t3", "t4")
        for token in tokens:
            manager.add_token(token, token)
        for token in tokens:
            self.assertEqual(manager.get_token_object(token), token)

        # Test that the expiration times exist
        for token in tokens:
            # They should be datetime objects, not None
            self.assertIsNotNone(manager.get_expiration_time(token))

        # Test that the expiration proximity has been set to 5 seconds
        for token in tokens:
            self.assertEqual(manager.expiration_proximity.total_seconds(), 5)
        
        # Test that the actual expiration times have been set to a minute from now
        for token in tokens:
            minute_from_now = datetime.utcnow() + timedelta(minutes=1)
            expiration_time = manager.get_expiration_time(token)
            self.assertEqual(expiration_time.year, minute_from_now.year)
            self.assertEqual(expiration_time.month, minute_from_now.month)
            self.assertEqual(expiration_time.day, minute_from_now.day)
            self.assertEqual(expiration_time.hour, minute_from_now.hour)
            self.assertEqual(expiration_time.minute, minute_from_now.minute)
            self.assertEqual(expiration_time.second, minute_from_now.second)

        # Test that all the tokens exist in the same expiration group
        expiration_time = manager.get_expiration_time("t1")
        self.assertEqual(len(manager.expirations[expiration_time]), 4)
        # Check that the tokens exist in the token_expiration_time dict
        for token in tokens:
            self.assertIn(token, manager.token_expiration_time)

    def test_update_expiration_time(self):
        manager = TokenExpirationManager(session_timeout=timedelta(seconds=3), expiration_proximity=timedelta(seconds=1))
        t1 = "t1"
        td3 = timedelta(seconds=3)
        manager.add_token(t1, t1)
        t1_expiration = strip_milliseconds(manager.get_expiration_time(t1))
        self.assertEqual(t1_expiration, strip_milliseconds(datetime.utcnow() + td3))

        # Now update the expiration time and check again
        manager.update_expiration_time(t1)
        self.assertEqual(strip_milliseconds(manager.get_expiration_time(t1)), strip_milliseconds(datetime.utcnow() + td3))
        
        # Wait 2 seconds, add another token and check that the two tokens are in different expiration groups
        t2 = "t2"
        print("\nSleeping 2 seconds")
        sleep(2)
        manager.add_token(t2, t2)
        exp_t1, exp_t2 = manager.get_expiration_time(t1), manager.get_expiration_time(t2)
        self.assertNotEqual(manager.get_expiration_time(t1), manager.get_expiration_time(t2))
        self.assertEqual(len(manager.expirations[exp_t1]), 1)
        self.assertEqual(len(manager.expirations[exp_t2]), 1)
        self.assertEqual(len(manager.expirations), 2)
        # Add another token, its expiration time should be the same as t2
        t3 = "t3"
        manager.add_token(t3, t3)
        self.assertEqual(len(manager.expirations[exp_t1]), 1)
        self.assertEqual(len(manager.expirations[exp_t2]), 2)        
        # Now sleep half a second and add another token. It should still be in the same group as t2 and t3
        print("Sleeping 0.5 seconds")
        sleep(0.5)
        t4 = "t4"
        manager.add_token(t4, t4)
        self.assertEqual(len(manager.expirations[exp_t2]), 3)
        # Wait 1 second and update t2's expiration time. It should move to its own new set
        print("Sleeping 1 second")
        sleep(1)
        manager.update_expiration_time(t2)
        t2_exp = manager.get_expiration_time(t2)
        self.assertEqual(strip_milliseconds(t2_exp), strip_milliseconds(datetime.utcnow() + timedelta(seconds=3)))
        self.assertEqual(len(manager.expirations[t2_exp]), 1)
        self.assertEqual(len(manager.expirations[manager.get_expiration_time(t3)]), 2)
        # Assert that t2_exp is equal to the value stored in the token_expiration_time dict
        self.assertEqual(manager.token_expiration_time[t2], t2_exp)

    def test_get_token_object(self):
        manager = TokenExpirationManager(session_timeout=timedelta(seconds=3), expiration_proximity=timedelta(seconds=1)) 
        t1 = "t1"
        manager.add_token(t1, {})
        t1_exp = manager.get_expiration_time(t1) # First expiration time
        # Now wait 1 second and then get the object
        print("\nSleeping 1 second")
        sleep(1)
        t1_obj = manager.get_token_object(t1)
        self.assertEqual(t1_obj, {})
        self.assertNotEqual(manager.get_expiration_time(t1), t1_exp)
        # Check that the expiration time was updated
        new_exp = strip_milliseconds(manager.get_expiration_time(t1))
        self.assertEqual(new_exp, strip_milliseconds(datetime.utcnow() + timedelta(seconds=3)))

    def test_expire_token(self):
        # Test manual token removal
        manager = TokenExpirationManager(session_timeout=timedelta(seconds=2), expiration_proximity=timedelta(seconds=1))
        t1 = "t1"
        manager.add_token(t1, t1)
        sleep(0.1)
        manager.expire_token(t1)
        self.assertEqual(len(manager.tokens), 0)
        self.assertEqual(len(manager.token_expiration_time), 0)
        # Add two tokens and expire one
        t2 = "t2"
        manager.add_token(t1, t1)
        manager.add_token(t2, t2)
        # Expire t1
        manager.expire_token(t1)
        self.assertEqual(len(manager.tokens), 1)
        self.assertEqual(len(manager.token_expiration_time), 1)
        self.assertEqual(len(manager.expirations), 1)
        self.assertIsNone(manager.get_token_object(t1))
        # Add more. They should all still be in the same group as t1
        t3, t4, t5 = "t3", "t4", "t5"
        manager.add_token(t3, t3)
        manager.add_token(t4, t4)
        manager.add_token(t5, t5)
        t5_exp = manager.get_expiration_time(t5)
        self.assertEqual(len(manager.expirations[t5_exp]), 4)
        manager.expire_token(t4)
        self.assertEqual(len(manager.expirations[t5_exp]), 3)
        self.assertIsNone(manager.get_token_object(t4))

    def test_purge_expired_tokens(self):
        # Test the mass expiration of entire groups of tokens
        manager = TokenExpirationManager(session_timeout=timedelta(seconds=2), expiration_proximity=timedelta(seconds=1))
        # Add 1000 tokens
        for i in range(1000):
            token = "token_{}".format(i)
            manager.add_token(token, token)
        # Wait 3 seconds and then call the purging method
        print("\nSleeping 3 seconds")
        sleep(3)
        manager.purge_expired_tokens()
        self.assertEqual(len(manager.tokens), 0)
        self.assertEqual(len(manager.expirations), 0)
        self.assertEqual(len(manager.token_expiration_time), 0)
        # Now add several thousand more in separate waves
        for i in range(10):
            for x in range(randint(1000, 10000)):
                token = "token_{}_{}".format(i, x)
                manager.add_token(token, token)
            print("Added {} tokens. Sleeping 1 second".format(x + 1))
            sleep(1)
        # Now after purging we should have 1 group left. That group didn't have enough time to expire
        self.assertEqual(len(manager.expirations), 10)
        manager.purge_expired_tokens()
        self.assertEqual(len(manager.expirations), 1)
        # Now wait another second and purge again
        sleep(1)
        manager.purge_expired_tokens()
        self.assertEqual(len(manager.expirations), 0)
        self.assertEqual(len(manager.tokens), 0)
        self.assertEqual(len(manager.token_expiration_time), 0)
