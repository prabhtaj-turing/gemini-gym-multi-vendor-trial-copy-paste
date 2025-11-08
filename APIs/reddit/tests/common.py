import reddit as RedditAPI


def reset_db():
    """
    Set up the test environment before each test.
    Initializes the mock database. Instances are no longer needed
    for classes using static methods.
    """
    RedditAPI.DB.clear()
    RedditAPI.DB.update(
        {
            "accounts": {},
            "announcements": [],
            "captcha_needed": False,
            "collections": {},
            "comments": {},
            "emoji": {},
            "flair": {},
            "links": {},
            "listings": {},  # Keep if needed by any method logic
            "live_threads": {},
            "messages": {},
            "misc_data": {},  # Keep if needed by any method logic
            "moderation": {},  # Keep if needed by any method logic
            "modmail": {},  # Keep if needed by any method logic
            "modnotes": {},
            "multis": {},
            "search_index": {},  # Keep if needed by any method logic
            "subreddits": {},
            "users": {},
            "widgets": {},
            "wiki": {},
        }
    )
