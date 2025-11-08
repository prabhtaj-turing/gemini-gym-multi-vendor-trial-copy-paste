from __future__ import annotations

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, validator
from google_cloud_storage.SimulationEngine.utils import VALID_IAM_ROLES

# --- Enums ---

class BucketStorageClass(str, Enum):
    """Valid storage class values for buckets."""
    STANDARD = "STANDARD"
    NEARLINE = "NEARLINE" 
    COLDLINE = "COLDLINE"
    ARCHIVE = "ARCHIVE"
    MULTI_REGIONAL = "MULTI_REGIONAL"
    REGIONAL = "REGIONAL"
    DURABLE_REDUCED_AVAILABILITY = "DURABLE_REDUCED_AVAILABILITY"

class BucketRPO(str, Enum):
    """Valid RPO (Recovery Point Objective) values."""
    DEFAULT = "DEFAULT"
    ASYNC_TURBO = "ASYNC_TURBO"

class BucketProjection(str, Enum):
    """Valid projection values for bucket responses."""
    FULL = "full"
    NO_ACL = "noAcl"

class PredefinedBucketAcl(str, Enum):
    """Valid predefined ACL values for buckets."""
    AUTHENTICATED_READ = "authenticatedRead"
    PRIVATE = "private"
    PROJECT_PRIVATE = "projectPrivate"
    PUBLIC_READ = "publicRead"
    PUBLIC_READ_WRITE = "publicReadWrite"

class PredefinedDefaultObjectAcl(str, Enum):
    """Valid predefined default object ACL values."""
    AUTHENTICATED_READ = "authenticatedRead"
    BUCKET_OWNER_FULL_CONTROL = "bucketOwnerFullControl"
    BUCKET_OWNER_READ = "bucketOwnerRead"
    PRIVATE = "private"
    PROJECT_PRIVATE = "projectPrivate"
    PUBLIC_READ = "publicRead"

class LifecycleActionType(str, Enum):
    """Valid lifecycle action types."""
    DELETE = "Delete"
    SET_STORAGE_CLASS = "SetStorageClass"
    ABORT_INCOMPLETE_MULTIPART_UPLOAD = "AbortIncompleteMultipartUpload"

class PublicAccessPrevention(str, Enum):
    """Valid public access prevention values."""
    INHERITED = "inherited"
    ENFORCED = "enforced"

class IpFilterMode(str, Enum):
    """Valid IP filter mode values."""
    ENABLED = "Enabled"
    DISABLED = "Disabled"

# --- Nested Models ---

class BucketBilling(BaseModel):
    """Bucket billing configuration."""
    requesterPays: Optional[bool] = False

    class Config:
        extra = "forbid"

class CorsConfiguration(BaseModel):
    """CORS configuration for buckets."""
    maxAgeSeconds: Optional[int] = None
    method: Optional[List[str]] = None
    origin: Optional[List[str]] = None
    responseHeader: Optional[List[str]] = None

    class Config:
        extra = "forbid"

class CustomPlacementConfig(BaseModel):
    """Custom placement configuration for dual regions."""
    dataLocations: List[str]

    class Config:
        extra = "forbid"

class HierarchicalNamespace(BaseModel):
    """Hierarchical namespace configuration."""
    enabled: Optional[bool] = False

    class Config:
        extra = "forbid"

class UniformBucketLevelAccess(BaseModel):
    """Uniform bucket level access configuration."""
    enabled: Optional[bool] = False
    lockedTime: Optional[str] = None

    class Config:
        extra = "forbid"

class BucketPolicyOnly(BaseModel):
    """Bucket policy only configuration (legacy)."""
    enabled: Optional[bool] = False
    lockedTime: Optional[str] = None

    class Config:
        extra = "forbid"

class IamConfiguration(BaseModel):
    """IAM configuration for buckets."""
    uniformBucketLevelAccess: Optional[UniformBucketLevelAccess] = None
    bucketPolicyOnly: Optional[BucketPolicyOnly] = None
    publicAccessPrevention: Optional[PublicAccessPrevention] = None

    class Config:
        extra = "forbid"

class PublicNetworkSource(BaseModel):
    """Public network source configuration for IP filtering."""
    allowedIpCidrRanges: Optional[List[str]] = None

    class Config:
        extra = "forbid"

class VpcNetworkSource(BaseModel):
    """VPC network source configuration for IP filtering."""
    network: str
    allowedIpCidrRanges: Optional[List[str]] = None

    class Config:
        extra = "forbid"

class IpFilter(BaseModel):
    """IP filter configuration."""
    mode: Optional[IpFilterMode] = None
    publicNetworkSource: Optional[PublicNetworkSource] = None
    vpcNetworkSources: Optional[List[VpcNetworkSource]] = None
    allowCrossOrgVpcs: Optional[bool] = None
    allowAllServiceAgentAccess: Optional[bool] = None

    class Config:
        extra = "forbid"

