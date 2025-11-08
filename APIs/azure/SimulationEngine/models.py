from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator, conint, confloat
from pydantic_core import PydanticCustomError
from enum import Enum
from typing import Literal

class AuthMethod(str, Enum):
    CREDENTIAL = 'credential'
    KEY = 'key'
    CONNECTION_STRING = 'connectionString'


class RetryMode(str, Enum):
    FIXED = 'fixed'
    EXPONENTIAL = 'exponential'


# --- Helper from your reference models ---
def new_uuid_str():
    return str(uuid.uuid4())


# --- Common Model (as per your reference) ---
class AzureSku(BaseModel):
    name: str
    tier: Optional[str] = None
    capacity: Optional[int] = None
    family: Optional[str] = None


# --- App Configuration (P0 Relevant Models from your reference) ---
class AppConfigKeyValueItem(BaseModel):
    key: str
    value: str
    label: Optional[str] = None
    content_type: Optional[str] = None
    etag: str = Field(default_factory=new_uuid_str)
    last_modified: str
    locked: bool = False
    app_config_store_name: str


class AppConfigStore(BaseModel):
    id: str  # ARM ID
    name: str
    location: str
    resource_group_name: str
    subscription_id: str
    key_values: List[AppConfigKeyValueItem] = Field(default_factory=list)


# --- Cosmos DB (P0 Relevant Models from your reference) ---
class CosmosDBContainer(BaseModel):
    id: str  # ARM ID from 'azmcp-cosmos-database-container-list'
    name: str
    database_name: str
    account_name: str
    items: List[Dict[str, Any]] = Field(default_factory=list)


class CosmosDBDatabase(BaseModel):
    id: str  # ARM ID from 'azmcp-cosmos-database-list'
    name: str
    account_name: str
    containers: List[CosmosDBContainer] = Field(default_factory=list)


class CosmosDBAccount(BaseModel):
    id: str  # ARM ID from 'azmcp-cosmos-account-list'
    name: str
    location: str
    kind: str  # e.g., GlobalDocumentDB, MongoDB
    resource_group_name: str
    subscription_id: str
    databases: List[CosmosDBDatabase] = Field(default_factory=list)


class AzmcpCosmosDatabaseContainerListInputArgs(BaseModel):
    """
    Pydantic model for validating input arguments to azmcp_cosmos_database_container_list.
    """
    subscription: str = Field(..., min_length=1)
    account_name: str = Field(..., min_length=1)
    database_name: str = Field(..., min_length=1)

    auth_method: Optional[Literal['credential', 'key', 'connectionString']] = None
    tenant: Optional[str] = None  # No min_length as per schema unless specified otherwise

    # Retry parameters are strings in input schema but represent numbers.
    # Pydantic will attempt conversion; non-numeric strings will cause ValidationError.
    retry_max_retries: Optional[conint(ge=0)] = None
    retry_delay: Optional[confloat(ge=0)] = None  # Assuming non-negative float, ge=0 allows 0
    retry_max_delay: Optional[confloat(ge=0)] = None
    retry_mode: Optional[Literal['fixed', 'exponential']] = None
    retry_network_timeout: Optional[confloat(ge=0)] = None

    class Config:
        validate_assignment = True  # Ensure model fields are validated on assignment
        extra = 'forbid'  # Forbid any extra fields not defined in the model


class AzmcpCosmosAccountCreateInputArgs(BaseModel):
    """
    Pydantic model for validating input arguments to azmcp_cosmos_account_create.
    """
    subscription: str = Field(..., min_length=1)
    resource_group: str = Field(..., min_length=1)
    account_name: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    kind: Optional[Literal['GlobalDocumentDB', 'MongoDB', 'Parse']] = Field(default='GlobalDocumentDB')
    auth_method: Optional[Literal['credential', 'key', 'connectionString']] = None
    tenant: Optional[str] = None
    retry_max_retries: Optional[conint(ge=0)] = None
    retry_delay: Optional[confloat(ge=0)] = None
    retry_max_delay: Optional[confloat(ge=0)] = None
    retry_mode: Optional[Literal['fixed', 'exponential']] = None
    retry_network_timeout: Optional[confloat(ge=0)] = None

    class Config:
        validate_assignment = True
        extra = 'forbid'


