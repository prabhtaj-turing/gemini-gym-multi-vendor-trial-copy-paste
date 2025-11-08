# from linkedin import DB
import linkedin as LinkedinAPI


def reset_db():
    LinkedinAPI.DB.clear()
    LinkedinAPI.DB.update(
        {
            "people": {},
            "organizations": {},
            "organizationAcls": {},
            "posts": {},
            "next_person_id": 1,
            "next_org_id": 1,
            "next_acl_id": 1,
            "next_post_id": 1,
            "current_person_id": None,
        }
    )