class LifecycleAction(BaseModel):
    """Lifecycle rule action."""
    type: LifecycleActionType
    storageClass: Optional[BucketStorageClass] = None

    class Config:
        extra = "forbid"
        use_enum_values = True

class LifecycleCondition(BaseModel):
    """Lifecycle rule condition."""
    age: Optional[int] = None
    createdBefore: Optional[str] = None
    customTimeBefore: Optional[str] = None
    daysSinceCustomTime: Optional[int] = None
    daysSinceNoncurrentTime: Optional[int] = None
    isLive: Optional[bool] = None
    matchesPattern: Optional[str] = None
    matchesPrefix: Optional[List[str]] = None
    matchesSuffix: Optional[List[str]] = None
    matchesStorageClass: Optional[List[BucketStorageClass]] = None
    noncurrentTimeBefore: Optional[str] = None
    numNewerVersions: Optional[int] = None

    class Config:
        extra = "forbid"
        use_enum_values = True

class LifecycleRule(BaseModel):
    """Lifecycle management rule."""
    action: LifecycleAction
    condition: LifecycleCondition

    class Config:
        extra = "forbid"

class Lifecycle(BaseModel):
    """Lifecycle configuration."""
    rule: Optional[List[LifecycleRule]] = None

    class Config:
        extra = "forbid"

class Autoclass(BaseModel):
    """Autoclass configuration."""
    enabled: Optional[bool] = False
    toggleTime: Optional[str] = None
    terminalStorageClass: Optional[BucketStorageClass] = None
    terminalStorageClassUpdateTime: Optional[str] = None

    class Config:
        extra = "forbid"
        use_enum_values = True

class Versioning(BaseModel):
    """Versioning configuration."""
    enabled: Optional[bool] = False

    class Config:
        extra = "forbid"

class Website(BaseModel):
    """Website configuration."""
    mainPageSuffix: Optional[str] = None
    notFoundPage: Optional[str] = None

    class Config:
        extra = "forbid"

class Logging(BaseModel):
    """Logging configuration."""
    logBucket: Optional[str] = None
    logObjectPrefix: Optional[str] = None

    class Config:
        extra = "forbid"

class RetentionPolicy(BaseModel):
    """Retention policy configuration."""
    effectiveTime: Optional[str] = None
    isLocked: Optional[bool] = False
    retentionPeriod: Optional[str] = None

    class Config:
        extra = "forbid"

class ObjectRetention(BaseModel):
    """Object retention configuration."""
    mode: Optional[str] = None

    class Config:
        extra = "forbid"

class SoftDeletePolicy(BaseModel):
    """Soft delete policy configuration."""
    retentionDurationSeconds: Optional[str] = None
    effectiveTime: Optional[str] = None

    class Config:
        extra = "forbid"

class EncryptionConfiguration(BaseModel):
    """Encryption configuration."""
    defaultKmsKeyName: Optional[str] = None

    class Config:
        extra = "forbid"

class Owner(BaseModel):
    """Bucket owner information."""
    entity: Optional[str] = None
    entityId: Optional[str] = None

    class Config:
        extra = "forbid"

# --- Main Bucket Request Model ---