class AzmcpCosmosDatabaseListRetryParams(BaseModel):
    """
    Pydantic model for validating the optional retry parameters of the
    azmcp_cosmos_database_list function.
    These parameters are expected as strings as per the input schema.
    """
    retry_max_retries: Optional[str] = None
    retry_delay: Optional[str] = None
    retry_max_delay: Optional[str] = None
    retry_mode: Optional[str] = None  # String type, specific values not validated here
    retry_network_timeout: Optional[str] = None

    @field_validator('retry_max_retries', mode='before')
    def validate_retry_max_retries_format(cls, v: Optional[str]):
        if v is None:
            return v
        if not isinstance(v, str):
            raise TypeError("Input must be a string.")
        if not v.isdigit():  # Ensures it's a non-negative integer string
            raise ValueError("String must represent a non-negative integer.")
        return v

    @field_validator(
        'retry_delay',
        'retry_max_delay',
        'retry_network_timeout',
        mode='before'
    )
    def validate_retry_numeric_strings_format(cls, v: Optional[str], field):
        if v is None:
            return v
        if not isinstance(v, str):
            raise TypeError("Input must be a string.")
        try:
            # Check if the string can be converted to a float.
            # Further constraints (e.g., non-negative) could be added if required.
            float(v)
        except ValueError:
            raise ValueError("String must represent a valid number.")
        return v

    class Config:
        extra = 'forbid'


# --- Key Vault (P0 Relevant Models from your reference) ---
class KeyVaultKeyAttributes(BaseModel):
    enabled: bool
    exp: Optional[int] = None
    nbf: Optional[int] = None
    created: int
    updated: int
    recoveryLevel: Optional[str] = None  # Was str in your model


class KeyVaultKey(BaseModel):
    name: str
    kid: str
    kty: str
    key_ops: List[str] = Field(default_factory=list)
    attributes: KeyVaultKeyAttributes
    tags: Optional[Dict[str, str]] = None
    vault_name: str


class KeyVault(BaseModel):
    id: str  # ARM ID
    name: str
    location: str
    resource_group_name: str
    subscription_id: str
    keys: List[KeyVaultKey] = Field(default_factory=list)


# --- Azure Monitor (Log Analytics - P0 Relevant Models from your reference) ---
class LogAnalyticsTableColumn(BaseModel):
    name: str
    type: str  # e.g., 'string', 'datetime'


class LogAnalyticsTableSchema(BaseModel):
    name: str
    displayName: Optional[str] = None
    columns: List[LogAnalyticsTableColumn] = Field(default_factory=list)


class LogAnalyticsTable(BaseModel):
    id: str
    name: str
    timespan: str
    schema_details: LogAnalyticsTableSchema
    workspace_name: str
    log_entries: List[Dict[str, Any]] = Field(default_factory=list)


class LogAnalyticsWorkspaceSku(BaseModel):
    name: str


class LogAnalyticsWorkspace(BaseModel):
    id: str  # ARM ID
    name: str
    location: str
    customerId: Optional[str] = None
    sku: Optional[LogAnalyticsWorkspaceSku] = None
    provisioningState: Optional[str] = None
    resource_group_name: str
    subscription_id: str
    tables: List[LogAnalyticsTable] = Field(default_factory=list)
    available_table_types: List[str] = Field(default_factory=list)


class MonitorHealthCause(BaseModel):
    description: str
    severity: str
    recommendedActions: List[str] = Field(default_factory=list)


class MonitorHealthEntity(BaseModel):
    entityId: str
    healthState: str
    causes: List[MonitorHealthCause] = Field(default_factory=list)


class MonitorHealthModel(BaseModel):
    name: str
    resource_group_name: str
    subscription_id: str
    entities: List[MonitorHealthEntity] = Field(default_factory=list)


# --- Azure Storage (P0 Relevant Models from your reference) ---
class StorageBlobProperties(BaseModel):
    lastModified: str
    etag: str
    contentLength: int
    contentType: str
    blobType: str
    leaseStatus: str
    accessTier: Optional[str] = None


class StorageBlob(BaseModel):
    name: str
    properties: StorageBlobProperties
    metadata: Optional[Dict[str, str]] = None
    container_name: str
    account_name: str


class OutputBlobItem(BaseModel):
    """
    Represents a blob item as returned by the azmcp_storage_blob_list function.
    This model defines the structure of each dictionary in the list returned by the function.
    """
    name: str
    properties: StorageBlobProperties
    metadata: Optional[Dict[str, str]] = None


class StorageBlobContainer(BaseModel):
    name: str
    lastModified: str
    etag: str
    leaseStatus: Optional[str] = "unlocked"
    leaseState: Optional[str] = "available"
    publicAccess: Optional[str] = None
    hasImmutabilityPolicy: Optional[bool] = False
    hasLegalHold: Optional[bool] = False
    metadata: Optional[Dict[str, str]] = None
    account_name: str
    blobs: List[StorageBlob] = Field(default_factory=list)

