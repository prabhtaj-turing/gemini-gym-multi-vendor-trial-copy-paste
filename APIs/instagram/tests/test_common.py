# instagram/tests/test_common.py

import instagram as InstagramAPI


def reset_db():
    """
    Set up the test environment before each test.
    Initializes the mock database. Instances are no longer needed
    for classes using static methods.
    """
    InstagramAPI.DB.clear()
    InstagramAPI.DB.update({"users": {}, "media": {}, "comments": {}})