class BucketRequest(BaseModel):
    """
    Pydantic model for validating bucket requests in patch/update operations.
    Based on Google Cloud Storage Bucket schema.
    """
    # Core properties
    name: Optional[str] = None
    storageClass: Optional[BucketStorageClass] = None
    location: Optional[str] = None
    
    # Configuration objects
    billing: Optional[BucketBilling] = None
    cors: Optional[List[CorsConfiguration]] = None
    customPlacementConfig: Optional[CustomPlacementConfig] = None
    hierarchicalNamespace: Optional[HierarchicalNamespace] = None
    iamConfiguration: Optional[IamConfiguration] = None
    ipFilter: Optional[IpFilter] = None
    lifecycle: Optional[Lifecycle] = None
    autoclass: Optional[Autoclass] = None
    versioning: Optional[Versioning] = None
    website: Optional[Website] = None
    logging: Optional[Logging] = None
    retentionPolicy: Optional[RetentionPolicy] = None
    objectRetention: Optional[ObjectRetention] = None
    softDeletePolicy: Optional[SoftDeletePolicy] = None
    encryption: Optional[EncryptionConfiguration] = None
    owner: Optional[Owner] = None
    
    # Simple properties
    labels: Optional[Dict[str, str]] = None
    defaultEventBasedHold: Optional[bool] = None
    rpo: Optional[BucketRPO] = None
    locationType: Optional[str] = None
    projectNumber: Optional[str] = None
    satisfiesPZS: Optional[bool] = None
    satisfiesPZI: Optional[bool] = None
    
    # Internal simulation properties (not part of actual API)
    project: Optional[str] = None
    softDeleted: Optional[bool] = None
    objects: Optional[List[str]] = None
    enableObjectRetention: Optional[bool] = None

    @field_validator('location')
    @classmethod
    def validate_location(cls, v: Optional[str]) -> Optional[str]:
        """Validate location is not empty string."""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Location cannot be empty string")
        return v

    @field_validator('labels')
    @classmethod  
    def validate_labels(cls, v: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """Validate label keys and values."""
        if v is not None:
            for key, value in v.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValueError("All label keys and values must be strings")
                if len(key) > 63 or len(value) > 63:
                    raise ValueError("Label keys and values must be 63 characters or less")
        return v

    class Config:
        extra = "forbid"  # Reject unknown fields
        use_enum_values = True
        validate_assignment = True


class IamConditionModel(BaseModel):
    """
    Pydantic model for IAM policy condition.
    Represents a conditional expression that restricts when a binding applies.
    """
    title: str = Field(..., description="Short description of the condition")
    expression: str = Field(..., description="Common Expression Language (CEL) syntax string")
    description: Optional[str] = Field(None, description="Detailed explanation of the expression's intent")
    location: Optional[str] = Field(None, description="Optional location string for debugging")


class IamBindingModel(BaseModel):
    """
    Pydantic model for IAM policy binding.
    Represents a role-member association with optional conditions.
    """
    role: str = Field(..., description="IAM role string")
    members: List[str] = Field(..., min_items=1, description="List of member identifiers")
    condition: Optional[IamConditionModel] = Field(None, description="Optional condition expression")

    @validator('role')
    def validate_role(cls, v):
        if v not in VALID_IAM_ROLES:
            raise ValueError(f"Invalid role '{v}'. Valid roles: {sorted(VALID_IAM_ROLES)}")
        return v

    @validator('members')
    def validate_members(cls, v):
        if not v:
            raise ValueError("Members list cannot be empty")
        
        valid_prefixes = [
            "allUsers", "allAuthenticatedUsers", "user:", "serviceAccount:", 
            "group:", "domain:", "projectOwner:", "projectEditor:", "projectViewer:"
        ]
        
        for i, member in enumerate(v):
            if not isinstance(member, str):
                raise ValueError(f"Member at index {i} must be a string")
            
            if not any(member == prefix or member.startswith(prefix) for prefix in valid_prefixes):
                raise ValueError(f"Invalid member format '{member}' at index {i}. Must start with one of: {valid_prefixes}")
            
            # Additional validation for email formats
            if member.startswith(("user:", "serviceAccount:", "group:")):
                email_part = member.split(":", 1)[1]
                if not email_part or "@" not in email_part:
                    raise ValueError(f"Invalid email format in member '{member}' at index {i}")
        
        return v


class IamPolicyModel(BaseModel):
    """
    Pydantic model for IAM policy.
    Represents a complete IAM policy with bindings and metadata.
    """
    bindings: List[IamBindingModel] = Field(..., description="List of role-member associations")
    etag: Optional[str] = Field(None, description="HTTP 1.1 entity tag for the policy")
    kind: Optional[str] = Field(None, description="Resource kind, should be 'storage#policy'")
    resourceId: Optional[str] = Field(None, description="Resource ID the policy applies to")
    version: Optional[int] = Field(1, ge=1, description="IAM policy format version")

    @validator('kind')
    def validate_kind(cls, v):
        if v is not None and v != "storage#policy":
            raise ValueError("Policy 'kind' must be 'storage#policy' if provided")
        return v

    @validator('version')
    def validate_version(cls, v):
        if v is not None and v < 1:
            raise ValueError("Policy 'version' must be >= 1 if provided")
        return v


# --- Complete Database Bucket Model ---

class DatabaseBucketModel(BaseModel):
    """
    Complete Pydantic model for validating bucket data as stored in the database.
    This covers all fields that can be present in the GoogleCloudStorageDefaultDB.json structure,
    including both API response fields and internal simulation fields.
    """
    # Core required fields
    name: str = Field(..., description="Bucket name")
    project: str = Field(..., description="Project ID")
    id: str = Field(..., description="Bucket ID (project/bucket_name format)")
    kind: str = Field(default="storage#bucket", description="Resource kind")
    
    # Metadata fields
    metageneration: str = Field(..., description="Bucket metageneration")
    generation: str = Field(..., description="Bucket generation")
    timeCreated: str = Field(..., description="Creation time in RFC 3339 format")
    updated: str = Field(..., description="Last update time in RFC 3339 format")
    etag: str = Field(..., description="Entity tag")
    selfLink: str = Field(..., description="Self link URL")
    
    # Location and storage
    location: str = Field(default="US", description="Bucket location")
    locationType: Optional[str] = Field(None, description="Location type (region, dual-region, etc.)")
    storageClass: str = Field(default="STANDARD", description="Default storage class")
    rpo: Optional[str] = Field(None, description="Recovery Point Objective")
    
    # Project information
    projectNumber: str = Field(..., description="Project number")
    
    # Internal simulation fields
    softDeleted: bool = Field(default=False, description="Whether bucket is soft deleted")
    objects: List[str] = Field(default_factory=list, description="List of objects in bucket")
    enableObjectRetention: bool = Field(default=False, description="Object retention enabled")
    
    # IAM and security
    iamPolicy: Dict[str, Any] = Field(default_factory=lambda: {"bindings": []}, description="IAM policy")
    acl: Optional[List[Dict[str, Any]]] = Field(None, description="Access control list")
    defaultObjectAcl: Optional[List[Dict[str, Any]]] = Field(None, description="Default object ACL")
    
    # Configuration objects (all optional as they may not be present in all buckets)
    billing: Optional[BucketBilling] = None
    cors: Optional[List[CorsConfiguration]] = None
    customPlacementConfig: Optional[CustomPlacementConfig] = None
    hierarchicalNamespace: Optional[HierarchicalNamespace] = None
    iamConfiguration: Optional[IamConfiguration] = None
    ipFilter: Optional[IpFilter] = None
    lifecycle: Optional[Lifecycle] = None
    autoclass: Optional[Autoclass] = None
    versioning: Optional[Versioning] = None
    website: Optional[Website] = None
    logging: Optional[Logging] = None
    retentionPolicy: Optional[RetentionPolicy] = None
    objectRetention: Optional[ObjectRetention] = None
    softDeletePolicy: Optional[SoftDeletePolicy] = None
    encryption: Optional[EncryptionConfiguration] = None
    owner: Optional[Owner] = None
    
    # Storage layout
    storageLayout: Dict[str, Any] = Field(default_factory=dict, description="Storage layout configuration")
    
    # Simple optional properties
    labels: Optional[Dict[str, str]] = None
    defaultEventBasedHold: Optional[bool] = None
    satisfiesPZS: Optional[bool] = None
    satisfiesPZI: Optional[bool] = None
    
    # Legacy fields (may be present in older bucket data)
    retentionPolicyLocked: Optional[bool] = Field(None, description="Legacy retention policy locked flag")

    @field_validator('kind')
    @classmethod
    def validate_kind(cls, v: str) -> str:
        """Validate kind field."""
        if v != "storage#bucket":
            raise ValueError("Bucket kind must be 'storage#bucket'")
        return v

    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Validate ID follows project/bucket_name format."""
        if '/' not in v:
            raise ValueError("Bucket ID must follow 'project/bucket_name' format")
        return v

    @field_validator('projectNumber')
    @classmethod
    def validate_project_number(cls, v: str) -> str:
        """Validate project number is a valid format."""
        if not v.isdigit() or len(v) != 12:
            raise ValueError("Project number must be a 12-digit string")
        return v

    @field_validator('timeCreated', 'updated')
    @classmethod
    def validate_rfc3339_format(cls, v: str) -> str:
        """Validate timestamp is in RFC 3339 format."""
        if not v.endswith('Z') and '+' not in v and v.count('T') != 1:
            raise ValueError("Timestamp must be in RFC 3339 format")
        return v

    class Config:
        extra = "forbid"  # Reject unknown fields
        use_enum_values = True
        validate_assignment = True


class GoogleCloudStorageDB(BaseModel):
    """
    Complete Pydantic model for validating the entire GoogleCloudStorageDefaultDB.json structure.
    """
    buckets: Dict[str, DatabaseBucketModel] = Field(
        default_factory=dict, 
        description="Dictionary of bucket name to bucket data"
    )
    
    # Optional simulation engine fields (used in tests and internal operations)
    bucket_counter: Optional[int] = Field(None, description="Internal counter for bucket operations")
    project_id: Optional[str] = Field(None, description="Default project ID for operations")

    @field_validator('buckets')
    @classmethod
    def validate_bucket_names_match_keys(cls, v: Dict[str, DatabaseBucketModel]) -> Dict[str, DatabaseBucketModel]:
        """Validate that bucket names match their dictionary keys."""
        for bucket_name, bucket_data in v.items():
            if bucket_data.name != bucket_name:
                raise ValueError(f"Bucket name '{bucket_data.name}' does not match key '{bucket_name}'")
        return v

    class Config:
        extra = "forbid"  # Still forbid unknown fields, but allow the defined optional ones
        validate_assignment = True