class AzmcpStorageBlobContainerDetailsInput(BaseModel):
    """
    Pydantic model for validating input arguments to azmcp_storage_blob_container_details.
    Corresponds to the inputSchema provided in the function's documentation.
    """
    subscription: str = Field(min_length=1)
    account_name: str = Field(min_length=1)
    container_name: str = Field(min_length=1)
    auth_method: Optional[str] = None
    tenant: Optional[str] = None
    retry_max_retries: Optional[str] = None
    retry_delay: Optional[str] = None
    retry_max_delay: Optional[str] = None
    retry_mode: Optional[str] = None
    retry_network_timeout: Optional[str] = None

    class Config:
        # Configuration to allow Pydantic to validate even if extra fields are passed in raw_args
        # that are not defined in this model (though in this case, all args are mapped).
        # This is generally good practice for input models.
        extra = 'ignore'

class AzmcpStorageBlobContainerDetailsOutput(BaseModel):
    """
    Pydantic model for validating the output of azmcp_storage_blob_container_details.
    Corresponds to the outputSchema of the function.
    """
    name: str
    lastModified: str
    etag: str
    leaseStatus: str
    leaseState: str
    publicAccess: Optional[str] = None
    hasImmutabilityPolicy: bool
    hasLegalHold: bool
    metadata: Optional[Dict[str, str]] = None

class StorageTable(BaseModel): 
    TableName: str
    account_name: str


class StorageAccount(BaseModel):
    id: str
    name: str
    location: str
    kind: str
    sku: AzureSku
    provisioningState: Optional[str] = None
    primaryEndpoints: Optional[Dict[str, str]] = None
    resource_group_name: str
    subscription_id: str
    blob_containers: List[StorageBlobContainer] = Field(default_factory=list)
    tables: List[StorageTable] = Field(default_factory=list)


# --- Azure Resource Group and Subscription (Containers from your reference) ---
class AzureResourceGroup(BaseModel):
    id: str  # ARM ID
    name: str
    location: str
    managedBy: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    subscription_id: str
    app_config_stores: List[AppConfigStore] = Field(default_factory=list)
    cosmos_db_accounts: List[CosmosDBAccount] = Field(default_factory=list)
    key_vaults: List[KeyVault] = Field(default_factory=list)
    log_analytics_workspaces: List[LogAnalyticsWorkspace] = Field(default_factory=list)
    monitor_health_models: List[MonitorHealthModel] = Field(default_factory=list)
    storage_accounts: List[StorageAccount] = Field(default_factory=list)
 
class AzmcpGroupListInput(BaseModel):
    """
    Pydantic model for validating input arguments to the azmcp_group_list function.
    """
    subscription: str
    auth_method: Optional[Literal['credential', 'key', 'connectionString']] = None
    tenant: Optional[str] = None
    
    # Fields are defined as Optional[str] to match the input schema's "type": "string".
    # A validator then ensures the string content represents a valid integer.
    retry_max_retries: Optional[str] = None
    retry_delay: Optional[str] = None
    retry_max_delay: Optional[str] = None
    retry_network_timeout: Optional[str] = None

    retry_mode: Optional[Literal['fixed', 'exponential']] = None

class AzmcpGroupListItem(BaseModel):
    """
    Represents a resource group as returned by the list operation.
    """
    name: str
    id: str
    location: str
    managedBy: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


class AzureSubscription(BaseModel):
    id: str
    subscriptionId: str
    displayName: str
    state: str
    tenantId: str
    resource_groups: List[AzureResourceGroup] = Field(default_factory=list)


# --- Main Azure DB Model (Scoped to P0, using your reference model structures) ---
class AzureDB(BaseModel):
    """
    Root Pydantic model for the Azure services simulation database,
    scoped to P0 functionalities and using the agreed-upon model structures.
    """

    subscriptions: List[AzureSubscription] = Field(default_factory=list)

    class Config:
        validate_assignment = True

# --- azmcp_monitor_table_list ---
class LogAnalyticsTableSchemaReturn(BaseModel):
    """
    Represents the schema definition of a Log Analytics table as returned by the function.
    This model is specific to the function's return structure, particularly ensuring
    `displayName` is non-optional as per the docstring.
    """
    name: str
    displayName: str
    columns: List[LogAnalyticsTableColumn] # Uses the existing LogAnalyticsTableColumn model

class LogAnalyticsTableListItemReturn(BaseModel):
    """
    Represents a single table item in the list returned by the function.
    This model precisely matches the fields described in the function's docstring for each table.
    """
    name: str
    id: str
    timespan: str
    schema: LogAnalyticsTableSchemaReturn

class SubscriptionListItem(BaseModel):
    """
    Represents an Azure subscription as returned by the list operation.
    Contains essential details like ID, name, state, and tenant ID.
    """
    id: str
    subscriptionId: str
    displayName: str
    state: str
    tenantId: str


