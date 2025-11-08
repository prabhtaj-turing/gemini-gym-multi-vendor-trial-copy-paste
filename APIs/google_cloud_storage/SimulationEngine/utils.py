from enum import Enum

class BucketPredefinedACL(str, Enum):
    """Enumeration of valid predefined ACL values for buckets as per Google Cloud Storage API."""

    authenticatedRead = "authenticatedRead"
    private = "private"
    projectPrivate = "projectPrivate"
    publicRead = "publicRead"
    publicReadWrite = "publicReadWrite"


class ObjectPredefinedDefaultACL(str, Enum):
    """Enumeration of valid predefined default object ACL values for buckets."""

    authenticatedRead = "authenticatedRead"
    bucketOwnerFullControl = "bucketOwnerFullControl"
    bucketOwnerRead = "bucketOwnerRead"
    private = "private"
    projectPrivate = "projectPrivate"
    publicRead = "publicRead"


# Convenience collections (for quick membership checks without importing Enum in callers)
ALLOWED_BUCKET_PREDEFINED_ACLS = {member.value for member in BucketPredefinedACL}
ALLOWED_OBJECT_PREDEFINED_DEFAULT_ACLS = {member.value for member in ObjectPredefinedDefaultACL}

# Valid IAM roles for Google Cloud Storage
VALID_IAM_ROLES = {
    "roles/storage.admin",
    "roles/storage.objectViewer",
    "roles/storage.objectCreator", 
    "roles/storage.objectAdmin",
    "roles/storage.legacyObjectReader",
    "roles/storage.legacyObjectOwner",
    "roles/storage.legacyBucketReader",
    "roles/storage.legacyBucketWriter",
    "roles/storage.legacyBucketOwner"
}