# --- azmcp_appconfig_kv_lock ---
class LockedAppConfigKeyValueItem(BaseModel):
    """
    Represents the details of a locked key-value item returned by the lock operation.
    """
    key: str
    value: str
    label: Optional[str] = None
    content_type: Optional[str] = None
    etag: str
    last_modified: str  # ISO 8601 format
    locked: bool


class SetAppConfigKeyValueItem(BaseModel):
    """
    Represents the details of a key-value item returned by the set operation.
    Contains all the properties of a key-value item after it has been set or updated.
    """
    key: str
    value: str
    label: Optional[str] = None
    content_type: Optional[str] = None
    etag: str
    last_modified: str  # ISO 8601 format
    locked: bool = False


class AppConfigKeyValueUpsertData(BaseModel):
    """
    Represents the data needed to create or update a key-value in App Configuration.
    Used for upsert operations.
    """
    key: str
    value: str
    label: Optional[str] = None


# --- azmcp_appconfig_account_list ---
class AppConfigStoreListItem(BaseModel):
    """
    Represents an App Configuration store as returned by the list operation.
    Contains essential details like name, ID, and location.
    """
    name: str
    id: str
    location: str


# --- azmcp_keyvault_key_create ---
class AllowedKeyTypes(Enum):
    RSA = "RSA"
    EC = "EC"


class KeyOpsRSA(Enum):
    Encrypt = "encrypt"
    Decrypt = "decrypt"
    Sign = "sign"
    Verify = "verify"
    WrapKey = "wrapKey"
    UnwrapKey = "unwrapKey"


class KeyOpsEC(Enum):
    Sign = "sign"
    Verify = "verify"


class KeyCreateResponseAttributes(BaseModel):
    """
    Attributes of a created key, as returned by azmcp_keyvault_key_create.
    """
    enabled: bool
    exp: Optional[int] = None
    nbf: Optional[int] = None
    created: int
    updated: int
    recoveryLevel: str


class KeyVaultKeyCreateResponse(BaseModel):
    """
    Pydantic model for the return type of azmcp_keyvault_key_create.
    """
    key_ops: List[str]
    kty: str
    attributes: KeyCreateResponseAttributes


class KeyOperationAttributes(KeyCreateResponseAttributes):
    """
    Attributes of a key as returned by the get key operation,
    specifically matching the function's return docstring.
    """
    pass


class KeyDetails(BaseModel):
    """
    Details of a retrieved key from Azure Key Vault, as specified
    by the function's return docstring.
    """
    kid: str
    key_ops: List[str] = Field(default_factory=list)
    kty: str
    attributes: KeyOperationAttributes


class KeyListItemAttributes(BaseModel):
    """
    Attributes of a key listed from Azure Key Vault.
    Corresponds to the 'attributes' dictionary in the return type of the list keys function.
    """
    enabled: bool
    exp: Optional[int] = None
    nbf: Optional[int] = None
    created: int
    updated: int


class KeyListItem(BaseModel):
    """
    Represents a single key item as returned by the list keys function.
    This model defines the structure of each dictionary in the list returned by the function.
    """
    attributes: KeyListItemAttributes
    tags: Optional[Dict[str, str]] = None


class HealthStateCause(BaseModel):
    description: str
    severity: str
    recommendedActions: List[str] = Field(default_factory=list)


class HealthStateEntity(BaseModel):
    entityId: str
    healthState: str
    causes: List[HealthStateCause] = Field(default_factory=list)


class AzmcpMonitorWorkspaceListItem(BaseModel):
    """
    Represents a single Log Analytics workspace item as returned by
    the azmcp_monitor_workspace_list function.
    """
    name: str
    id: str
    location: str
    customerId: str
    sku: LogAnalyticsWorkspaceSku  # This uses an existing model from the DB schema
    provisioningState: str


class StorageAccountKind(str, Enum):
    """Enum for Azure Storage account kinds."""
    STORAGE_V2 = 'StorageV2'
    BLOB_STORAGE = 'BlobStorage'


class StorageTableListItem(BaseModel):
    TableName: str

class StorageAccountListItem(BaseModel):
    """
    Represents a Storage Account as returned by the list operation.
    Contains essential details like name, ID, location, kind, and SKU.
    """
    name: str
    id: str
    location: str
    kind: str
    sku: AzureSku
    provisioningState: str
    primaryEndpoints: Dict[str, str]

class RetryModesOps(str, Enum):
    """Enumeration for supported retry modes."""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"

class StorageBlobContainerListItem(BaseModel):
    """
    Represents a blob container as returned by the list operation.
    Contains essential details for the command's output.
    """
    name: str
    lastModified: str
    etag: str
    leaseStatus: str
    publicAccess: Optional[str] = None