from common_utils.tool_spec_decorator import tool_spec
import json
import unittest
import os
import sys
from datetime import datetime
import builtins
import hashlib
import time

from typing import Dict, Any, List, Tuple, Optional, Union

from google_cloud_storage.SimulationEngine.db import DB
from google_cloud_storage.SimulationEngine.custom_errors import InvalidProjectionValueError, MissingGenerationError, NotSoftDeletedError, SoftDeleteRetentionActiveError
from google_cloud_storage.SimulationEngine.custom_errors import BucketNotFoundError, MetagenerationMismatchError, BucketNotEmptyError, GenerationMismatchError
from pydantic import ValidationError
from google_cloud_storage.SimulationEngine.models import (
        BucketRequest, 
        BucketProjection, 
        PredefinedBucketAcl, 
        PredefinedDefaultObjectAcl
    )
from google_cloud_storage.SimulationEngine.custom_errors import (
    InvalidPredefinedAclValueError, 
    InvalidPredefinedDefaultObjectAclValueError,
    InvalidProjectionValueError
)
from google_cloud_storage.SimulationEngine.utils import (
    ALLOWED_BUCKET_PREDEFINED_ACLS,
    ALLOWED_OBJECT_PREDEFINED_DEFAULT_ACLS,
    VALID_IAM_ROLES,
)


@tool_spec(
    spec={
        'name': 'delete_bucket',
        'description': """ Deletes an empty bucket.
        
        Deletions are permanent unless soft delete is enabled on the bucket. This function
        checks for metageneration match conditions and ensures the bucket is empty before deletion. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'bucket': {
                    'type': 'string',
                    'description': 'Name of the bucket to delete. Must be a valid, non-empty bucket name.'
                },
                'if_metageneration_match': {
                    'type': 'string',
                    'description': """ If set, deletes only if the bucket's metageneration
                    matches this value. """
                },
                'if_metageneration_not_match': {
                    'type': 'string',
                    'description': """ If set, deletes only if the bucket's metageneration
                    does not match this value. """
                }
            },
            'required': [
                'bucket'
            ]
        }
    }
)
def delete(
    bucket: str,
    if_metageneration_match: Optional[str] = None,
    if_metageneration_not_match: Optional[str] = None
) -> Dict[str, Any]:
    """
    Deletes an empty bucket.

    Deletions are permanent unless soft delete is enabled on the bucket. This function
    checks for metageneration match conditions and ensures the bucket is empty before deletion.

    Args:
        bucket (str): Name of the bucket to delete. Must be a valid, non-empty bucket name.
        if_metageneration_match (Optional[str]): If set, deletes only if the bucket's metageneration
            matches this value.
        if_metageneration_not_match (Optional[str]): If set, deletes only if the bucket's metageneration
            does not match this value.

    Returns:
        Dict[str, Any]:
        - A `message` key indicating success with the value:
            - "Bucket '{bucket_name}' deleted successfully" when the bucket is hard deleted 
            or "Bucket '{bucket_name}' soft deleted successfully" when the bucket is soft deleted
            or "Bucket '{bucket_name}' permanently deleted (retention period expired)" if the bucket is hard deleted as the retention period has expired after the bucket was soft deleted previously.

    Raises:
        TypeError: If 'bucket' is not a string, or if 'if_metageneration_match' or
                   'if_metageneration_not_match' are provided and are not strings.
        ValueError: If 'bucket' is empty, or if parameters are empty
                   , or if contain only whitespace when provided, or if violates Google Cloud Storage naming conventions
        BucketNotFoundError: If the specified bucket does not exist in the DB.
        MetagenerationMismatchError: If 'if_metageneration_match' or 'if_metageneration_not_match'
                                     conditions are not met.
        BucketNotEmptyError: If the bucket is not empty and cannot be deleted.
        SoftDeleteRetentionActiveError: If the bucket is already soft deleted and has a soft delete retention period active.
    """
    # --- Input Validation ---
    if not isinstance(bucket, str):
        raise TypeError(f"Argument 'bucket' must be a string, got {type(bucket).__name__}.")
    if if_metageneration_match is not None and not isinstance(if_metageneration_match, str):
        raise TypeError(f"Argument 'if_metageneration_match' must be a string or None, got {type(if_metageneration_match).__name__}.")
    if if_metageneration_not_match is not None and not isinstance(if_metageneration_not_match, str):
        raise TypeError(f"Argument 'if_metageneration_not_match' must be a string or None, got {type(if_metageneration_not_match).__name__}.")

    # Validate bucket name is not empty
    if not bucket.strip():
        raise ValueError("Argument 'bucket' cannot be empty or contain only whitespace.")
    
    # Validate bucket name follows basic Google Cloud Storage naming conventions
    if len(bucket) < 3 or len(bucket) > 63:
        raise ValueError("Bucket name must be between 3 and 63 characters long.")
    
    # Check for basic naming convention violations
    if bucket.startswith('.') or bucket.endswith('.') or '..' in bucket:
        raise ValueError("Bucket name cannot start or end with dots, or contain consecutive dots.")

    # --- Core Logic ---
    # Assume DB is accessible here
    if bucket not in DB["buckets"]:
        raise BucketNotFoundError(f"Bucket '{bucket}' not found.")

    bucket_data = DB["buckets"][bucket]

    # Check metageneration conditions
    current_metageneration = bucket_data.get("metageneration")
    if if_metageneration_match is not None:
        if current_metageneration != if_metageneration_match:
            raise MetagenerationMismatchError(f"Metageneration mismatch: Required match '{if_metageneration_match}', found '{current_metageneration}'.")
    if if_metageneration_not_match is not None:
        if current_metageneration == if_metageneration_not_match:
            raise MetagenerationMismatchError(f"Metageneration mismatch: Required non-match '{if_metageneration_not_match}', found '{current_metageneration}'.")

    # Check if bucket is empty
    if bucket_data.get("objects") and len(bucket_data["objects"]) > 0:
        raise BucketNotEmptyError(f"Bucket '{bucket}' is not empty.")

    # Check for soft delete policy and handle accordingly
    soft_delete_policy = bucket_data.get("softDeletePolicy")
    if soft_delete_policy and isinstance(soft_delete_policy, dict) and soft_delete_policy.get("effectiveTime"):
        # Soft delete is enabled
        import datetime
        current_time = datetime.datetime.now(datetime.timezone.utc)
        current_time_iso = current_time.isoformat() + "Z"

        # Check if bucket is already soft deleted
        if bucket_data.get("softDeleted", False):
            soft_delete_time_str = bucket_data.get("softDeleteTime")
            if soft_delete_time_str:
                soft_delete_time = datetime.datetime.fromisoformat(soft_delete_time_str.replace("Z", ""))
                retention_seconds = int(soft_delete_policy.get("retentionDurationSeconds", 0))
                expiration_time = soft_delete_time + datetime.timedelta(seconds=retention_seconds)
                
                if current_time < expiration_time:
                    # Retention period has not expired - bucket is still in soft delete state
                    raise SoftDeleteRetentionActiveError(f"Bucket '{bucket}' is already soft deleted and cannot be deleted again until retention period expires")
                else:
                    # Retention period has expired - perform hard deletion
                    del DB["buckets"][bucket]
                    return {"message": f"Bucket '{bucket}' permanently deleted (retention period expired)"}
            
        # Bucket is not yet soft deleted - perform soft deletion
        DB["buckets"][bucket].update({
            "softDeleted": True,
            "softDeleteTime": current_time_iso,
            "hardDeleteTime": None  # Will be set later based on retention period
        })
        DB["buckets"][bucket]["softDeletePolicy"]["effectiveTime"] = current_time_iso
        
        # Calculate hard delete time based on retention period if specified
        if "retentionDurationSeconds" in soft_delete_policy:
            try:
                retention_seconds = int(soft_delete_policy["retentionDurationSeconds"])
                hard_delete_time = current_time + datetime.timedelta(seconds=retention_seconds)
                DB["buckets"][bucket]["hardDeleteTime"] = hard_delete_time.isoformat() + "Z"
            except (ValueError, TypeError):
                # If retention period is invalid, leave hardDeleteTime as None
                pass
        
        return {"message": f"Bucket '{bucket}' soft deleted successfully"}
    else:
        # No soft delete policy - perform immediate hard deletion
        del DB["buckets"][bucket]
        return {"message": f"Bucket '{bucket}' deleted successfully"}


@tool_spec(
    spec={
        'name': 'restore_bucket',
        'description': """ Restores a soft-deleted bucket.
        
        This function restores a bucket only if it exists, is soft-deleted, and its generation
        matches the provided generation value. The bucket's softDeleted flag is set to False
        upon successful restoration. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'bucket': {
                    'type': 'string',
                    'description': 'Name of the bucket to restore. Must be a valid, non-empty bucket name.'
                },
                'generation': {
                    'type': 'string',
                    'description': """ The generation of the bucket for verification. Must match the
                    bucket's current generation exactly. """
                },
                'projection': {
                    'type': 'string',
                    'description': """ Set of properties to return. Defaults to "full".
                    Allowed values:
                    - "full": Includes all properties including acl and defaultObjectAcl.
                    - "noAcl": Excludes acl and defaultObjectAcl properties. """
                },
                'user_project': {
                    'type': 'string',
                    'description': """ The project to be billed for the request. Required for
                    Requester Pays buckets. Defaults to None. """
                }
            },
            'required': [
                'bucket',
                'generation'
            ]
        }
    }
)
def restore(
    bucket: str,
    generation: str,
    projection: str = "full",
    user_project: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Restores a soft-deleted bucket.

    This function restores a bucket only if it exists, is soft-deleted, and its generation
    matches the provided generation value. The bucket's softDeleted flag is set to False
    upon successful restoration.

    Args:
        bucket (str): Name of the bucket to restore. Must be a valid, non-empty bucket name.
        generation (str): The generation of the bucket for verification. Must match the
            bucket's current generation exactly.
        projection (str): Set of properties to return. Defaults to "full".
            Allowed values:
            - "full": Includes all properties including acl and defaultObjectAcl.
            - "noAcl": Excludes acl and defaultObjectAcl properties.
        user_project (Optional[str]): The project to be billed for the request. Required for
            Requester Pays buckets. Defaults to None.

    Returns:
        Dict[str, Any]: On success, returns a dictionary with:
            - message (str): Success message indicating bucket restoration.
            - bucket (Dict[str, Any]): Restored bucket metadata. If projection is "noAcl",
              acl and defaultObjectAcl fields are omitted. Contains the following keys:
                - acl (List[BucketAccessControl]): Access control list for the bucket.
                - billing (Dict[str, bool]):
                    - requesterPays (bool): Whether Requester Pays is enabled.
                - cors (List[Dict[str, Any]]): CORS configuration rules.
                    - maxAgeSeconds (int): Maximum age for preflight requests.
                    - method (List[str]): Allowed HTTP methods.
                    - origin (List[str]): Allowed origins.
                    - responseHeader (List[str]): Allowed response headers.
                - customPlacementConfig (Dict[str, List[str]]): Custom placement configuration.
                    - dataLocations (List[str]): Regional locations for data placement.
                - defaultEventBasedHold (bool): Whether event-based hold is enabled by default.
                - defaultObjectAcl (List[ObjectAccessControl]): Default object access controls.
                - encryption (Dict[str, str]): Encryption configuration.
                    - defaultKmsKeyName (str): Default KMS key for encryption.
                - etag (str): HTTP entity tag for the bucket.
                - hierarchicalNamespace (Dict[str, bool]): Hierarchical namespace configuration.
                    - enabled (bool): Whether hierarchical namespace is enabled.
                - iamConfiguration (Dict[str, Any]): IAM configuration settings.
                    - bucketPolicyOnly (Dict[str, Any]): Bucket policy only configuration.
                        - enabled (bool): Whether bucket policy only is enabled.
                        - lockedTime (str): When the policy was locked.
                    - uniformBucketLevelAccess (Dict[str, Any]): Uniform bucket-level access.
                        - enabled (bool): Whether uniform bucket-level access is enabled.
                        - lockedTime (str): When the access was locked.
                    - publicAccessPrevention (str): Public access prevention setting.
                - id (str): Bucket ID.
                - ipFilter (Dict[str, Any]): IP filter configuration.
                    - mode (str): IP filter mode.
                    - publicNetworkSource (Dict[str, List[str]]): Public network source config.
                        - allowedIpCidrRanges (List[str]): Allowed IP CIDR ranges.
                    - vpcNetworkSources (List[Dict[str, Any]]): VPC network sources.
                        - network (str): VPC network identifier.
                        - allowedIpCidrRanges (List[str]): Allowed IP CIDR ranges.
                - kind (str): Resource kind, always "storage#bucket".
                - labels (Dict[str, str]): User-defined labels.
                - lifecycle (Dict[str, List[Dict[str, Any]]]): Lifecycle configuration.
                    - rule (List[Dict[str, Any]]): Lifecycle rules.
                        - action (Dict[str, str]): Action to take.
                            - type (str): Action type.
                            - storageClass (str): Target storage class.
                        - condition (Dict[str, Any]): Condition for the rule.
                            - age (int): Age in days.
                            - createdBefore (str): Creation date threshold.
                            - customTimeBefore (str): Custom time threshold.
                            - daysSinceCustomTime (int): Days since custom time.
                            - daysSinceNoncurrentTime (int): Days since noncurrent time.
                            - isLive (bool): Whether object is live.
                            - matchesPattern (str): Pattern to match.
                            - matchesPrefix (List[str]): Prefixes to match.
                            - matchesSuffix (List[str]): Suffixes to match.
                            - matchesStorageClass (List[str]): Storage classes to match.
                            - noncurrentTimeBefore (str): Noncurrent time threshold.
                            - numNewerVersions (int): Number of newer versions.
                - autoclass (Dict[str, Any]): Autoclass configuration.
                    - enabled (bool): Whether autoclass is enabled.
                    - toggleTime (str): When autoclass was toggled.
                    - terminalStorageClass (str): Terminal storage class.
                    - terminalStorageClassUpdateTime (str): When terminal storage class was updated.
                - location (str): Bucket location.
                - locationType (str): Type of location configuration.
                - logging (Dict[str, str]): Logging configuration.
                    - logBucket (str): Log bucket name.
                    - logObjectPrefix (str): Log object prefix.
                - generation (str): Bucket generation number.
                - metageneration (str): Bucket metageneration number.
                - name (str): Bucket name.
                - owner (Dict[str, str]): Bucket owner information.
                    - entity (str): Owner entity.
                    - entityId (str): Owner entity ID.
                - projectNumber (str): Project number.
                - retentionPolicy (Dict[str, Any]): Retention policy configuration.
                    - effectiveTime (str): When retention policy becomes effective.
                    - isLocked (bool): Whether retention policy is locked.
                    - retentionPeriod (str): Retention period in seconds.
                - objectRetention (Dict[str, str]): Object retention configuration.
                    - mode (str): Retention mode.
                - rpo (str): Recovery Point Objective.
                - selfLink (str): Self-referencing URL.
                - softDeletePolicy (Dict[str, str]): Soft delete policy configuration.
                    - retentionDurationSeconds (str): Soft delete retention duration.
                    - effectiveTime (str): When soft delete policy becomes effective.
                - storageClass (str): Default storage class.
                - timeCreated (str): Creation timestamp.
                - updated (str): Last update timestamp.
                - softDeleteTime (str): Soft deletion timestamp.
                - hardDeleteTime (str): Hard deletion timestamp.
                - versioning (Dict[str, bool]): Versioning configuration.
                    - enabled (bool): Whether versioning is enabled.
                - website (Dict[str, str]): Website configuration.
                    - mainPageSuffix (str): Main page suffix.
                    - notFoundPage (str): 404 page.
                - satisfiesPZS (bool): Whether bucket satisfies PZS.
                - satisfiesPZI (bool): Whether bucket satisfies PZI.

    Raises:
        TypeError: If any argument is of an incorrect type.
        ValueError: If bucket is empty or contains only whitespace, or if bucket name
                   violates Google Cloud Storage naming conventions (length, dots).
        InvalidProjectionValueError: If projection is not one of the allowed values
                                   ("full" or "noAcl").
        BucketNotFoundError: If the specified bucket does not exist.
        NotSoftDeletedError: If the bucket is not soft-deleted.
        GenerationMismatchError: If the provided generation does not match the bucket's generation.
    """
    # --- Input Validation ---
    if not isinstance(bucket, str):
        raise TypeError(f"Argument 'bucket' must be a string, got {type(bucket).__name__}.")
    if not isinstance(generation, str):
        raise TypeError(f"Argument 'generation' must be a string, got {type(generation).__name__}.")
    if not isinstance(projection, str):
        raise TypeError(f"Argument 'projection' must be a string, got {type(projection).__name__}.")
    if user_project is not None and not isinstance(user_project, str):
        raise TypeError(f"Argument 'user_project' must be a string or None, got {type(user_project).__name__}.")

    # Validate bucket name is not empty
    if not bucket.strip():
        raise ValueError("Argument 'bucket' cannot be empty or contain only whitespace.")
    
    # Validate bucket name follows basic Google Cloud Storage naming conventions
    if len(bucket) < 3 or len(bucket) > 63:
        raise ValueError("Bucket name must be between 3 and 63 characters long.")
    
    # Check for basic naming convention violations
    if bucket.startswith('.') or bucket.endswith('.') or '..' in bucket:
        raise ValueError("Bucket name cannot start or end with dots, or contain consecutive dots.")

    # Validate projection value
    if projection not in ("full", "noAcl"):
        raise InvalidProjectionValueError(
            f"Invalid value for 'projection': '{projection}'. Must be 'full' or 'noAcl'."
        )

    # --- Core Logic ---
    if bucket not in DB["buckets"]:
        raise BucketNotFoundError(f"Bucket '{bucket}' not found.")

    bucket_data = DB["buckets"][bucket]
    
    if not bucket_data.get("softDeleted"):
        raise NotSoftDeletedError(f"Bucket '{bucket}' is not soft deleted.")
    
    if bucket_data.get("generation") != generation:
        raise GenerationMismatchError(
            f"Generation mismatch for bucket '{bucket}': Required '{generation}', found '{bucket_data.get('generation')}'."
        )

    # Restore the bucket
    bucket_data["softDeleted"] = False
    
    # Prepare response based on projection
    if projection == "full":
        return {
            "message": f"Bucket '{bucket}' restored successfully",
            "bucket": bucket_data,
        }
    else:
        return {
            "message": f"Bucket '{bucket}' restored successfully",
            "bucket": {
                k: v
                for k, v in bucket_data.items()
                if k not in ["acl", "defaultObjectAcl"]
            },
        }


@tool_spec(
    spec={
        'name': 'relocate_bucket',
        'description': """ Initiates a long-running Relocate Bucket operation on the specified bucket.
        
        This function validates the relocation request and initiates a bucket relocation operation.
        The operation moves a bucket from its current location to a specified destination location. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'bucket': {
                    'type': 'string',
                    'description': """ Name of the bucket to be relocated. Must be a valid, non-empty bucket name
                    that follows Google Cloud Storage naming conventions. """
                },
                'request_body': {
                    'type': 'object',
                    'description': 'A dictionary representing Configuration for the bucket relocation operation.',
                    'properties': {
                        'destinationLocation': {
                            'type': 'string',
                            'description': """ The new location to which the bucket will be moved.
                               Must be a valid Google Cloud region (e.g., 'us-central1', 'europe-west1'). """
                        },
                        'destinationCustomPlacementConfig': {
                            'type': 'object',
                            'description': """ Configuration for
                               Custom Dual Region. Optional. Contains: """,
                            'properties': {
                                'dataLocations': {
                                    'type': 'array',
                                    'description': """ The list of regional locations that will be used
                                           to store the bucket's data. Must contain exactly 2 locations for dual-region. """,
                                    'items': {
                                        'type': 'string'
                                    }
                                }
                            },
                            'required': [
                                'dataLocations'
                            ]
                        },
                        'validateOnly': {
                            'type': 'boolean',
                            'description': """ If True, only validate the relocation request
                               without executing. Defaults to False. """
                        }
                    },
                    'required': [
                        'destinationLocation'
                    ]
                }
            },
            'required': [
                'bucket',
                'request_body'
            ]
        }
    }
)
def relocate(
    bucket: str,
    request_body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Initiates a long-running Relocate Bucket operation on the specified bucket.

    This function validates the relocation request and initiates a bucket relocation operation.
    The operation moves a bucket from its current location to a specified destination location.

    Args:
        bucket (str): Name of the bucket to be relocated. Must be a valid, non-empty bucket name
            that follows Google Cloud Storage naming conventions.
        request_body (Dict[str, Any]): A dictionary representing Configuration for the bucket relocation operation.
            - destinationLocation (str): The new location to which the bucket will be moved.
              Must be a valid Google Cloud region (e.g., 'us-central1', 'europe-west1').
            - destinationCustomPlacementConfig (Optional[Dict[str, Any]]): Configuration for 
              Custom Dual Region. Optional. Contains:
                - dataLocations (List[str]): The list of regional locations that will be used 
                  to store the bucket's data. Must contain exactly 2 locations for dual-region.
            - validateOnly (Optional[bool]): If True, only validate the relocation request 
              without executing. Defaults to False.

    Returns:
        Dict[str, Any]: Dictionary representing a long-running operation:
            - done (bool): False for regular operations, True for validation-only operations.
            - error (Optional[Dict[str, Any]]): Present only if an error occurred during operation.
              Matches GoogleRpcStatus schema:
                - code (int): The status code, which should be an enum value of google.rpc.Code.
                - message (str): A developer-facing error message, which should be in English.
                - details (List[Dict[str, Any]]): A list of messages that carry the error details.
                  Each detail dictionary contains:
                    - "@type" (str): Type URL for the detail message.
                    - Additional fields specific to the error type.
            - metadata (Dict[str, Any]): Metadata related to the operation. Always contains:
                - requestedLocation (str): The destination location for the relocation.
                - validateOnly (bool): Whether this is a validation-only operation.
              For validation-only operations, additionally contains:
                - validationResult (str): Result of validation, always "Request is valid".
              For regular operations, additionally contains:
                - bucket (str): Name of the bucket being relocated.
                - operationType (str): Type of operation, always "RELOCATE_BUCKET".
                - customPlacementConfig (Optional[Dict[str, Any]]): Present only if custom 
                  placement was specified in the request. Contains:
                    - dataLocations (List[str]): The list of regional locations for data placement.
            - name (str): Unique operation name. Format varies by operation type:
              - Validation operations: "operations/relocate-bucket-{bucket}-validation"
              - Regular operations: "operations/relocate-bucket-{bucket}-{timestamp}-{random}"
            - response (Optional[Dict[str, Any]]): Result returned when operation completes.
              Only present for completed operations. Structure depends on operation outcome.
            - selfLink (str): URI of the operation resource. Format:
              - "https://storage.googleapis.com/storage/v1/operations/relocate-bucket-{bucket}-validation"
              - "https://storage.googleapis.com/storage/v1/operations/{operation_id}"
                - kind (str): Always "storage#operation".

    Raises:
        TypeError: If any argument is of an incorrect type.
        ValueError: If bucket name violates Google Cloud Storage naming conventions,
                   if request_body structure is invalid, or if required fields are missing/invalid.
        BucketNotFoundError: If the specified bucket does not exist.
    """
    # --- Input Validation ---
    
    # Validate bucket parameter
    if not isinstance(bucket, str):
        raise TypeError(f"Argument 'bucket' must be a string, got {type(bucket).__name__}.")
    
    if not bucket.strip():
        raise ValueError("Argument 'bucket' cannot be empty or contain only whitespace.")
    
    # Validate bucket name follows basic Google Cloud Storage naming conventions
    if len(bucket) < 3 or len(bucket) > 63:
        raise ValueError("Bucket name must be between 3 and 63 characters long.")
    
    if bucket.startswith('.') or bucket.endswith('.') or '..' in bucket:
        raise ValueError("Bucket name cannot start or end with dots, or contain consecutive dots.")

    # Validate request_body parameter
    if not isinstance(request_body, dict):
        raise TypeError(f"Argument 'request_body' must be a dictionary, got {type(request_body).__name__}.")

    # --- Core Logic ---
    
    # Check if bucket exists
    if bucket not in DB["buckets"]:
        raise BucketNotFoundError(f"Bucket '{bucket}' not found.")
    
    # Validate required field: destinationLocation
    if "destinationLocation" not in request_body:
        raise ValueError("Missing required field: destinationLocation")
    
    destination_location = request_body["destinationLocation"]
    if not isinstance(destination_location, str) or not destination_location.strip():
        raise ValueError("Invalid destinationLocation: must be a non-empty string")
    
    # Validate optional destinationCustomPlacementConfig
    custom_placement = request_body.get("destinationCustomPlacementConfig")
    if custom_placement is not None:
        if not isinstance(custom_placement, dict):
            raise ValueError("destinationCustomPlacementConfig must be a dictionary")
        
        if "dataLocations" in custom_placement:
            data_locations = custom_placement["dataLocations"]
            if type(data_locations).__name__ != 'list':
                raise ValueError("dataLocations must be a list")
            
            if len(data_locations) != 2:
                raise ValueError("dataLocations must contain exactly 2 locations for dual-region")
            
            if not all(isinstance(loc, str) and loc.strip() for loc in data_locations):
                raise ValueError("All dataLocations must be non-empty strings")
    
    # Validate optional validateOnly field
    validate_only = request_body.get("validateOnly", False)
    if not isinstance(validate_only, bool):
        raise ValueError("validateOnly must be a boolean")
    
    # If validation-only mode, return success without actually initiating operation
    if validate_only:
        return {
            "done": True,
            "metadata": {
                "requestedLocation": destination_location,
                "validateOnly": True,
                "validationResult": "Request is valid"
            },
            "name": f"operations/relocate-bucket-{bucket}-validation",
            "selfLink": f"https://storage.googleapis.com/storage/v1/operations/relocate-bucket-{bucket}-validation",
            "kind": "storage#operation"
        }
    
    # Generate operation ID with timestamp-like suffix for uniqueness
    import time
    import random
    operation_id = f"relocate-bucket-{bucket}-{int(time.time() * 1000)}-{random.randint(100, 999)}"
    
    # Initiate the long-running operation
    # In a real implementation, this would interact with the actual Google Cloud Storage API
    operation_response = {
        "done": False,
        "metadata": {
            "requestedLocation": destination_location,
            "validateOnly": False,
            "bucket": bucket,
            "operationType": "RELOCATE_BUCKET"
        },
        "name": f"operations/{operation_id}",
        "selfLink": f"https://storage.googleapis.com/storage/v1/operations/{operation_id}",
        "kind": "storage#operation"
    }
    
    # Add custom placement config to metadata if provided
    if custom_placement is not None:
        operation_response["metadata"]["customPlacementConfig"] = custom_placement
    
    return operation_response


@tool_spec(
    spec={
        'name': 'get_bucket_details',
        'description': """ Returns metadata for the specified bucket.
        
        This function supports conditional fetches based on metageneration and supports
        retrieval of soft-deleted buckets if specified. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'bucket': {
                    'type': 'string',
                    'description': 'Name of the bucket to retrieve metadata for.'
                },
                'generation': {
                    'type': 'string',
                    'description': """ If specified, fetches the version of the bucket
                    matching this generation. Required if soft_deleted is True. """
                },
                'soft_deleted': {
                    'type': 'boolean',
                    'description': 'If True, retrieves the soft-deleted version of the bucket.'
                },
                'if_metageneration_match': {
                    'type': 'string',
                    'description': """ Returns metadata only if the bucket's
                    metageneration matches this value. """
                },
                'if_metageneration_not_match': {
                    'type': 'string',
                    'description': """ Returns metadata only if the bucket's
                    metageneration does not match this value. """
                },
                'projection': {
                    'type': 'string',
                    'description': """ Set of properties to return. Acceptable values:
                    - "full": Includes all properties.
                    - "noAcl": Excludes owner, acl, and defaultObjectAcl. Default is "noAcl". """
                }
            },
            'required': [
                'bucket'
            ]
        }
    }
)
def get(
    bucket: str,
    generation: Optional[str] = None,
    soft_deleted: bool = False,
    if_metageneration_match: Optional[str] = None,
    if_metageneration_not_match: Optional[str] = None,
    projection: str = "noAcl"
) -> Dict[str, Any]:
    """
    Returns metadata for the specified bucket.

    This function supports conditional fetches based on metageneration and supports
    retrieval of soft-deleted buckets if specified.

    Args:
        bucket (str): Name of the bucket to retrieve metadata for.
        generation (Optional[str]): If specified, fetches the version of the bucket
            matching this generation. Required if soft_deleted is True.
        soft_deleted (bool): If True, retrieves the soft-deleted version of the bucket.
        if_metageneration_match (Optional[str]): Returns metadata only if the bucket's
            metageneration matches this value.
        if_metageneration_not_match (Optional[str]): Returns metadata only if the bucket's
            metageneration does not match this value.
        projection (str): Set of properties to return. Acceptable values:
            - "full": Includes all properties.
            - "noAcl": Excludes owner, acl, and defaultObjectAcl. Default is "noAcl".

    Returns:
        Dict[str, Any]: On a successful call, returns a dictionary containing the bucket resource.
            - "bucket" (Dict[str, Any]): A dictionary with the bucket's metadata. If 'projection' is "noAcl" (the default), `acl` and `defaultObjectAcl` are omitted. The structure includes:
                - acl (List[BucketAccessControl])
                - billing (Dict[str, bool]):
                    - requesterPays (bool)
                - cors (List[Dict[str, Any]]):
                    - maxAgeSeconds (int)
                    - method (List[str])
                    - origin (List[str])
                    - responseHeader (List[str])
                - customPlacementConfig (Dict[str, List[str]]):
                    - dataLocations (List[str])
                - defaultEventBasedHold (bool)
                - defaultObjectAcl (List[ObjectAccessControl])
                - encryption (Dict[str, str]):
                    - defaultKmsKeyName (str)
                - etag (str)
                - hierarchicalNamespace (Dict[str, bool]):
                    - enabled (bool)
                - iamConfiguration (Dict[str, Any]):
                    - bucketPolicyOnly (Dict[str, Any]):
                        - enabled (bool)
                        - lockedTime (str)
                    - uniformBucketLevelAccess (Dict[str, Any]):
                        - enabled (bool)
                        - lockedTime (str)
                    - publicAccessPrevention (str)
                - id (str)
                - ipFilter (Dict[str, Any]):
                    - mode (str)
                    - publicNetworkSource (Dict[str, List[str]]):
                        - allowedIpCidrRanges (List[str])
                    - vpcNetworkSources (List[Dict[str, Any]]):
                        - network (str)
                        - allowedIpCidrRanges (List[str])
                - kind (str)
                - labels (Dict[str, str])
                - lifecycle (Dict[str, List[Dict[str, Any]]]):
                    - rule:
                        - action (Dict[str, str]):
                            - type (str)
                            - storageClass (str)
                        - condition (Dict[str, Any]):
                            - age (int)
                            - createdBefore (str)
                            - customTimeBefore (str)
                            - daysSinceCustomTime (int)
                            - daysSinceNoncurrentTime (int)
                            - isLive (bool)
                            - matchesPattern (str)
                            - matchesPrefix (List[str])
                            - matchesSuffix (List[str])
                            - matchesStorageClass (List[str])
                            - noncurrentTimeBefore (str)
                            - numNewerVersions (int)
                - autoclass (Dict[str, Any]):
                    - enabled (bool)
                    - toggleTime (str)
                    - terminalStorageClass (str)
                    - terminalStorageClassUpdateTime (str)
                - location (str)
                - locationType (str)
                - logging (Dict[str, str]):
                    - logBucket (str)
                    - logObjectPrefix (str)
                - generation (str)
                - metageneration (str)
                - name (str)
                - owner (Dict[str, str]):
                    - entity (str)
                    - entityId (str)
                - projectNumber (str)
                - retentionPolicy (Dict[str, Any]):
                    - effectiveTime (str)
                    - isLocked (bool)
                    - retentionPeriod (str)
                - objectRetention (Dict[str, str]):
                    - mode (str)
                - rpo (str)
                - selfLink (str)
                - softDeletePolicy (Dict[str, str]):
                    - retentionDurationSeconds (str)
                    - effectiveTime (str)
                - storageClass (str)
                - timeCreated (str)
                - updated (str)
                - softDeleteTime (str)
                - hardDeleteTime (str)
                - versioning (Dict[str, bool]):
                    - enabled (bool)
                - website (Dict[str, str]):
                    - mainPageSuffix (str)
                    - notFoundPage (str)
                - satisfiesPZS (bool)
                - satisfiesPZI (bool)

    Raises:
        TypeError: If any argument is of an incorrect type.
        InvalidProjectionValueError: If 'projection' is not one of "full" or "noAcl".
        MissingGenerationError: If 'soft_deleted' is True but 'generation' is not provided.
        BucketNotFoundError: If the specified bucket does not exist.
        NotSoftDeletedError: If 'soft_deleted' is True but the bucket is not soft-deleted.
        GenerationMismatchError: If 'soft_deleted' is True and the provided 'generation' 
                                  does not match the bucket's generation.
        MetagenerationMismatchError: If 'if_metageneration_match' or
                                     'if_metageneration_not_match' conditions are not met.
    """
    # --- Input Validation Logic ---
    if not isinstance(bucket, str):
        raise TypeError("Argument 'bucket' must be a string.")
    if generation is not None and not isinstance(generation, str):
        raise TypeError("Argument 'generation' must be a string or None.")
    if not isinstance(soft_deleted, bool):
        raise TypeError("Argument 'soft_deleted' must be a boolean.")
    if if_metageneration_match is not None and not isinstance(if_metageneration_match, str):
        raise TypeError("Argument 'if_metageneration_match' must be a string or None.")
    if if_metageneration_not_match is not None and not isinstance(if_metageneration_not_match, str):
        raise TypeError("Argument 'if_metageneration_not_match' must be a string or None.")
    if not isinstance(projection, str):
        raise TypeError("Argument 'projection' must be a string.")
    
    if projection not in ("full", "noAcl"):
        raise InvalidProjectionValueError(
            f"Invalid value for 'projection': '{projection}'. Must be 'full' or 'noAcl'."
        )

    if soft_deleted and generation is None:
        raise MissingGenerationError(
            "Argument 'generation' is required when 'soft_deleted' is True."
        )
    # --- End of Input Validation Logic ---

    # --- Core Functionality ---
    if bucket not in DB["buckets"]:
        raise BucketNotFoundError(f"Bucket '{bucket}' not found.") # Raise custom error

    bucket_data = DB["buckets"][bucket]
    current_metageneration = bucket_data.get("metageneration") # Store for reuse

    if soft_deleted: # generation is guaranteed to be non-None here due to validation
        if not bucket_data.get("softDeleted"):
            raise NotSoftDeletedError(f"Bucket '{bucket}' is not soft deleted.") # Raise custom error
        if bucket_data.get("generation") != generation:
            # Include bucket name in the message for better context
            raise GenerationMismatchError(
                f"Generation mismatch for bucket '{bucket}': Required '{generation}', found '{bucket_data.get('generation')}'."
            ) # Raise custom error

    if if_metageneration_match is not None: # Changed from direct truthiness check
        if current_metageneration != if_metageneration_match:
            raise MetagenerationMismatchError(
                f"Metageneration mismatch for bucket '{bucket}': Required match '{if_metageneration_match}', found '{current_metageneration}'."
            ) # Raise custom error
            
    if if_metageneration_not_match is not None: # Changed from direct truthiness check
        if current_metageneration == if_metageneration_not_match:
            raise MetagenerationMismatchError(
                f"Metageneration mismatch for bucket '{bucket}': Required non-match '{if_metageneration_not_match}', found '{current_metageneration}'."
            ) # Raise custom error

    # If all checks pass, return the bucket data based on projection
    if projection == "full":
        return {"bucket": bucket_data}
    else:
        return {
            "bucket": {
                k: v
                for k, v in bucket_data.items()
                if k not in ["acl", "defaultObjectAcl"]
            }
        }
    # --- End of Core Functionality ---


@tool_spec(
    spec={
        'name': 'get_bucket_iam_policy',
        'description': """ Returns an IAM policy for the specified bucket.
        
        This function retrieves the IAM policy for a Google Cloud Storage bucket, with support
        for different policy format versions and proper error handling for various edge cases. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'bucket': {
                    'type': 'string',
                    'description': """ Name of the bucket whose IAM policy is being requested. Must be a valid,
                    non-empty bucket name that follows Google Cloud Storage naming conventions. """
                },
                'options_requested_policy_version': {
                    'type': 'integer',
                    'description': """ The desired IAM policy format version
                    to be returned. Must be >= 1 if specified. Defaults to None (latest version).
                    Different versions may have different field structures and capabilities. """
                },
                'user_project': {
                    'type': 'string',
                    'description': """ The project to be billed for this request. Required for
                    Requester Pays buckets. Must be a valid project identifier if specified. """
                }
            },
            'required': [
                'bucket'
            ]
        }
    }
)
def getIamPolicy(
    bucket: str,
    options_requested_policy_version: Optional[int] = None,
    user_project: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns an IAM policy for the specified bucket.

    This function retrieves the IAM policy for a Google Cloud Storage bucket, with support
    for different policy format versions and proper error handling for various edge cases.

    Args:
        bucket (str): Name of the bucket whose IAM policy is being requested. Must be a valid,
            non-empty bucket name that follows Google Cloud Storage naming conventions.
        options_requested_policy_version (Optional[int]): The desired IAM policy format version
            to be returned. Must be >= 1 if specified. Defaults to None (latest version).
            Different versions may have different field structures and capabilities.
        user_project (Optional[str]): The project to be billed for this request. Required for
            Requester Pays buckets. Must be a valid project identifier if specified.

    Returns:
        Dict[str, Any]: Dictionary with an "iamPolicy" key containing:
            - iamPolicy (Dict[str, Any]): A complete policy object describing access control for the bucket.
                - bindings (List[Dict[str, Any]]): List of role-member mappings with optional conditions.
                  Each binding dictionary contains:
                    - role (str): The IAM role string (e.g., "roles/storage.admin", "roles/storage.objectViewer").
                    - members (List[str]): List of member identifiers. Each member can be:
                        - "user:email@example.com"
                        - "group:group@example.com"
                        - "serviceAccount:service@project.iam.gserviceaccount.com"
                        - "domain:example.com"
                        - "allUsers"
                        - "allAuthenticatedUsers"
                    - condition (Optional[Dict[str, Any]]): An optional condition that restricts when the binding is applied.
                      Contains:
                        - title (str): Short label for the expression (max 100 characters).
                        - description (Optional[str]): Optional description of the expression's intent (max 256 characters).
                        - expression (str): Common Expression Language (CEL) syntax string that defines the condition.
                        - location (Optional[str]): Optional location string for debugging (e.g., file or position).
                - etag (str): HTTP 1.1 entity tag for the policy. Used for optimistic concurrency control.
                - kind (str): Resource kind, always "storage#policy".
                - resourceId (str): The full resource ID the policy applies to (format: "projects/_/buckets/{bucket}").
                - version (int): IAM policy format version. Determines which features are available:
                    - Version 1: Basic role bindings
                    - Version 3: Role bindings with conditions (conditional IAM)

    Raises:
        TypeError: If any argument is of an incorrect type.
        ValueError: If bucket name violates Google Cloud Storage naming conventions,
                   if user_project format is invalid, or if policy version is invalid.
        BucketNotFoundError: If the specified bucket does not exist.
    """
    # --- Input Validation ---
    
    # Validate bucket parameter
    if not isinstance(bucket, str):
        raise TypeError(f"Argument 'bucket' must be a string, got {type(bucket).__name__}.")
    
    if not bucket.strip():
        raise ValueError("Argument 'bucket' cannot be empty or contain only whitespace.")
    
    # Validate bucket name follows basic Google Cloud Storage naming conventions
    if len(bucket) < 3 or len(bucket) > 63:
        raise ValueError("Bucket name must be between 3 and 63 characters long.")
    
    if bucket.startswith('.') or bucket.endswith('.') or '..' in bucket:
        raise ValueError("Bucket name cannot start or end with dots, or contain consecutive dots.")
    
    # Validate options_requested_policy_version parameter
    if options_requested_policy_version is not None:
        if not isinstance(options_requested_policy_version, int):
            raise TypeError(f"Argument 'options_requested_policy_version' must be an integer or None, got {type(options_requested_policy_version).__name__}.")
        if options_requested_policy_version < 1:
            raise ValueError("Argument 'options_requested_policy_version' must be >= 1 if specified.")
    
    # Validate user_project parameter
    if user_project is not None:
        if not isinstance(user_project, str):
            raise TypeError(f"Argument 'user_project' must be a string or None, got {type(user_project).__name__}.")
        if not user_project.strip():
            raise ValueError("Argument 'user_project' cannot be empty or contain only whitespace if specified.")
    
    # --- Core Logic ---
    
    # Check if bucket exists
    if bucket not in DB["buckets"]:
        raise BucketNotFoundError(f"Bucket '{bucket}' not found.")

    bucket_data = DB["buckets"][bucket]
    
    # Get existing IAM policy or create default structure
    existing_policy = bucket_data.get("iamPolicy", {})
    
    # Determine the policy version to use
    if options_requested_policy_version is not None:
        policy_version = options_requested_policy_version
    else:
        # Use existing version or default to version 1
        policy_version = existing_policy.get("version", 1)
    
    # Ensure policy version is valid (1 or 3 are commonly supported)
    if policy_version not in [1, 3]:
        raise ValueError(f"Invalid policy version: {policy_version}. Supported versions are 1 and 3.")
    
    # Build the complete IAM policy structure
    bindings = existing_policy.get("bindings", [])
    
    # Filter bindings based on policy version capabilities
    if policy_version == 1:
        # Version 1 doesn't support conditions, filter them out
        filtered_bindings = []
        for binding in bindings:
            filtered_binding = {
                "role": binding.get("role", ""),
                "members": binding.get("members", [])
            }
            # Don't include condition for version 1
            filtered_bindings.append(filtered_binding)
        bindings = filtered_bindings
    elif policy_version == 3:
        # Version 3 supports conditions, include all binding data
        bindings = bindings  # Use as-is, conditions are supported
    
    # Generate etag for the policy
    import hashlib
    import json
    policy_content = json.dumps({"bindings": bindings, "version": policy_version}, sort_keys=True)
    etag = hashlib.md5(policy_content.encode()).hexdigest()
    
    # Construct the complete policy response
    iam_policy = {
        "bindings": bindings,
        "etag": etag,
        "kind": "storage#policy",
        "resourceId": f"projects/_/buckets/{bucket}",
        "version": policy_version
    }
    
    return {"iamPolicy": iam_policy}


@tool_spec(
    spec={
        'name': 'get_bucket_storage_layout',
        'description': """ Returns the storage layout configuration for the specified bucket.
        
        This function retrieves the storage layout information for a Google Cloud Storage bucket,
        with optional prefix-based access validation. The operation validates the requirement
        for `storage.objects.list` permission and validates access based on the specified prefix. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'bucket': {
                    'type': 'string',
                    'description': """ Name of the bucket whose storage layout is to be retrieved. Must be a valid,
                    non-empty bucket name that follows Google Cloud Storage naming conventions. """
                },
                'prefix': {
                    'type': 'string',
                    'description': """ Optional prefix used for permission checks and access validation.
                    When specified, the function validates that the caller would have permission to access
                    objects under this prefix path within the bucket. Must follow valid object naming
                    conventions if provided. Defaults to None (no prefix restriction). """
                }
            },
            'required': [
                'bucket'
            ]
        }
    }
)
def getStorageLayout(bucket: str, prefix: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns the storage layout configuration for the specified bucket.

    This function retrieves the storage layout information for a Google Cloud Storage bucket,
    with optional prefix-based access validation. The operation validates the requirement
    for `storage.objects.list` permission and validates access based on the specified prefix.

    Args:
        bucket (str): Name of the bucket whose storage layout is to be retrieved. Must be a valid,
            non-empty bucket name that follows Google Cloud Storage naming conventions.
        prefix (Optional[str]): Optional prefix used for permission checks and access validation.
            When specified, the function validates that the caller would have permission to access
            objects under this prefix path within the bucket. Must follow valid object naming
            conventions if provided. Defaults to None (no prefix restriction).

    Returns:
        Dict[str, Any]: Always returns a dictionary with a "storageLayout" key on success:
            - storageLayout (Dict[str, Any]): Complete storage layout configuration containing:
                - bucket (str): The name of the bucket that this layout applies to.
                - customPlacementConfig (Dict[str, List[str]]): Custom placement configuration for the bucket.
                    - dataLocations (List[str]): List of regional locations where bucket data is placed.
                      For single-region buckets, contains one location. For dual-region buckets,
                      contains exactly two locations. For multi-region buckets, contains multiple locations.
                - hierarchicalNamespace (Dict[str, bool]): Hierarchical namespace configuration.
                    - enabled (bool): True if hierarchical namespace is enabled for the bucket,
                      allowing folder-like organization. False for standard flat namespace.
                - kind (str): Resource type identifier, always "storage#storageLayout".
                - location (str): The primary physical location or region of the bucket
                  (e.g., "us-central1", "us", "eu").
                - locationType (str): Type of location configuration describing the bucket's
                  geographic distribution. Possible values:
                    - "region": Single region bucket
                    - "dual-region": Dual-region bucket spanning two specific regions
                    - "multi-region": Multi-region bucket (e.g., US, EU, ASIA)

    Raises:
        TypeError: If any argument is of an incorrect type.
        ValueError: If bucket name violates Google Cloud Storage naming conventions,
                   if prefix format is invalid, or if access is denied for the specified prefix.
        BucketNotFoundError: If the specified bucket does not exist.
    """
    # --- Input Validation ---
    
    # Validate bucket parameter
    if not isinstance(bucket, str):
        raise TypeError(f"Argument 'bucket' must be a string, got {type(bucket).__name__}.")
    
    if not bucket.strip():
        raise ValueError("Argument 'bucket' cannot be empty or contain only whitespace.")
    
    # Validate bucket name follows basic Google Cloud Storage naming conventions
    if len(bucket) < 3 or len(bucket) > 63:
        raise ValueError("Bucket name must be between 3 and 63 characters long.")
    
    if bucket.startswith('.') or bucket.endswith('.') or '..' in bucket:
        raise ValueError("Bucket name cannot start or end with dots, or contain consecutive dots.")
    
    # Validate prefix parameter
    if prefix is not None:
        if not isinstance(prefix, str):
            raise TypeError(f"Argument 'prefix' must be a string or None, got {type(prefix).__name__}.")
        
        # Basic prefix format validation
        if prefix.strip() == "":
            raise ValueError("Argument 'prefix' cannot be empty or contain only whitespace if specified.")
        
        # Check for invalid characters in prefix (basic validation)
        invalid_chars = ['\r', '\n', '\0']
        if any(char in prefix for char in invalid_chars):
            raise ValueError("Argument 'prefix' contains invalid characters (carriage return, newline, or null).")
    
    # --- Core Logic ---
    
    # Check if bucket exists
    if bucket not in DB["buckets"]:
        raise BucketNotFoundError(f"Bucket '{bucket}' not found.")
    
    bucket_data = DB["buckets"][bucket]
    
    # Prefix-based permission validation
    if prefix is not None:
        # Access validation based on prefix
        bucket_objects = bucket_data.get("objects", [])
        
        # Check if prefix starts with slash (invalid - no absolute paths)
        if prefix.startswith('/'):
            raise ValueError("Argument 'prefix' cannot start with '/' (absolute paths not allowed).")
        
        # Permission check: if prefix is specified, check if any objects match
        # or if the prefix represents a valid path pattern
        has_matching_objects = any(
            str(obj).startswith(prefix) for obj in bucket_objects
        ) if bucket_objects else True  # Allow if no objects exist yet
        
        # Access denied for certain restricted prefixes
        restricted_prefixes = ["admin/", "system/", ".config/"]
        if any(prefix.startswith(restricted) for restricted in restricted_prefixes):
            raise ValueError(f"Access denied for prefix '{prefix}'. Restricted prefixes: {restricted_prefixes}")
        
        # Additional validation: prefix length check (practical limits)
        if len(prefix) > 1024:
            raise ValueError("Argument 'prefix' cannot exceed 1024 characters.")
    
    # Get existing storage layout configuration or create default structure
    existing_layout = bucket_data.get("storageLayout", {})
    
    # Determine bucket location and type from bucket data or defaults
    bucket_location = bucket_data.get("location", "us-central1")
    bucket_location_type = bucket_data.get("locationType", "region")
    
    # Determine custom placement config
    custom_placement = existing_layout.get("customPlacementConfig", {})
    if not custom_placement:
        # Create default placement based on location type
        if bucket_location_type == "dual-region":
            custom_placement = {
                "dataLocations": ["us-central1", "us-east1"]
            }
        elif bucket_location_type == "multi-region":
            if bucket_location.startswith("us"):
                custom_placement = {
                    "dataLocations": ["us-central1", "us-east1", "us-west1"]
                }
            elif bucket_location.startswith("eu"):
                custom_placement = {
                    "dataLocations": ["europe-west1", "europe-west4", "europe-north1"]
                }
            else:
                custom_placement = {
                    "dataLocations": [bucket_location]
                }
        else:
            # Single region
            custom_placement = {
                "dataLocations": [bucket_location]
            }
    
    # Determine hierarchical namespace setting
    hierarchical_ns = existing_layout.get("hierarchicalNamespace", {})
    if not hierarchical_ns:
        # Default to disabled for most buckets
        hierarchical_ns = {
            "enabled": bucket_data.get("enableHierarchicalNamespace", False)
        }
    
    # Construct the complete storage layout response
    storage_layout = {
        "bucket": bucket,
        "customPlacementConfig": custom_placement,
        "hierarchicalNamespace": hierarchical_ns,
        "kind": "storage#storageLayout",
        "location": bucket_location,
        "locationType": bucket_location_type
    }
    
    return {"storageLayout": storage_layout}


@tool_spec(
    spec={
        'name': 'create_bucket',
        'description': 'Creates a new bucket.',
        'parameters': {
            'type': 'object',
            'properties': {
                'project': {
                    'type': 'string',
                    'description': 'A valid API project identifier.'
                },
                'bucket_request': {
                    'type': 'object',
                    'description': """ A dictionary representing the bucket properties
                    to create. Will be validated against the BucketRequest model. If not provided, a default
                    bucket with auto-generated name will be created. Supported keys:
                    Defaults to None. """,
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'Bucket name (required if provided)'
                        },
                        'storageClass': {
                            'type': 'string',
                            'description': 'Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE, etc.)'
                        },
                        'location': {
                            'type': 'string',
                            'description': 'Bucket location'
                        },
                        'billing': {
                            'type': 'object',
                            'description': 'Billing configuration',
                            'properties': {
                                'requesterPays': {
                                    'type': 'boolean',
                                    'description': 'Whether requester pays is enabled'
                                }
                            },
                            'required': [
                                'requesterPays'
                            ]
                        },
                        'cors': {
                            'type': 'array',
                            'description': 'CORS configuration rules',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'maxAgeSeconds': {
                                        'type': 'integer',
                                        'description': 'Max age for preflight cache'
                                    },
                                    'method': {
                                        'type': 'array',
                                        'description': 'HTTP methods allowed',
                                        'items': {
                                            'type': 'string'
                                        }
                                    },
                                    'origin': {
                                        'type': 'array',
                                        'description': 'Origins allowed',
                                        'items': {
                                            'type': 'string'
                                        }
                                    },
                                    'responseHeader': {
                                        'type': 'array',
                                        'description': 'Headers allowed in response',
                                        'items': {
                                            'type': 'string'
                                        }
                                    }
                                },
                                'required': [
                                    'maxAgeSeconds',
                                    'method',
                                    'origin',
                                    'responseHeader'
                                ]
                            }
                        },
                        'customPlacementConfig': {
                            'type': 'object',
                            'description': 'Custom dual region placement',
                            'properties': {
                                'dataLocations': {
                                    'type': 'array',
                                    'description': 'List of regional locations',
                                    'items': {
                                        'type': 'string'
                                    }
                                }
                            },
                            'required': [
                                'dataLocations'
                            ]
                        },
                        'hierarchicalNamespace': {
                            'type': 'object',
                            'description': 'Hierarchical namespace config',
                            'properties': {
                                'enabled': {
                                    'type': 'boolean',
                                    'description': 'Whether hierarchical namespace is enabled'
                                }
                            },
                            'required': [
                                'enabled'
                            ]
                        },
                        'iamConfiguration': {
                            'type': 'object',
                            'description': 'IAM configuration',
                            'properties': {
                                'uniformBucketLevelAccess': {
                                    'type': 'object',
                                    'description': 'Uniform bucket-level access config',
                                    'properties': {
                                        'enabled': {
                                            'type': 'boolean',
                                            'description': 'Whether enabled'
                                        },
                                        'lockedTime': {
                                            'type': 'string',
                                            'description': 'When it was locked (RFC 3339 format)'
                                        }
                                    },
                                    'required': [
                                        'enabled',
                                        'lockedTime'
                                    ]
                                },
                                'bucketPolicyOnly': {
                                    'type': 'object',
                                    'description': 'Legacy bucket policy only config',
                                    'properties': {
                                        'enabled': {
                                            'type': 'boolean',
                                            'description': 'Whether enabled'
                                        },
                                        'lockedTime': {
                                            'type': 'string',
                                            'description': 'When it was locked (RFC 3339 format)'
                                        }
                                    },
                                    'required': [
                                        'enabled',
                                        'lockedTime'
                                    ]
                                },
                                'publicAccessPrevention': {
                                    'type': 'string',
                                    'description': 'Public access prevention ("inherited" or "enforced")'
                                }
                            },
                            'required': [
                                'uniformBucketLevelAccess',
                                'bucketPolicyOnly',
                                'publicAccessPrevention'
                            ]
                        },
                        'ipFilter': {
                            'type': 'object',
                            'description': 'IP filter configuration',
                            'properties': {
                                'mode': {
                                    'type': 'string',
                                    'description': 'Filter mode ("Enabled" or "Disabled")'
                                },
                                'publicNetworkSource': {
                                    'type': 'object',
                                    'description': 'Public network sources',
                                    'properties': {
                                        'allowedIpCidrRanges': {
                                            'type': 'array',
                                            'description': 'List of allowed IP CIDR ranges',
                                            'items': {
                                                'type': 'string'
                                            }
                                        }
                                    },
                                    'required': [
                                        'allowedIpCidrRanges'
                                    ]
                                },
                                'vpcNetworkSources': {
                                    'type': 'array',
                                    'description': 'VPC network sources',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'network': {
                                                'type': 'string',
                                                'description': 'VPC network resource name'
                                            },
                                            'allowedIpCidrRanges': {
                                                'type': 'array',
                                                'description': 'List of allowed IP CIDR ranges',
                                                'items': {
                                                    'type': 'string'
                                                }
                                            }
                                        },
                                        'required': [
                                            'network',
                                            'allowedIpCidrRanges'
                                        ]
                                    }
                                }
                            },
                            'required': [
                                'mode',
                                'publicNetworkSource',
                                'vpcNetworkSources'
                            ]
                        },
                        'lifecycle': {
                            'type': 'object',
                            'description': 'Lifecycle management rules',
                            'properties': {
                                'rule': {
                                    'type': 'array',
                                    'description': 'List of lifecycle rules',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'action': {
                                                'type': 'object',
                                                'description': 'Action to take',
                                                'properties': {
                                                    'type': {
                                                        'type': 'string',
                                                        'description': 'Action type (Delete, SetStorageClass, AbortIncompleteMultipartUpload)'
                                                    },
                                                    'storageClass': {
                                                        'type': 'string',
                                                        'description': 'Target storage class for SetStorageClass action'
                                                    }
                                                },
                                                'required': [
                                                    'type',
                                                    'storageClass'
                                                ]
                                            },
                                            'condition': {
                                                'type': 'object',
                                                'description': 'Conditions for applying the rule',
                                                'properties': {
                                                    'age': {
                                                        'type': 'integer',
                                                        'description': 'Age of object in days'
                                                    },
                                                    'createdBefore': {
                                                        'type': 'string',
                                                        'description': 'Date in RFC 3339 format'
                                                    },
                                                    'customTimeBefore': {
                                                        'type': 'string',
                                                        'description': 'Date in RFC 3339 format'
                                                    },
                                                    'daysSinceCustomTime': {
                                                        'type': 'integer',
                                                        'description': 'Days since custom time'
                                                    },
                                                    'daysSinceNoncurrentTime': {
                                                        'type': 'integer',
                                                        'description': 'Days since noncurrent time'
                                                    },
                                                    'isLive': {
                                                        'type': 'boolean',
                                                        'description': 'Whether object is live'
                                                    },
                                                    'matchesPattern': {
                                                        'type': 'string',
                                                        'description': 'Regular expression pattern'
                                                    },
                                                    'matchesPrefix': {
                                                        'type': 'array',
                                                        'description': 'Object name prefixes',
                                                        'items': {
                                                            'type': 'string'
                                                        }
                                                    },
                                                    'matchesSuffix': {
                                                        'type': 'array',
                                                        'description': 'Object name suffixes',
                                                        'items': {
                                                            'type': 'string'
                                                        }
                                                    },
                                                    'matchesStorageClass': {
                                                        'type': 'array',
                                                        'description': 'Storage classes to match',
                                                        'items': {
                                                            'type': 'string'
                                                        }
                                                    },
                                                    'noncurrentTimeBefore': {
                                                        'type': 'string',
                                                        'description': 'Date in RFC 3339 format'
                                                    },
                                                    'numNewerVersions': {
                                                        'type': 'integer',
                                                        'description': 'Number of newer versions'
                                                    }
                                                },
                                                'required': [
                                                    'age',
                                                    'createdBefore',
                                                    'customTimeBefore',
                                                    'daysSinceCustomTime',
                                                    'daysSinceNoncurrentTime',
                                                    'isLive',
                                                    'matchesPattern',
                                                    'matchesPrefix',
                                                    'matchesSuffix',
                                                    'matchesStorageClass',
                                                    'noncurrentTimeBefore',
                                                    'numNewerVersions'
                                                ]
                                            }
                                        },
                                        'required': [
                                            'action',
                                            'condition'
                                        ]
                                    }
                                }
                            },
                            'required': [
                                'rule'
                            ]
                        },
                        'autoclass': {
                            'type': 'object',
                            'description': 'Autoclass configuration',
                            'properties': {
                                'enabled': {
                                    'type': 'boolean',
                                    'description': 'Whether autoclass is enabled'
                                },
                                'toggleTime': {
                                    'type': 'string',
                                    'description': 'Time autoclass was toggled (RFC 3339 format)'
                                },
                                'terminalStorageClass': {
                                    'type': 'string',
                                    'description': 'Terminal storage class (NEARLINE or ARCHIVE)'
                                },
                                'terminalStorageClassUpdateTime': {
                                    'type': 'string',
                                    'description': 'Time terminal class was updated (RFC 3339)'
                                }
                            },
                            'required': [
                                'enabled',
                                'toggleTime',
                                'terminalStorageClass',
                                'terminalStorageClassUpdateTime'
                            ]
                        },
                        'versioning': {
                            'type': 'object',
                            'description': 'Versioning configuration',
                            'properties': {
                                'enabled': {
                                    'type': 'boolean',
                                    'description': 'Whether versioning is enabled'
                                }
                            },
                            'required': [
                                'enabled'
                            ]
                        },
                        'website': {
                            'type': 'object',
                            'description': 'Website configuration',
                            'properties': {
                                'mainPageSuffix': {
                                    'type': 'string',
                                    'description': 'Main page suffix (e.g., "index.html")'
                                },
                                'notFoundPage': {
                                    'type': 'string',
                                    'description': '404 page (e.g., "404.html")'
                                }
                            },
                            'required': [
                                'mainPageSuffix',
                                'notFoundPage'
                            ]
                        },
                        'logging': {
                            'type': 'object',
                            'description': 'Access logging configuration',
                            'properties': {
                                'logBucket': {
                                    'type': 'string',
                                    'description': 'Destination bucket for logs'
                                },
                                'logObjectPrefix': {
                                    'type': 'string',
                                    'description': 'Prefix for log objects'
                                }
                            },
                            'required': [
                                'logBucket',
                                'logObjectPrefix'
                            ]
                        },
                        'retentionPolicy': {
                            'type': 'object',
                            'description': 'Retention policy',
                            'properties': {
                                'effectiveTime': {
                                    'type': 'string',
                                    'description': 'When policy became effective (RFC 3339 format)'
                                },
                                'isLocked': {
                                    'type': 'boolean',
                                    'description': 'Whether policy is locked'
                                },
                                'retentionPeriod': {
                                    'type': 'string',
                                    'description': 'Retention period in seconds'
                                }
                            },
                            'required': [
                                'effectiveTime',
                                'isLocked',
                                'retentionPeriod'
                            ]
                        },
                        'objectRetention': {
                            'type': 'object',
                            'description': 'Object retention configuration',
                            'properties': {
                                'mode': {
                                    'type': 'string',
                                    'description': 'Object retention mode'
                                }
                            },
                            'required': [
                                'mode'
                            ]
                        },
                        'softDeletePolicy': {
                            'type': 'object',
                            'description': 'Soft delete policy',
                            'properties': {
                                'retentionDurationSeconds': {
                                    'type': 'string',
                                    'description': 'Retention duration in seconds'
                                },
                                'effectiveTime': {
                                    'type': 'string',
                                    'description': 'When policy became effective (RFC 3339 format)'
                                }
                            },
                            'required': [
                                'retentionDurationSeconds',
                                'effectiveTime'
                            ]
                        },
                        'encryption': {
                            'type': 'object',
                            'description': 'Encryption configuration',
                            'properties': {
                                'defaultKmsKeyName': {
                                    'type': 'string',
                                    'description': 'Default KMS key resource name'
                                }
                            },
                            'required': [
                                'defaultKmsKeyName'
                            ]
                        },
                        'owner': {
                            'type': 'object',
                            'description': 'Bucket owner information',
                            'properties': {
                                'entity': {
                                    'type': 'string',
                                    'description': 'Owner entity'
                                },
                                'entityId': {
                                    'type': 'string',
                                    'description': 'Owner entity ID'
                                }
                            },
                            'required': [
                                'entity',
                                'entityId'
                            ]
                        },
                        'labels': {
                            'type': 'object',
                            'description': """ User-defined labels as arbitrary key-value pairs where:
                                 - Keys are user-defined strings (max 63 characters)
                                - Values are user-defined strings (max 63 characters) """,
                            'properties': {},
                            'required': []
                        },
                        'defaultEventBasedHold': {
                            'type': 'boolean',
                            'description': 'Default event-based hold for new objects'
                        },
                        'rpo': {
                            'type': 'string',
                            'description': 'Recovery Point Objective ("DEFAULT" or "ASYNC_TURBO")'
                        },
                        'locationType': {
                            'type': 'string',
                            'description': 'Type of location (e.g., "region", "dual-region")'
                        },
                        'projectNumber': {
                            'type': 'string',
                            'description': 'Project number bucket belongs to'
                        },
                        'satisfiesPZS': {
                            'type': 'boolean',
                            'description': 'Whether bucket satisfies Zone Separation'
                        },
                        'satisfiesPZI': {
                            'type': 'boolean',
                            'description': 'Whether bucket satisfies Zone Isolation'
                        }
                    },
                    'required': [
                        'name',
                        'storageClass',
                        'location',
                        'billing',
                        'cors',
                        'customPlacementConfig',
                        'hierarchicalNamespace',
                        'iamConfiguration',
                        'ipFilter',
                        'lifecycle',
                        'autoclass',
                        'versioning',
                        'website',
                        'logging',
                        'retentionPolicy',
                        'objectRetention',
                        'softDeletePolicy',
                        'encryption',
                        'owner',
                        'labels',
                        'defaultEventBasedHold',
                        'rpo',
                        'locationType',
                        'projectNumber',
                        'satisfiesPZS',
                        'satisfiesPZI'
                    ]
                },
                'predefinedAcl': {
                    'type': 'string',
                    'description': """ Apply a predefined set of access controls to this bucket.
                    Valid values:
                    - "authenticatedRead": Project team owners get OWNER access, allAuthenticatedUsers get READER access
                    - "private": Project team owners get OWNER access
                    - "projectPrivate": Project team members get access according to their roles
                    - "publicRead": Project team owners get OWNER access, allUsers get READER access
                    - "publicReadWrite": Project team owners get OWNER access, allUsers get WRITER access
                    Defaults to None. """
                },
                'predefined_default_object_acl': {
                    'type': 'string',
                    'description': """ Apply a predefined set of default object
                    access controls to this bucket. Valid values:
                    - "authenticatedRead": Object owner gets OWNER access, allAuthenticatedUsers get READER access
                    - "bucketOwnerFullControl": Object owner gets OWNER access, project team owners get OWNER access
                    - "bucketOwnerRead": Object owner gets OWNER access, project team owners get READER access
                    - "private": Object owner gets OWNER access
                    - "projectPrivate": Object owner gets OWNER access, project team members get access according to roles
                    - "publicRead": Object owner gets OWNER access, allUsers get READER access
                    Defaults to None. """
                },
                'projection': {
                    'type': 'string',
                    'description': """ Set of properties to return in the response. Valid values:
                    - "full": Include all properties
                    - "noAcl": Omit owner, acl and defaultObjectAcl properties
                    Defaults to "noAcl". """
                },
                'user_project': {
                    'type': 'string',
                    'description': """ The project to be billed for this request. Required for
                    Requester Pays buckets. Defaults to None. """
                },
                'enableObjectRetention': {
                    'type': 'boolean',
                    'description': """ If True, enables object retention on the bucket.
                    Defaults to False. """
                }
            },
            'required': [
                'project'
            ]
        }
    }
)
def insert(
    project: str,
    bucket_request: Optional[Dict[str, Any]] = None,
    predefinedAcl: Optional[str] = None,
    predefined_default_object_acl: Optional[str] = None,
    projection: str = "noAcl",
    user_project: Optional[str] = None,
    enableObjectRetention: bool = False,
) -> Dict[str, Any]:
    """
    Creates a new bucket.

    Args:
        project (str): A valid API project identifier.
        bucket_request (Optional[Dict[str, Any]]): A dictionary representing the bucket properties
            to create. Will be validated against the BucketRequest model. If not provided, a default
            bucket with auto-generated name will be created. Supported keys:
            - name (str): Bucket name (required if provided)
            - storageClass (str): Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE, etc.)
            - location (str): Bucket location
            - billing (Dict[str, bool]): Billing configuration
                - requesterPays (bool): Whether requester pays is enabled
            - cors (List[Dict[str, Any]]): CORS configuration rules
                - maxAgeSeconds (int): Max age for preflight cache
                - method (List[str]): HTTP methods allowed
                - origin (List[str]): Origins allowed
                - responseHeader (List[str]): Headers allowed in response
            - customPlacementConfig (Dict[str, List[str]]): Custom dual region placement
                - dataLocations (List[str]): List of regional locations
            - hierarchicalNamespace (Dict[str, bool]): Hierarchical namespace config
                - enabled (bool): Whether hierarchical namespace is enabled
            - iamConfiguration (Dict[str, Any]): IAM configuration
                - uniformBucketLevelAccess (Dict[str, Any]): Uniform bucket-level access config
                    - enabled (bool): Whether enabled
                    - lockedTime (str): When it was locked (RFC 3339 format)
                - bucketPolicyOnly (Dict[str, Any]): Legacy bucket policy only config
                    - enabled (bool): Whether enabled
                    - lockedTime (str): When it was locked (RFC 3339 format)
                - publicAccessPrevention (str): Public access prevention ("inherited" or "enforced")
            - ipFilter (Dict[str, Any]): IP filter configuration
                - mode (str): Filter mode ("Enabled" or "Disabled")
                - publicNetworkSource (Dict[str, List[str]]): Public network sources
                    - allowedIpCidrRanges (List[str]): List of allowed IP CIDR ranges
                - vpcNetworkSources (List[Dict[str, Any]]): VPC network sources
                    - network (str): VPC network resource name
                    - allowedIpCidrRanges (List[str]): List of allowed IP CIDR ranges
            - lifecycle (Dict[str, List[Dict[str, Any]]]): Lifecycle management rules
                - rule (List[Dict[str, Any]]): List of lifecycle rules
                    - action (Dict[str, str]): Action to take
                        - type (str): Action type (Delete, SetStorageClass, AbortIncompleteMultipartUpload)
                        - storageClass (str): Target storage class for SetStorageClass action
                    - condition (Dict[str, Any]): Conditions for applying the rule
                        - age (int): Age of object in days
                        - createdBefore (str): Date in RFC 3339 format
                        - customTimeBefore (str): Date in RFC 3339 format
                        - daysSinceCustomTime (int): Days since custom time
                        - daysSinceNoncurrentTime (int): Days since noncurrent time
                        - isLive (bool): Whether object is live
                        - matchesPattern (str): Regular expression pattern
                        - matchesPrefix (List[str]): Object name prefixes
                        - matchesSuffix (List[str]): Object name suffixes
                        - matchesStorageClass (List[str]): Storage classes to match
                        - noncurrentTimeBefore (str): Date in RFC 3339 format
                        - numNewerVersions (int): Number of newer versions
            - autoclass (Dict[str, Any]): Autoclass configuration
                - enabled (bool): Whether autoclass is enabled
                - toggleTime (str): Time autoclass was toggled (RFC 3339 format)
                - terminalStorageClass (str): Terminal storage class (NEARLINE or ARCHIVE)
                - terminalStorageClassUpdateTime (str): Time terminal class was updated (RFC 3339)
            - versioning (Dict[str, bool]): Versioning configuration
                - enabled (bool): Whether versioning is enabled
            - website (Dict[str, str]): Website configuration
                - mainPageSuffix (str): Main page suffix (e.g., "index.html")
                - notFoundPage (str): 404 page (e.g., "404.html")
            - logging (Dict[str, str]): Access logging configuration
                - logBucket (str): Destination bucket for logs
                - logObjectPrefix (str): Prefix for log objects
            - retentionPolicy (Dict[str, Any]): Retention policy
                - effectiveTime (str): When policy became effective (RFC 3339 format)
                - isLocked (bool): Whether policy is locked
                - retentionPeriod (str): Retention period in seconds
            - objectRetention (Dict[str, str]): Object retention configuration
                - mode (str): Object retention mode
            - softDeletePolicy (Dict[str, str]): Soft delete policy
                - retentionDurationSeconds (str): Retention duration in seconds
                - effectiveTime (str): When policy became effective (RFC 3339 format)
            - encryption (Dict[str, str]): Encryption configuration
                - defaultKmsKeyName (str): Default KMS key resource name
            - owner (Dict[str, str]): Bucket owner information
                - entity (str): Owner entity
                - entityId (str): Owner entity ID
            - labels (Dict[str, str]): User-defined labels as arbitrary key-value pairs where:
                - Keys are user-defined strings (max 63 characters)
                - Values are user-defined strings (max 63 characters)
            - defaultEventBasedHold (bool): Default event-based hold for new objects
            - rpo (str): Recovery Point Objective ("DEFAULT" or "ASYNC_TURBO")
            - locationType (str): Type of location (e.g., "region", "dual-region")
            - projectNumber (str): Project number bucket belongs to
            - satisfiesPZS (bool): Whether bucket satisfies Zone Separation
            - satisfiesPZI (bool): Whether bucket satisfies Zone Isolation
            Defaults to None.
        predefinedAcl (Optional[str]): Apply a predefined set of access controls to this bucket.
            Valid values:
            - "authenticatedRead": Project team owners get OWNER access, allAuthenticatedUsers get READER access
            - "private": Project team owners get OWNER access
            - "projectPrivate": Project team members get access according to their roles
            - "publicRead": Project team owners get OWNER access, allUsers get READER access
            - "publicReadWrite": Project team owners get OWNER access, allUsers get WRITER access
            Defaults to None.
        predefined_default_object_acl (Optional[str]): Apply a predefined set of default object
            access controls to this bucket. Valid values:
            - "authenticatedRead": Object owner gets OWNER access, allAuthenticatedUsers get READER access
            - "bucketOwnerFullControl": Object owner gets OWNER access, project team owners get OWNER access
            - "bucketOwnerRead": Object owner gets OWNER access, project team owners get READER access
            - "private": Object owner gets OWNER access
            - "projectPrivate": Object owner gets OWNER access, project team members get access according to roles
            - "publicRead": Object owner gets OWNER access, allUsers get READER access
            Defaults to None.
        projection (str): Set of properties to return in the response. Valid values:
            - "full": Include all properties
            - "noAcl": Omit owner, acl and defaultObjectAcl properties
            Defaults to "noAcl".
        user_project (Optional[str]): The project to be billed for this request. Required for
            Requester Pays buckets. Defaults to None.
        enableObjectRetention (bool): If True, enables object retention on the bucket.
            Defaults to False.

    Returns:
        Dict[str, Any]:
        - On success (if projection is "full" otherwise `acl` and `defaultObjectAcl` are omitted):
            - "bucket" (Dict[str, Any]) with the following keys:
                - name (str): Bucket name
                - id (str): Bucket ID
                - kind (str): Resource kind (always "storage#bucket")
                - storageClass (str): Current storage class
                - location (str): Bucket location
                - metageneration (str): Current metageneration (incremented after update)
                - generation (str): Bucket generation
                - timeCreated (str): Creation time (RFC 3339 format)
                - updated (str): Last update time (RFC 3339 format)
                - etag (str): Entity tag for the bucket
                - projectNumber (str): Project number
                - acl (List[Dict[str, Any]]): Access control list (omitted if projection="noAcl")
                    - bucket (str): Name of the bucket
                    - domain (str): Domain associated with the entity
                    - email (str): Email address associated with the entity
                    - entity (str): The entity holding the permission
                    - entityId (str): ID for the entity
                    - etag (str): HTTP 1.1 Entity tag for the access-control entry
                    - id (str): ID of the access-control entry
                    - kind (str): Always "storage#bucketAccessControl"
                    - projectTeam (Dict[str, str]): Project team associated with entity
                        - projectNumber (str): Project number
                        - team (str): Team name
                    - role (str): Access permission for the entity
                    - selfLink (str): Link to this access-control entry
                - defaultObjectAcl (List[Dict[str, Any]]): Default object ACL (omitted if projection="noAcl")
                    - bucket (str): Name of the bucket
                    - domain (str): Domain associated with the entity
                    - email (str): Email address associated with the entity
                    - entity (str): The entity holding the permission
                    - entityId (str): ID for the entity
                    - etag (str): HTTP 1.1 Entity tag for the access-control entry
                    - generation (str): Content generation of the object
                    - id (str): ID of the access-control entry
                    - kind (str): Always "storage#objectAccessControl"
                    - object (str): Name of the object
                    - projectTeam (Dict[str, str]): Project team associated with entity
                        - projectNumber (str): Project number
                        - team (str): Team name
                    - role (str): Access permission for the entity
                    - selfLink (str): Link to this access-control entry
                - billing (Dict[str, bool]): Billing configuration
                    - requesterPays (bool): Whether requester pays is enabled
                - cors (List[Dict[str, Any]]): CORS configuration rules
                    - maxAgeSeconds (int): Max age for preflight cache
                    - method (List[str]): HTTP methods allowed
                    - origin (List[str]): Origins allowed
                    - responseHeader (List[str]): Headers allowed in response
                - versioning (Dict[str, bool]): Versioning configuration
                    - enabled (bool): Whether versioning is enabled
                - lifecycle (Dict[str, List[Dict[str, Any]]]): Lifecycle configuration
                    - rule (List[Dict[str, Any]]): List of lifecycle rules
                        - action (Dict[str, str]): Action to take
                            - type (str): Action type (Delete, SetStorageClass, etc.)
                            - storageClass (str): Target storage class for SetStorageClass
                        - condition (Dict[str, Any]): Conditions for applying the rule
                            - age (int): Age of object in days
                            - createdBefore (str): Date in RFC 3339 format
                            - customTimeBefore (str): Date in RFC 3339 format
                            - daysSinceCustomTime (int): Days since custom time
                            - daysSinceNoncurrentTime (int): Days since noncurrent time
                            - isLive (bool): Whether object is live
                            - matchesPattern (str): Regular expression pattern
                            - matchesPrefix (List[str]): Object name prefixes
                            - matchesSuffix (List[str]): Object name suffixes
                            - matchesStorageClass (List[str]): Storage classes to match
                            - noncurrentTimeBefore (str): Date in RFC 3339 format
                            - numNewerVersions (int): Number of newer versions
                - customPlacementConfig (Dict[str, List[str]]): Custom dual region placement
                    - dataLocations (List[str]): List of regional locations
                - hierarchicalNamespace (Dict[str, bool]): Hierarchical namespace config
                    - enabled (bool): Whether hierarchical namespace is enabled
                - iamConfiguration (Dict[str, Any]): IAM configuration
                    - uniformBucketLevelAccess (Dict[str, Any]): Uniform bucket-level access config
                        - enabled (bool): Whether enabled
                        - lockedTime (str): When it was locked (RFC 3339 format)
                    - bucketPolicyOnly (Dict[str, Any]): Legacy bucket policy only config
                        - enabled (bool): Whether enabled
                        - lockedTime (str): When it was locked (RFC 3339 format)
                    - publicAccessPrevention (str): Public access prevention setting
                - ipFilter (Dict[str, Any]): IP filter configuration
                    - mode (str): Filter mode ("Enabled" or "Disabled")
                    - publicNetworkSource (Dict[str, List[str]]): Public network sources
                        - allowedIpCidrRanges (List[str]): List of allowed IP CIDR ranges
                    - vpcNetworkSources (List[Dict[str, Any]]): VPC network sources
                        - network (str): VPC network resource name
                        - allowedIpCidrRanges (List[str]): List of allowed IP CIDR ranges
                - autoclass (Dict[str, Any]): Autoclass configuration
                    - enabled (bool): Whether autoclass is enabled
                    - toggleTime (str): Time autoclass was toggled (RFC 3339 format)
                    - terminalStorageClass (str): Terminal storage class (NEARLINE or ARCHIVE)
                    - terminalStorageClassUpdateTime (str): Time terminal class was updated (RFC 3339)
                - website (Dict[str, str]): Website configuration
                    - mainPageSuffix (str): Main page suffix (e.g., "index.html")
                    - notFoundPage (str): 404 page (e.g., "404.html")
                - logging (Dict[str, str]): Access logging configuration
                    - logBucket (str): Destination bucket for logs
                    - logObjectPrefix (str): Prefix for log objects
                - retentionPolicy (Dict[str, Any]): Retention policy
                    - effectiveTime (str): When policy became effective (RFC 3339 format)
                    - isLocked (bool): Whether policy is locked
                    - retentionPeriod (str): Retention period in seconds
                - objectRetention (Dict[str, str]): Object retention configuration
                    - mode (str): Object retention mode
                - softDeletePolicy (Dict[str, str]): Soft delete policy
                    - retentionDurationSeconds (str): Retention duration in seconds
                    - effectiveTime (str): When policy became effective (RFC 3339 format)
                - encryption (Dict[str, str]): Encryption configuration
                    - defaultKmsKeyName (str): Default KMS key resource name
                - owner (Dict[str, str]): Bucket owner information
                    - entity (str): Owner entity
                    - entityId (str): Owner entity ID
                - labels (Dict[str, str]): User-defined labels as arbitrary key-value pairs where:
                    - Keys are user-defined strings (max 63 characters)
                    - Values are user-defined strings (max 63 characters)
                - defaultEventBasedHold (bool): Default event-based hold for new objects
                - rpo (str): Recovery Point Objective ("DEFAULT" or "ASYNC_TURBO")
                - locationType (str): Type of location (e.g., "region", "dual-region")
                - satisfiesPZS (bool): Whether bucket satisfies Zone Separation
                - satisfiesPZI (bool): Whether bucket satisfies Zone Isolation
                - enableObjectRetention (bool): Whether object retention is enabled

    Raises:
        TypeError: If any argument is of an incorrect type.
        ValueError: If 'projection' is not one of "full" or "noAcl", if 'predefinedAcl' is not a valid value,
                   if 'predefined_default_object_acl' is not a valid value, if bucket_request validation fails,
                   if bucket name is missing, or if bucket already exists.
    """
    # --- Input Type Validation ---
    if not isinstance(project, str):
        raise TypeError("Project must be a string")
    
    if project.strip() == "":
        raise ValueError("Argument 'project' cannot be empty.")
    
    if bucket_request is not None and not isinstance(bucket_request, dict):
        raise TypeError("Invalid bucket_request; must be a dictionary")

    if predefinedAcl is not None and not isinstance(predefinedAcl, str):
        raise TypeError("Argument 'predefinedAcl' must be a string or None.")
        
    if predefined_default_object_acl is not None and not isinstance(predefined_default_object_acl, str):
        raise TypeError("Argument 'predefined_default_object_acl' must be a string or None.")
        
    if not isinstance(projection, str):
        raise TypeError("Argument 'projection' must be a string.")
        
    if user_project is not None and not isinstance(user_project, str):
        raise TypeError("Argument 'user_project' must be a string or None.")
        
    if not isinstance(enableObjectRetention, bool):
        raise TypeError("Argument 'enableObjectRetention' must be a boolean.")

    # --- Value Validation ---
    # Validate projection
    if BucketProjection:
        valid_projections = [proj.value for proj in BucketProjection]
    else:
        valid_projections = ["full", "noAcl"]
        
    if projection not in valid_projections:
        raise ValueError(f"Invalid projection. Must be one of: {valid_projections}")

    # Validate predefinedAcl
    if predefinedAcl is not None:
        if PredefinedBucketAcl:
            valid_acls = [acl.value for acl in PredefinedBucketAcl]
        else:
            valid_acls = ["authenticatedRead", "private", "projectPrivate", "publicRead", "publicReadWrite"]
        
        if predefinedAcl not in valid_acls:
            raise ValueError(f"Invalid predefinedAcl. Must be one of: {valid_acls}")

    # Validate predefined_default_object_acl
    if predefined_default_object_acl is not None:
        if PredefinedDefaultObjectAcl:
            valid_default_acls = [acl.value for acl in PredefinedDefaultObjectAcl]
        else:
            valid_default_acls = ["authenticatedRead", "bucketOwnerFullControl", "bucketOwnerRead", 
                                 "private", "projectPrivate", "publicRead"]
        
        if predefined_default_object_acl not in valid_default_acls:
            raise ValueError(f"Invalid predefined_default_object_acl. Must be one of: {valid_default_acls}")

    # --- Bucket Request Processing ---
    # Provide default bucket_request if none provided (for backward compatibility)
    if bucket_request is None:
        bucket_name = f"bucket-{len(DB.get('buckets', {})) + 1}"
        bucket_request = {
            "name": bucket_name,
            "location": "US",
            "storageClass": "STANDARD"
        }

    try:
        # Validate the bucket request using Pydantic model
        if BucketRequest:
            validated_bucket = BucketRequest(**bucket_request)
            validated_data = validated_bucket.model_dump(exclude_none=True)
        else:
            # Fallback when models not available - basic validation
            validated_data = bucket_request.copy()
            
            # Basic validation for common fields when models not available
            if "storageClass" in validated_data:
                valid_storage_classes = ["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE", 
                                       "MULTI_REGIONAL", "REGIONAL", "DURABLE_REDUCED_AVAILABILITY"]
                if validated_data["storageClass"] not in valid_storage_classes:
                    raise ValueError(f"Invalid storageClass. Must be one of: {valid_storage_classes}")
                    
            if "rpo" in validated_data:
                valid_rpo_values = ["DEFAULT", "ASYNC_TURBO"]
                if validated_data["rpo"] not in valid_rpo_values:
                    raise ValueError(f"Invalid rpo. Must be one of: {valid_rpo_values}")
                    
            if "location" in validated_data and validated_data["location"] == "":
                raise ValueError("Location cannot be empty string")

        # Extract required fields
        bucket_name = validated_data.get("name")
        if not bucket_name:
            raise ValueError("Bucket name is required")

        # Check if bucket already exists
        if bucket_name in DB.get("buckets", {}):
            raise ValueError(f"Bucket {bucket_name} already exists")

        # Set defaults for required fields
        current_time = datetime.now().isoformat() + "Z"
        bucket_data = {
            "name": bucket_name,
            "project": project,
            "id": f"{project}/{bucket_name}",
            "metageneration": "1",
            "generation": "1",
            "kind": "storage#bucket",
            "timeCreated": current_time,
            "updated": current_time,
            "softDeleted": False,
            "objects": [],
            "enableObjectRetention": enableObjectRetention,
            "iamPolicy": {"bindings": []},
            "storageLayout": {},
            "storageClass": "STANDARD",  # Default storage class
            "location": "US",  # Default location
            "etag": f"etag-{bucket_name}-{current_time}",
            "selfLink": f"https://www.googleapis.com/storage/v1/b/{bucket_name}",
            "projectNumber": "123456789012"  # Standard 12-digit project number format
        }

        # Merge validated data with defaults (validated data takes precedence)
        for key, value in validated_data.items():
            if value is not None:  # Only update with non-None values
                bucket_data[key] = value

        # Apply predefined ACLs if specified, otherwise initialize as empty lists
        # ACL fields should always be present in the bucket data for proper projection behavior
        if predefinedAcl is not None:
            bucket_data["acl"] = predefinedAcl
        else:
            bucket_data["acl"] = []
            
        if predefined_default_object_acl is not None:
            bucket_data["defaultObjectAcl"] = predefined_default_object_acl
        else:
            bucket_data["defaultObjectAcl"] = []

        # Ensure critical fields are set correctly (these should not be overridden)
        bucket_data["project"] = project
        bucket_data["enableObjectRetention"] = enableObjectRetention
        bucket_data["kind"] = "storage#bucket"  # Always ensure this is correct

        # Initialize DB if needed
        if "buckets" not in DB:
            DB["buckets"] = {}
            
        # Store the bucket
        DB["buckets"][bucket_name] = bucket_data

        # Apply projection for response
        if projection == "noAcl":
            response_data = {k: v for k, v in bucket_data.items() 
                            if k not in ["acl", "defaultObjectAcl"]}
        else:
            response_data = bucket_data.copy()

        return {"bucket": response_data}

    except ValidationError as e:
        error_details = []
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            error_details.append(f"{field}: {error['msg']}")
        raise ValueError(f"Validation error: {'; '.join(error_details)}")
    except Exception as e:
        if isinstance(e, (ValueError, TypeError)):
            raise
        raise ValueError(f"Validation error: {str(e)}")

@tool_spec(
    spec={
        'name': 'list_buckets',
        'description': 'Retrieve buckets within a project with optional filtering and pagination.',
        'parameters': {
            'type': 'object',
            'properties': {
                'project': {
                    'type': 'string',
                    'description': 'Identifier of the owning project. Cannot be empty.'
                },
                'max_results': {
                    'type': 'integer',
                    'description': 'Maximum number of buckets to return. Must be a positive integer. Defaults to 1000.'
                },
                'page_token': {
                    'type': 'string',
                    'description': 'String token representing the starting offset of the next page. If None or invalid, the listing starts at the first record.'
                },
                'prefix': {
                    'type': 'string',
                    'description': 'If provided, only buckets whose names start with this prefix are returned.'
                },
                'soft_deleted': {
                    'type': 'boolean',
                    'description': 'When True, only buckets whose softDeleted flag is True are returned. When False, soft-deleted buckets are excluded.'
                },
                'projection': {
                    'type': 'string',
                    'description': 'Amount of metadata to include for each bucket. Allowed values: "full" or "noAcl". Default is "noAcl".'
                },
                'user_project': {
                    'type': 'string',
                    'description': 'Billing project identifier for Requester Pays buckets.'
                }
            },
            'required': [
                'project'
            ]
        }
    }
)
def list(
    project: str,
    max_results: int = 1000,
    page_token: Optional[str] = None,
    prefix: Optional[str] = None,
    soft_deleted: bool = False,
    projection: str = "noAcl",
    user_project: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve buckets within a project with optional filtering and pagination.

    Args:
        project (str): Identifier of the owning project. Cannot be empty.
        max_results (int): Maximum number of buckets to return. Must be a positive integer. Defaults to 1000.
        page_token (Optional[str]): String token representing the starting offset of the next page. If None or invalid, the listing starts at the first record.
        prefix (Optional[str]): If provided, only buckets whose names start with this prefix are returned.
        soft_deleted (bool): When True, only buckets whose softDeleted flag is True are returned. When False, soft-deleted buckets are excluded.
        projection (str): Amount of metadata to include for each bucket. Allowed values: "full" or "noAcl". Default is "noAcl".
        user_project (Optional[str]): Billing project identifier for Requester Pays buckets.

    Returns:
        Dict[str, Any]: Dictionary with the following keys:
            - items (List[Dict[str, Any]]): List of bucket resources that match the query. Each bucket dictionary contains:
                - acl (List[BucketAccessControl])
                - billing (Dict[str, bool]):
                    - requesterPays (bool)
                - cors (List[Dict[str, Any]]):
                    - maxAgeSeconds (int)
                    - method (List[str])
                    - origin (List[str])
                    - responseHeader (List[str])
                - customPlacementConfig (Dict[str, List[str]]):
                    - dataLocations (List[str])
                - defaultEventBasedHold (bool)
                - defaultObjectAcl (List[ObjectAccessControl])
                - encryption (Dict[str, str]):
                    - defaultKmsKeyName (str)
                - etag (str)
                - hierarchicalNamespace (Dict[str, bool]):
                    - enabled (bool)
                - iamConfiguration (Dict[str, Any]):
                    - bucketPolicyOnly (Dict[str, Any]):
                        - enabled (bool)
                        - lockedTime (str)
                    - uniformBucketLevelAccess (Dict[str, Any]):
                        - enabled (bool)
                        - lockedTime (str)
                    - publicAccessPrevention (str)
                - id (str)
                - ipFilter (Dict[str, Any]):
                    - mode (str)
                    - publicNetworkSource (Dict[str, List[str]]):
                        - allowedIpCidrRanges (List[str])
                    - vpcNetworkSources (List[Dict[str, Any]]):
                        - network (str)
                        - allowedIpCidrRanges (List[str])
                - kind (str)
                - labels (Dict[str, str])
                - lifecycle (Dict[str, List[Dict[str, Any]]]):
                    - rule:
                        - action (Dict[str, str]):
                            - type (str)
                            - storageClass (str)
                        - condition (Dict[str, Any]):
                            - age (int)
                            - createdBefore (str)
                            - customTimeBefore (str)
                            - daysSinceCustomTime (int)
                            - daysSinceNoncurrentTime (int)
                            - isLive (bool)
                            - matchesPattern (str)
                            - matchesPrefix (List[str])
                            - matchesSuffix (List[str])
                            - matchesStorageClass (List[str])
                            - noncurrentTimeBefore (str)
                            - numNewerVersions (int)
                - autoclass (Dict[str, Any]):
                    - enabled (bool)
                    - toggleTime (str)
                    - terminalStorageClass (str)
                    - terminalStorageClassUpdateTime (str)
                - location (str)
                - locationType (str)
                - logging (Dict[str, str]):
                    - logBucket (str)
                    - logObjectPrefix (str)
                - generation (str)
                - metageneration (str)
                - name (str)
                - owner (Dict[str, str]):
                    - entity (str)
                    - entityId (str)
                - projectNumber (str)
                - retentionPolicy (Dict[str, Any]):
                    - effectiveTime (str)
                    - isLocked (bool)
                    - retentionPeriod (str)
                - objectRetention (Dict[str, str]):
                    - mode (str)
                - rpo (str)
                - selfLink (str)
                - softDeletePolicy (Dict[str, str]):
                    - retentionDurationSeconds (str)
                    - effectiveTime (str)
                - storageClass (str)
                - timeCreated (str)
                - updated (str)
                - softDeleteTime (str)
                - hardDeleteTime (str)
                - versioning (Dict[str, bool]):
                    - enabled (bool)
                - website (Dict[str, str]):
                    - mainPageSuffix (str)
                    - notFoundPage (str)
                - satisfiesPZS (bool)
                - satisfiesPZI (bool)
            - nextPageToken (str): Present only when additional pages of results exist.

    Raises:
        TypeError: If any argument is of an unexpected type.
        ValueError: If project is empty or max_results is not positive.
        InvalidProjectionValueError: If projection is not one of the allowed values.
    """

    # ----------------------------- Validation ----------------------------- #
    if not isinstance(project, str):
        raise TypeError("Argument 'project' must be a string.")
    if project.strip() == "":
        raise ValueError("Argument 'project' cannot be empty or whitespace only.")

    if not isinstance(max_results, int):
        raise TypeError("Argument 'max_results' must be an integer.")
    if max_results <= 0:
        raise ValueError("Argument 'max_results' must be greater than zero.")

    if page_token is not None and not isinstance(page_token, str):
        raise TypeError("Argument 'page_token' must be a string or None.")

    if prefix is not None and not isinstance(prefix, str):
        raise TypeError("Argument 'prefix' must be a string or None.")

    if not isinstance(soft_deleted, bool):
        raise TypeError("Argument 'soft_deleted' must be a boolean.")

    if not isinstance(projection, str):
        raise TypeError("Argument 'projection' must be a string.")
    if projection not in ("full", "noAcl"):
        raise InvalidProjectionValueError(
            f"Invalid value for 'projection': '{projection}'. Must be 'full' or 'noAcl'."
        )

    if user_project is not None and not isinstance(user_project, str):
        raise TypeError("Argument 'user_project' must be a string or None.")

    # Convert page_token to starting offset; fallback to 0 on errors
    try:
        offset = int(page_token) if page_token is not None else 0
        if offset < 0:
            offset = 0
    except (ValueError, TypeError):
        offset = 0

    # --------------------------- Filtering Logic -------------------------- #
    filtered: List[Dict[str, Any]] = []

    for bucket_name, bucket_data in DB.get("buckets", {}).items():
        if bucket_data.get("project") != project:
            continue

        if prefix and not bucket_name.startswith(prefix):
            continue

        bucket_is_soft = bucket_data.get("softDeleted", False)
        if soft_deleted and not bucket_is_soft:
            continue
        if not soft_deleted and bucket_is_soft:
            continue

        if projection == "full":
            filtered.append(bucket_data)
        else:
            filtered.append(
                {k: v for k, v in bucket_data.items() if k not in ["acl", "defaultObjectAcl"]}
            )

    # Ensure deterministic order (by name) for pagination predictability
    filtered.sort(key=lambda b: b.get("name", ""))

    # ----------------------------- Pagination ----------------------------- #
    page_items = filtered[offset : offset + max_results]
    next_token: Optional[str]
    if offset + max_results < len(filtered):
        next_token = str(offset + max_results)
    else:
        next_token = None

    response: Dict[str, Any] = {"items": page_items}
    if next_token is not None:
        response["nextPageToken"] = next_token

    return response


@tool_spec(
    spec={
        'name': 'lock_bucket_retention_policy',
        'description': """ Locks retention policy on a bucket.
        
        This function permanently locks the retention policy on a Google Cloud Storage bucket,
        preventing any future changes to the retention period. Once locked, the retention policy
        cannot be unlocked or modified. The operation is conditional on the bucket's current
        metageneration matching the specified value for optimistic concurrency control. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'bucket': {
                    'type': 'string',
                    'description': """ Name of the bucket on which to lock the retention policy. Must be a valid,
                    non-empty bucket name that follows Google Cloud Storage naming conventions. """
                },
                'if_metageneration_match': {
                    'type': 'string',
                    'description': """ Locks only if the bucket's current metageneration matches
                    this value exactly. This ensures the bucket hasn't been modified since the client
                    last retrieved it. Must be a non-empty string representing a valid metageneration value. """
                },
                'user_project': {
                    'type': 'string',
                    'description': """ The project to be billed for this request. Required for
                    Requester Pays buckets. Must be a valid project identifier if specified. """
                }
            },
            'required': [
                'bucket',
                'if_metageneration_match'
            ]
        }
    }
)
def lockRetentionPolicy(
    bucket: str,
    if_metageneration_match: str,
    user_project: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Locks retention policy on a bucket.

    This function permanently locks the retention policy on a Google Cloud Storage bucket,
    preventing any future changes to the retention period. Once locked, the retention policy
    cannot be unlocked or modified. The operation is conditional on the bucket's current
    metageneration matching the specified value for optimistic concurrency control.

    Args:
        bucket (str): Name of the bucket on which to lock the retention policy. Must be a valid,
            non-empty bucket name that follows Google Cloud Storage naming conventions.
        if_metageneration_match (str): Locks only if the bucket's current metageneration matches
            this value exactly. This ensures the bucket hasn't been modified since the client
            last retrieved it. Must be a non-empty string representing a valid metageneration value.
        user_project (Optional[str]): The project to be billed for this request. Required for
            Requester Pays buckets. Must be a valid project identifier if specified.

    Returns:
        Dict[str, Any]: Dictionary containing the updated bucket resource with key:
            - bucket (Dict[str, Any]): The complete bucket resource with the locked retention policy.
              Contains all bucket metadata including:
                - acl (List[BucketAccessControl]): Access control list for the bucket.
                - billing (Dict[str, bool]): Billing configuration.
                    - requesterPays (bool): Whether requester pays for requests.
                - cors (List[Dict[str, Any]]): Cross-origin resource sharing configuration.
                    - maxAgeSeconds (int): Maximum age for preflight requests.
                    - method (List[str]): Allowed HTTP methods.
                    - origin (List[str]): Allowed origins.
                    - responseHeader (List[str]): Headers exposed to the client.
                - customPlacementConfig (Dict[str, List[str]]): Custom placement configuration.
                    - dataLocations (List[str]): Regional locations for data placement.
                - defaultEventBasedHold (bool): Default event-based hold setting.
                - defaultObjectAcl (List[ObjectAccessControl]): Default object access control list.
                - encryption (Dict[str, str]): Encryption configuration.
                    - defaultKmsKeyName (str): Default KMS key for encryption.
                - etag (str): HTTP ETag for the bucket resource.
                - hierarchicalNamespace (Dict[str, bool]): Hierarchical namespace configuration.
                    - enabled (bool): Whether hierarchical namespace is enabled.
                - iamConfiguration (Dict[str, Any]): IAM configuration.
                    - bucketPolicyOnly (Dict[str, Any]): Bucket policy only configuration.
                        - enabled (bool): Whether bucket policy only is enabled.
                        - lockedTime (str): Time when policy was locked.
                    - uniformBucketLevelAccess (Dict[str, Any]): Uniform bucket-level access.
                        - enabled (bool): Whether uniform access is enabled.
                        - lockedTime (str): Time when uniform access was locked.
                    - publicAccessPrevention (str): Public access prevention setting.
                - id (str): Unique identifier for the bucket.
                - ipFilter (Dict[str, Any]): IP filtering configuration.
                    - mode (str): IP filtering mode.
                    - publicNetworkSource (Dict[str, List[str]]): Public network source config.
                        - allowedIpCidrRanges (List[str]): Allowed IP CIDR ranges.
                    - vpcNetworkSources (List[Dict[str, Any]]): VPC network sources.
                        - network (str): VPC network name.
                        - allowedIpCidrRanges (List[str]): Allowed IP ranges for this VPC.
                - kind (str): Resource type, always "storage#bucket".
                - labels (Dict[str, str]): User-defined labels for the bucket.
                - lifecycle (Dict[str, List[Dict[str, Any]]]): Lifecycle management configuration.
                    - rule (List[Dict[str, Any]]): Lifecycle rules.
                        - action (Dict[str, str]): Action to take.
                            - type (str): Action type (e.g., "Delete", "SetStorageClass").
                            - storageClass (str): Target storage class for SetStorageClass.
                        - condition (Dict[str, Any]): Conditions for applying the rule.
                            - age (int): Age in days.
                            - createdBefore (str): Created before this date.
                            - customTimeBefore (str): Custom time before this date.
                            - daysSinceCustomTime (int): Days since custom time.
                            - daysSinceNoncurrentTime (int): Days since becoming noncurrent.
                            - isLive (bool): Whether object is live.
                            - matchesPattern (str): Pattern to match object names.
                            - matchesPrefix (List[str]): Prefixes to match.
                            - matchesSuffix (List[str]): Suffixes to match.
                            - matchesStorageClass (List[str]): Storage classes to match.
                            - noncurrentTimeBefore (str): Noncurrent time before this date.
                            - numNewerVersions (int): Number of newer versions.
                - autoclass (Dict[str, Any]): Autoclass configuration.
                    - enabled (bool): Whether autoclass is enabled.
                    - toggleTime (str): Time when autoclass was toggled.
                    - terminalStorageClass (str): Terminal storage class.
                    - terminalStorageClassUpdateTime (str): Last update time for terminal class.
                - location (str): Geographic location of the bucket.
                - locationType (str): Type of location (region, dual-region, multi-region).
                - logging (Dict[str, str]): Access logging configuration.
                    - logBucket (str): Destination bucket for access logs.
                    - logObjectPrefix (str): Prefix for log object names.
                - generation (str): Generation number of the bucket metadata.
                - metageneration (str): Metageneration number (incremented after update).
                - name (str): Name of the bucket.
                - owner (Dict[str, str]): Owner information.
                    - entity (str): Owner entity identifier.
                    - entityId (str): Owner entity ID.
                - projectNumber (str): Project number that owns the bucket.
                - retentionPolicy (Dict[str, Any]): Retention policy configuration.
                    - effectiveTime (str): Time when retention policy became effective.
                    - isLocked (bool): Whether retention policy is locked (will be True after this operation).
                    - retentionPeriod (str): Retention period in seconds.
                - objectRetention (Dict[str, str]): Object retention configuration.
                    - mode (str): Object retention mode.
                - rpo (str): Recovery point objective setting.
                - selfLink (str): URI of this bucket resource.
                - softDeletePolicy (Dict[str, str]): Soft delete policy configuration.
                    - retentionDurationSeconds (str): Retention duration for soft-deleted objects.
                    - effectiveTime (str): Time when soft delete policy became effective.
                - storageClass (str): Default storage class for objects in the bucket.
                - timeCreated (str): Time when the bucket was created.
                - updated (str): Time when the bucket was last updated.
                - softDeleteTime (str): Time when bucket was soft-deleted (if applicable).
                - hardDeleteTime (str): Time when bucket will be hard-deleted (if applicable).
                - versioning (Dict[str, bool]): Object versioning configuration.
                    - enabled (bool): Whether object versioning is enabled.
                - website (Dict[str, str]): Website configuration.
                    - mainPageSuffix (str): Main page suffix for website.
                    - notFoundPage (str): Not found page for website.
                - satisfiesPZS (bool): Whether bucket satisfies Physical Zone Separation.
                - satisfiesPZI (bool): Whether bucket satisfies Physical Zone Isolation.

    Raises:
        TypeError: If any argument is of an incorrect type.
        ValueError: If bucket name violates Google Cloud Storage naming conventions,
                   if metageneration format is invalid, or if user_project format is invalid.
        BucketNotFoundError: If the specified bucket does not exist.
        MetagenerationMismatchError: If the provided metageneration does not match
                                   the bucket's current metageneration.
    """
    # --- Input Validation ---
    
    # Validate bucket parameter
    if not isinstance(bucket, str):
        raise TypeError(f"Argument 'bucket' must be a string, got {type(bucket).__name__}.")
    
    if not bucket.strip():
        raise ValueError("Argument 'bucket' cannot be empty or contain only whitespace.")
    
    # Validate bucket name follows basic Google Cloud Storage naming conventions
    if len(bucket) < 3 or len(bucket) > 63:
        raise ValueError("Bucket name must be between 3 and 63 characters long.")
    
    if bucket.startswith('.') or bucket.endswith('.') or '..' in bucket:
        raise ValueError("Bucket name cannot start or end with dots, or contain consecutive dots.")
    
    # Validate if_metageneration_match parameter
    if not isinstance(if_metageneration_match, str):
        raise TypeError(f"Argument 'if_metageneration_match' must be a string, got {type(if_metageneration_match).__name__}.")
    
    if not if_metageneration_match.strip():
        raise ValueError("Argument 'if_metageneration_match' cannot be empty or contain only whitespace.")
    
    # Validate metageneration format (should be numeric string)
    if not if_metageneration_match.isdigit():
        raise ValueError("Argument 'if_metageneration_match' must be a numeric string representing a valid metageneration.")
    
    # Validate user_project parameter
    if user_project is not None:
        if not isinstance(user_project, str):
            raise TypeError(f"Argument 'user_project' must be a string or None, got {type(user_project).__name__}.")
        if not user_project.strip():
            raise ValueError("Argument 'user_project' cannot be empty or contain only whitespace if specified.")
    
    # --- Core Logic ---
    
    # Check if bucket exists
    if bucket not in DB["buckets"]:
        raise BucketNotFoundError(f"Bucket '{bucket}' not found.")
    
    bucket_data = DB["buckets"][bucket]
    
    # Check metageneration match for optimistic concurrency control
    current_metageneration = str(bucket_data.get("metageneration", "0"))
    if current_metageneration != if_metageneration_match:
        raise MetagenerationMismatchError(
            f"Metageneration mismatch for bucket '{bucket}': Required '{if_metageneration_match}', found '{current_metageneration}'."
        )
    
    # Lock the retention policy
    bucket_data["retentionPolicyLocked"] = True
    
    # Update metageneration to reflect the change
    bucket_data["metageneration"] = str(int(current_metageneration) + 1)
    
    # Return the complete bucket object as promised in docstring
    return {"bucket": bucket_data}


@tool_spec(
    spec={
        'name': 'patch_bucket_attributes',
        'description': """ Patches a bucket.
        
        Changes to the bucket are readable immediately after writing, but configuration changes
        may take time to propagate. This operation may be conditional on metageneration match.
        Only the fields specified in bucket_request are updated; other fields remain unchanged. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'bucket': {
                    'type': 'string',
                    'description': 'Name of the bucket to update.'
                },
                'if_metageneration_match': {
                    'type': 'string',
                    'description': """ Makes the patch conditional on whether the
                    bucket's current metageneration matches this value. Defaults to None. """
                },
                'if_metageneration_not_match': {
                    'type': 'string',
                    'description': """ Makes the patch conditional on whether the
                    bucket's current metageneration does not match this value. Defaults to None. """
                },
                'predefinedAcl': {
                    'type': 'string',
                    'description': """ Apply a predefined set of access controls to the bucket.
                    Valid values:
                    - "authenticatedRead": Project team owners get OWNER access, allAuthenticatedUsers get READER access
                    - "private": Project team owners get OWNER access
                    - "projectPrivate": Project team members get access according to their roles
                    - "publicRead": Project team owners get OWNER access, allUsers get READER access
                    - "publicReadWrite": Project team owners get OWNER access, allUsers get WRITER access
                    Defaults to None. """
                },
                'predefined_default_object_acl': {
                    'type': 'string',
                    'description': """ Apply a predefined set of default object
                    access controls to the bucket. Valid values:
                    - "authenticatedRead": Object owner gets OWNER access, allAuthenticatedUsers get READER access
                    - "bucketOwnerFullControl": Object owner gets OWNER access, project team owners get OWNER access
                    - "bucketOwnerRead": Object owner gets OWNER access, project team owners get READER access
                    - "private": Object owner gets OWNER access
                    - "projectPrivate": Object owner gets OWNER access, project team members get access according to roles
                    - "publicRead": Object owner gets OWNER access, allUsers get READER access
                    Defaults to None. """
                },
                'projection': {
                    'type': 'string',
                    'description': """ Set of properties to return in the response. Valid values:
                    - "full": Include all properties
                    - "noAcl": Omit owner, acl and defaultObjectAcl properties
                    Defaults to None (returns all properties). """
                },
                'user_project': {
                    'type': 'string',
                    'description': """ The project to be billed for this request. Required for
                    Requester Pays buckets. Defaults to None. """
                },
                'bucket_request': {
                    'type': 'object',
                    'description': """ A dictionary representing the bucket properties
                    to update. Will be validated against the BucketRequest model. Supported keys:
                    Defaults to None. """,
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'Bucket name'
                        },
                        'storageClass': {
                            'type': 'string',
                            'description': 'Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE, etc.)'
                        },
                        'location': {
                            'type': 'string',
                            'description': 'Bucket location'
                        },
                        'billing': {
                            'type': 'object',
                            'description': 'Billing configuration',
                            'properties': {
                                'requesterPays': {
                                    'type': 'boolean',
                                    'description': 'Whether requester pays is enabled'
                                }
                            },
                            'required': [
                                'requesterPays'
                            ]
                        },
                        'cors': {
                            'type': 'array',
                            'description': 'CORS configuration rules',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'maxAgeSeconds': {
                                        'type': 'integer',
                                        'description': 'Max age for preflight cache'
                                    },
                                    'method': {
                                        'type': 'array',
                                        'description': 'HTTP methods allowed',
                                        'items': {
                                            'type': 'string'
                                        }
                                    },
                                    'origin': {
                                        'type': 'array',
                                        'description': 'Origins allowed',
                                        'items': {
                                            'type': 'string'
                                        }
                                    },
                                    'responseHeader': {
                                        'type': 'array',
                                        'description': 'Headers allowed in response',
                                        'items': {
                                            'type': 'string'
                                        }
                                    }
                                },
                                'required': [
                                    'maxAgeSeconds',
                                    'method',
                                    'origin',
                                    'responseHeader'
                                ]
                            }
                        },
                        'customPlacementConfig': {
                            'type': 'object',
                            'description': 'Custom dual region placement',
                            'properties': {
                                'dataLocations': {
                                    'type': 'array',
                                    'description': 'List of regional locations',
                                    'items': {
                                        'type': 'string'
                                    }
                                }
                            },
                            'required': [
                                'dataLocations'
                            ]
                        },
                        'hierarchicalNamespace': {
                            'type': 'object',
                            'description': 'Hierarchical namespace config',
                            'properties': {
                                'enabled': {
                                    'type': 'boolean',
                                    'description': 'Whether hierarchical namespace is enabled'
                                }
                            },
                            'required': [
                                'enabled'
                            ]
                        },
                        'iamConfiguration': {
                            'type': 'object',
                            'description': 'IAM configuration',
                            'properties': {
                                'uniformBucketLevelAccess': {
                                    'type': 'object',
                                    'description': 'Uniform bucket-level access config',
                                    'properties': {
                                        'enabled': {
                                            'type': 'boolean',
                                            'description': 'Whether enabled'
                                        },
                                        'lockedTime': {
                                            'type': 'string',
                                            'description': 'When it was locked (RFC 3339 format)'
                                        }
                                    },
                                    'required': [
                                        'enabled',
                                        'lockedTime'
                                    ]
                                },
                                'bucketPolicyOnly': {
                                    'type': 'object',
                                    'description': 'Legacy bucket policy only config',
                                    'properties': {
                                        'enabled': {
                                            'type': 'boolean',
                                            'description': 'Whether enabled'
                                        },
                                        'lockedTime': {
                                            'type': 'string',
                                            'description': 'When it was locked (RFC 3339 format)'
                                        }
                                    },
                                    'required': [
                                        'enabled',
                                        'lockedTime'
                                    ]
                                },
                                'publicAccessPrevention': {
                                    'type': 'string',
                                    'description': 'Public access prevention ("inherited" or "enforced")'
                                }
                            },
                            'required': [
                                'uniformBucketLevelAccess',
                                'bucketPolicyOnly',
                                'publicAccessPrevention'
                            ]
                        },
                        'ipFilter': {
                            'type': 'object',
                            'description': 'IP filter configuration',
                            'properties': {
                                'mode': {
                                    'type': 'string',
                                    'description': 'Filter mode ("Enabled" or "Disabled")'
                                },
                                'publicNetworkSource': {
                                    'type': 'object',
                                    'description': 'Public network sources',
                                    'properties': {
                                        'allowedIpCidrRanges': {
                                            'type': 'array',
                                            'description': 'List of allowed IP CIDR ranges',
                                            'items': {
                                                'type': 'string'
                                            }
                                        }
                                    },
                                    'required': [
                                        'allowedIpCidrRanges'
                                    ]
                                },
                                'vpcNetworkSources': {
                                    'type': 'array',
                                    'description': 'VPC network sources',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'network': {
                                                'type': 'string',
                                                'description': 'VPC network resource name'
                                            },
                                            'allowedIpCidrRanges': {
                                                'type': 'array',
                                                'description': 'List of allowed IP CIDR ranges',
                                                'items': {
                                                    'type': 'string'
                                                }
                                            }
                                        },
                                        'required': [
                                            'network',
                                            'allowedIpCidrRanges'
                                        ]
                                    }
                                }
                            },
                            'required': [
                                'mode',
                                'publicNetworkSource',
                                'vpcNetworkSources'
                            ]
                        },
                        'lifecycle': {
                            'type': 'object',
                            'description': 'Lifecycle management rules',
                            'properties': {
                                'rule': {
                                    'type': 'array',
                                    'description': 'List of lifecycle rules',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'action': {
                                                'type': 'object',
                                                'description': 'Action to take',
                                                'properties': {
                                                    'type': {
                                                        'type': 'string',
                                                        'description': 'Action type (Delete, SetStorageClass, AbortIncompleteMultipartUpload)'
                                                    },
                                                    'storageClass': {
                                                        'type': 'string',
                                                        'description': 'Target storage class for SetStorageClass action'
                                                    }
                                                },
                                                'required': [
                                                    'type',
                                                    'storageClass'
                                                ]
                                            },
                                            'condition': {
                                                'type': 'object',
                                                'description': 'Conditions for applying the rule',
                                                'properties': {
                                                    'age': {
                                                        'type': 'integer',
                                                        'description': 'Age of object in days'
                                                    },
                                                    'createdBefore': {
                                                        'type': 'string',
                                                        'description': 'Date in RFC 3339 format'
                                                    },
                                                    'customTimeBefore': {
                                                        'type': 'string',
                                                        'description': 'Date in RFC 3339 format'
                                                    },
                                                    'daysSinceCustomTime': {
                                                        'type': 'integer',
                                                        'description': 'Days since custom time'
                                                    },
                                                    'daysSinceNoncurrentTime': {
                                                        'type': 'integer',
                                                        'description': 'Days since noncurrent time'
                                                    },
                                                    'isLive': {
                                                        'type': 'boolean',
                                                        'description': 'Whether object is live'
                                                    },
                                                    'matchesPattern': {
                                                        'type': 'string',
                                                        'description': 'Regular expression pattern'
                                                    },
                                                    'matchesPrefix': {
                                                        'type': 'array',
                                                        'description': 'Object name prefixes',
                                                        'items': {
                                                            'type': 'string'
                                                        }
                                                    },
                                                    'matchesSuffix': {
                                                        'type': 'array',
                                                        'description': 'Object name suffixes',
                                                        'items': {
                                                            'type': 'string'
                                                        }
                                                    },
                                                    'matchesStorageClass': {
                                                        'type': 'array',
                                                        'description': 'Storage classes to match',
                                                        'items': {
                                                            'type': 'string'
                                                        }
                                                    },
                                                    'noncurrentTimeBefore': {
                                                        'type': 'string',
                                                        'description': 'Date in RFC 3339 format'
                                                    },
                                                    'numNewerVersions': {
                                                        'type': 'integer',
                                                        'description': 'Number of newer versions'
                                                    }
                                                },
                                                'required': [
                                                    'age',
                                                    'createdBefore',
                                                    'customTimeBefore',
                                                    'daysSinceCustomTime',
                                                    'daysSinceNoncurrentTime',
                                                    'isLive',
                                                    'matchesPattern',
                                                    'matchesPrefix',
                                                    'matchesSuffix',
                                                    'matchesStorageClass',
                                                    'noncurrentTimeBefore',
                                                    'numNewerVersions'
                                                ]
                                            }
                                        },
                                        'required': [
                                            'action',
                                            'condition'
                                        ]
                                    }
                                }
                            },
                            'required': [
                                'rule'
                            ]
                        },
                        'autoclass': {
                            'type': 'object',
                            'description': 'Autoclass configuration',
                            'properties': {
                                'enabled': {
                                    'type': 'boolean',
                                    'description': 'Whether autoclass is enabled'
                                },
                                'toggleTime': {
                                    'type': 'string',
                                    'description': 'Time autoclass was toggled (RFC 3339 format)'
                                },
                                'terminalStorageClass': {
                                    'type': 'string',
                                    'description': 'Terminal storage class (NEARLINE or ARCHIVE)'
                                },
                                'terminalStorageClassUpdateTime': {
                                    'type': 'string',
                                    'description': 'Time terminal class was updated (RFC 3339)'
                                }
                            },
                            'required': [
                                'enabled',
                                'toggleTime',
                                'terminalStorageClass',
                                'terminalStorageClassUpdateTime'
                            ]
                        },
                        'versioning': {
                            'type': 'object',
                            'description': 'Versioning configuration',
                            'properties': {
                                'enabled': {
                                    'type': 'boolean',
                                    'description': 'Whether versioning is enabled'
                                }
                            },
                            'required': [
                                'enabled'
                            ]
                        },
                        'website': {
                            'type': 'object',
                            'description': 'Website configuration',
                            'properties': {
                                'mainPageSuffix': {
                                    'type': 'string',
                                    'description': 'Main page suffix (e.g., "index.html")'
                                },
                                'notFoundPage': {
                                    'type': 'string',
                                    'description': '404 page (e.g., "404.html")'
                                }
                            },
                            'required': [
                                'mainPageSuffix',
                                'notFoundPage'
                            ]
                        },
                        'logging': {
                            'type': 'object',
                            'description': 'Access logging configuration',
                            'properties': {
                                'logBucket': {
                                    'type': 'string',
                                    'description': 'Destination bucket for logs'
                                },
                                'logObjectPrefix': {
                                    'type': 'string',
                                    'description': 'Prefix for log objects'
                                }
                            },
                            'required': [
                                'logBucket',
                                'logObjectPrefix'
                            ]
                        },
                        'retentionPolicy': {
                            'type': 'object',
                            'description': 'Retention policy',
                            'properties': {
                                'effectiveTime': {
                                    'type': 'string',
                                    'description': 'When policy became effective (RFC 3339 format)'
                                },
                                'isLocked': {
                                    'type': 'boolean',
                                    'description': 'Whether policy is locked'
                                },
                                'retentionPeriod': {
                                    'type': 'string',
                                    'description': 'Retention period in seconds'
                                }
                            },
                            'required': [
                                'effectiveTime',
                                'isLocked',
                                'retentionPeriod'
                            ]
                        },
                        'objectRetention': {
                            'type': 'object',
                            'description': 'Object retention configuration',
                            'properties': {
                                'mode': {
                                    'type': 'string',
                                    'description': 'Object retention mode'
                                }
                            },
                            'required': [
                                'mode'
                            ]
                        },
                        'softDeletePolicy': {
                            'type': 'object',
                            'description': 'Soft delete policy',
                            'properties': {
                                'retentionDurationSeconds': {
                                    'type': 'string',
                                    'description': 'Retention duration in seconds'
                                },
                                'effectiveTime': {
                                    'type': 'string',
                                    'description': 'When policy became effective (RFC 3339 format)'
                                }
                            },
                            'required': [
                                'retentionDurationSeconds',
                                'effectiveTime'
                            ]
                        },
                        'encryption': {
                            'type': 'object',
                            'description': 'Encryption configuration',
                            'properties': {
                                'defaultKmsKeyName': {
                                    'type': 'string',
                                    'description': 'Default KMS key resource name'
                                }
                            },
                            'required': [
                                'defaultKmsKeyName'
                            ]
                        },
                        'owner': {
                            'type': 'object',
                            'description': 'Bucket owner information',
                            'properties': {
                                'entity': {
                                    'type': 'string',
                                    'description': 'Owner entity'
                                },
                                'entityId': {
                                    'type': 'string',
                                    'description': 'Owner entity ID'
                                }
                            },
                            'required': [
                                'entity',
                                'entityId'
                            ]
                        },
                        'labels': {
                            'type': 'object',
                            'description': """ User-defined labels as arbitrary key-value pairs where:
                                 - Keys are user-defined strings (max 63 characters)
                                - Values are user-defined strings (max 63 characters) """,
                            'properties': {},
                            'required': []
                        },
                        'defaultEventBasedHold': {
                            'type': 'boolean',
                            'description': 'Default event-based hold for new objects'
                        },
                        'rpo': {
                            'type': 'string',
                            'description': 'Recovery Point Objective ("DEFAULT" or "ASYNC_TURBO")'
                        },
                        'locationType': {
                            'type': 'string',
                            'description': 'Type of location (e.g., "region", "dual-region")'
                        },
                        'projectNumber': {
                            'type': 'string',
                            'description': 'Project number bucket belongs to'
                        },
                        'satisfiesPZS': {
                            'type': 'boolean',
                            'description': 'Whether bucket satisfies Zone Separation'
                        },
                        'satisfiesPZI': {
                            'type': 'boolean',
                            'description': 'Whether bucket satisfies Zone Isolation'
                        }
                    },
                    'required': [
                        'name',
                        'storageClass',
                        'location',
                        'billing',
                        'cors',
                        'customPlacementConfig',
                        'hierarchicalNamespace',
                        'iamConfiguration',
                        'ipFilter',
                        'lifecycle',
                        'autoclass',
                        'versioning',
                        'website',
                        'logging',
                        'retentionPolicy',
                        'objectRetention',
                        'softDeletePolicy',
                        'encryption',
                        'owner',
                        'labels',
                        'defaultEventBasedHold',
                        'rpo',
                        'locationType',
                        'projectNumber',
                        'satisfiesPZS',
                        'satisfiesPZI'
                    ]
                }
            },
            'required': [
                'bucket'
            ]
        }
    }
)
def patch(
    bucket: str,
    if_metageneration_match: Optional[str] = None,
    if_metageneration_not_match: Optional[str] = None,
    predefinedAcl: Optional[str] = None,
    predefined_default_object_acl: Optional[str] = None,
    projection: Optional[str] = None,
    user_project: Optional[str] = None,
    bucket_request: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], int]:
    """
    Patches a bucket.

    Changes to the bucket are readable immediately after writing, but configuration changes
    may take time to propagate. This operation may be conditional on metageneration match.
    Only the fields specified in bucket_request are updated; other fields remain unchanged.

    Args:
        bucket (str): Name of the bucket to update.
        if_metageneration_match (Optional[str]): Makes the patch conditional on whether the
            bucket's current metageneration matches this value. Defaults to None.
        if_metageneration_not_match (Optional[str]): Makes the patch conditional on whether the
            bucket's current metageneration does not match this value. Defaults to None.
        predefinedAcl (Optional[str]): Apply a predefined set of access controls to the bucket.
            Valid values:
            - "authenticatedRead": Project team owners get OWNER access, allAuthenticatedUsers get READER access
            - "private": Project team owners get OWNER access
            - "projectPrivate": Project team members get access according to their roles
            - "publicRead": Project team owners get OWNER access, allUsers get READER access
            - "publicReadWrite": Project team owners get OWNER access, allUsers get WRITER access
            Defaults to None.
        predefined_default_object_acl (Optional[str]): Apply a predefined set of default object
            access controls to the bucket. Valid values:
            - "authenticatedRead": Object owner gets OWNER access, allAuthenticatedUsers get READER access
            - "bucketOwnerFullControl": Object owner gets OWNER access, project team owners get OWNER access
            - "bucketOwnerRead": Object owner gets OWNER access, project team owners get READER access
            - "private": Object owner gets OWNER access
            - "projectPrivate": Object owner gets OWNER access, project team members get access according to roles
            - "publicRead": Object owner gets OWNER access, allUsers get READER access
            Defaults to None.
        projection (Optional[str]): Set of properties to return in the response. Valid values:
            - "full": Include all properties
            - "noAcl": Omit owner, acl and defaultObjectAcl properties
            Defaults to None (returns all properties).
        user_project (Optional[str]): The project to be billed for this request. Required for
            Requester Pays buckets. Defaults to None.
        bucket_request (Optional[Dict[str, Any]]): A dictionary representing the bucket properties
            to update. Will be validated against the BucketRequest model. Supported keys:
            - name (str): Bucket name
            - storageClass (str): Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE, etc.)
            - location (str): Bucket location
            - billing (Dict[str, bool]): Billing configuration
                - requesterPays (bool): Whether requester pays is enabled
            - cors (List[Dict[str, Any]]): CORS configuration rules
                - maxAgeSeconds (int): Max age for preflight cache
                - method (List[str]): HTTP methods allowed
                - origin (List[str]): Origins allowed
                - responseHeader (List[str]): Headers allowed in response
            - customPlacementConfig (Dict[str, List[str]]): Custom dual region placement
                - dataLocations (List[str]): List of regional locations
            - hierarchicalNamespace (Dict[str, bool]): Hierarchical namespace config
                - enabled (bool): Whether hierarchical namespace is enabled
            - iamConfiguration (Dict[str, Any]): IAM configuration
                - uniformBucketLevelAccess (Dict[str, Any]): Uniform bucket-level access config
                    - enabled (bool): Whether enabled
                    - lockedTime (str): When it was locked (RFC 3339 format)
                - bucketPolicyOnly (Dict[str, Any]): Legacy bucket policy only config
                    - enabled (bool): Whether enabled
                    - lockedTime (str): When it was locked (RFC 3339 format)
                - publicAccessPrevention (str): Public access prevention ("inherited" or "enforced")
            - ipFilter (Dict[str, Any]): IP filter configuration
                - mode (str): Filter mode ("Enabled" or "Disabled")
                - publicNetworkSource (Dict[str, List[str]]): Public network sources
                    - allowedIpCidrRanges (List[str]): List of allowed IP CIDR ranges
                - vpcNetworkSources (List[Dict[str, Any]]): VPC network sources
                    - network (str): VPC network resource name
                    - allowedIpCidrRanges (List[str]): List of allowed IP CIDR ranges
            - lifecycle (Dict[str, List[Dict[str, Any]]]): Lifecycle management rules
                - rule (List[Dict[str, Any]]): List of lifecycle rules
                    - action (Dict[str, str]): Action to take
                        - type (str): Action type (Delete, SetStorageClass, AbortIncompleteMultipartUpload)
                        - storageClass (str): Target storage class for SetStorageClass action
                    - condition (Dict[str, Any]): Conditions for applying the rule
                        - age (int): Age of object in days
                        - createdBefore (str): Date in RFC 3339 format
                        - customTimeBefore (str): Date in RFC 3339 format
                        - daysSinceCustomTime (int): Days since custom time
                        - daysSinceNoncurrentTime (int): Days since noncurrent time
                        - isLive (bool): Whether object is live
                        - matchesPattern (str): Regular expression pattern
                        - matchesPrefix (List[str]): Object name prefixes
                        - matchesSuffix (List[str]): Object name suffixes
                        - matchesStorageClass (List[str]): Storage classes to match
                        - noncurrentTimeBefore (str): Date in RFC 3339 format
                        - numNewerVersions (int): Number of newer versions
            - autoclass (Dict[str, Any]): Autoclass configuration
                - enabled (bool): Whether autoclass is enabled
                - toggleTime (str): Time autoclass was toggled (RFC 3339 format)
                - terminalStorageClass (str): Terminal storage class (NEARLINE or ARCHIVE)
                - terminalStorageClassUpdateTime (str): Time terminal class was updated (RFC 3339)
            - versioning (Dict[str, bool]): Versioning configuration
                - enabled (bool): Whether versioning is enabled
            - website (Dict[str, str]): Website configuration
                - mainPageSuffix (str): Main page suffix (e.g., "index.html")
                - notFoundPage (str): 404 page (e.g., "404.html")
            - logging (Dict[str, str]): Access logging configuration
                - logBucket (str): Destination bucket for logs
                - logObjectPrefix (str): Prefix for log objects
            - retentionPolicy (Dict[str, Any]): Retention policy
                - effectiveTime (str): When policy became effective (RFC 3339 format)
                - isLocked (bool): Whether policy is locked
                - retentionPeriod (str): Retention period in seconds
            - objectRetention (Dict[str, str]): Object retention configuration
                - mode (str): Object retention mode
            - softDeletePolicy (Dict[str, str]): Soft delete policy
                - retentionDurationSeconds (str): Retention duration in seconds
                - effectiveTime (str): When policy became effective (RFC 3339 format)
            - encryption (Dict[str, str]): Encryption configuration
                - defaultKmsKeyName (str): Default KMS key resource name
            - owner (Dict[str, str]): Bucket owner information
                - entity (str): Owner entity
                - entityId (str): Owner entity ID
            - labels (Dict[str, str]): User-defined labels as arbitrary key-value pairs where:
                - Keys are user-defined strings (max 63 characters)
                - Values are user-defined strings (max 63 characters)
            - defaultEventBasedHold (bool): Default event-based hold for new objects
            - rpo (str): Recovery Point Objective ("DEFAULT" or "ASYNC_TURBO")
            - locationType (str): Type of location (e.g., "region", "dual-region")
            - projectNumber (str): Project number bucket belongs to
            - satisfiesPZS (bool): Whether bucket satisfies Zone Separation
            - satisfiesPZI (bool): Whether bucket satisfies Zone Isolation
            Defaults to None.

    Returns:
        Tuple[Dict[str, Any], int]: A tuple containing:
            - Dictionary with bucket metadata (filtered by projection if specified):
                - name (str): Bucket name
                - id (str): Bucket ID
                - kind (str): Resource kind (always "storage#bucket")
                - storageClass (str): Current storage class
                - location (str): Bucket location
                - metageneration (str): Current metageneration (incremented after update)
                - generation (str): Bucket generation
                - timeCreated (str): Creation time (RFC 3339 format)
                - updated (str): Last update time (RFC 3339 format)
                - etag (str): Entity tag for the bucket
                - projectNumber (str): Project number
                - acl (List[Dict[str, Any]]): Access control list (omitted if projection="noAcl")
                    - bucket (str): Name of the bucket
                    - domain (str): Domain associated with the entity
                    - email (str): Email address associated with the entity
                    - entity (str): The entity holding the permission
                    - entityId (str): ID for the entity
                    - etag (str): HTTP 1.1 Entity tag for the access-control entry
                    - id (str): ID of the access-control entry
                    - kind (str): Always "storage#bucketAccessControl"
                    - projectTeam (Dict[str, str]): Project team associated with entity
                        - projectNumber (str): Project number
                        - team (str): Team name
                    - role (str): Access permission for the entity
                    - selfLink (str): Link to this access-control entry
                - defaultObjectAcl (List[Dict[str, Any]]): Default object ACL (omitted if projection="noAcl")
                    - bucket (str): Name of the bucket
                    - domain (str): Domain associated with the entity
                    - email (str): Email address associated with the entity
                    - entity (str): The entity holding the permission
                    - entityId (str): ID for the entity
                    - etag (str): HTTP 1.1 Entity tag for the access-control entry
                    - generation (str): Content generation of the object
                    - id (str): ID of the access-control entry
                    - kind (str): Always "storage#objectAccessControl"
                    - object (str): Name of the object
                    - projectTeam (Dict[str, str]): Project team associated with entity
                        - projectNumber (str): Project number
                        - team (str): Team name
                    - role (str): Access permission for the entity
                    - selfLink (str): Link to this access-control entry
                - billing (Dict[str, bool]): Billing configuration
                    - requesterPays (bool): Whether requester pays is enabled
                - cors (List[Dict[str, Any]]): CORS configuration rules
                    - maxAgeSeconds (int): Max age for preflight cache
                    - method (List[str]): HTTP methods allowed
                    - origin (List[str]): Origins allowed
                    - responseHeader (List[str]): Headers allowed in response
                - versioning (Dict[str, bool]): Versioning configuration
                    - enabled (bool): Whether versioning is enabled
                - lifecycle (Dict[str, List[Dict[str, Any]]]): Lifecycle configuration
                    - rule (List[Dict[str, Any]]): List of lifecycle rules
                        - action (Dict[str, str]): Action to take
                            - type (str): Action type (Delete, SetStorageClass, etc.)
                            - storageClass (str): Target storage class for SetStorageClass
                        - condition (Dict[str, Any]): Conditions for applying the rule
                            - age (int): Age of object in days
                            - createdBefore (str): Date in RFC 3339 format
                            - customTimeBefore (str): Date in RFC 3339 format
                            - daysSinceCustomTime (int): Days since custom time
                            - daysSinceNoncurrentTime (int): Days since noncurrent time
                            - isLive (bool): Whether object is live
                            - matchesPattern (str): Regular expression pattern
                            - matchesPrefix (List[str]): Object name prefixes
                            - matchesSuffix (List[str]): Object name suffixes
                            - matchesStorageClass (List[str]): Storage classes to match
                            - noncurrentTimeBefore (str): Date in RFC 3339 format
                            - numNewerVersions (int): Number of newer versions
                - customPlacementConfig (Dict[str, List[str]]): Custom dual region placement
                    - dataLocations (List[str]): List of regional locations
                - hierarchicalNamespace (Dict[str, bool]): Hierarchical namespace config
                    - enabled (bool): Whether hierarchical namespace is enabled
                - iamConfiguration (Dict[str, Any]): IAM configuration
                    - uniformBucketLevelAccess (Dict[str, Any]): Uniform bucket-level access config
                        - enabled (bool): Whether enabled
                        - lockedTime (str): When it was locked (RFC 3339 format)
                    - bucketPolicyOnly (Dict[str, Any]): Legacy bucket policy only config
                        - enabled (bool): Whether enabled
                        - lockedTime (str): When it was locked (RFC 3339 format)
                    - publicAccessPrevention (str): Public access prevention setting
                - autoclass (Dict[str, Any]): Autoclass configuration
                    - enabled (bool): Whether autoclass is enabled
                    - toggleTime (str): Time autoclass was toggled (RFC 3339 format)
                    - terminalStorageClass (str): Terminal storage class
                    - terminalStorageClassUpdateTime (str): Time terminal class was updated
                - website (Dict[str, str]): Website configuration
                    - mainPageSuffix (str): Main page suffix
                    - notFoundPage (str): 404 page
                - logging (Dict[str, str]): Access logging configuration
                    - logBucket (str): Destination bucket for logs
                    - logObjectPrefix (str): Prefix for log objects
                - retentionPolicy (Dict[str, Any]): Retention policy
                    - effectiveTime (str): When policy became effective (RFC 3339 format)
                    - isLocked (bool): Whether policy is locked
                    - retentionPeriod (str): Retention period in seconds
                - objectRetention (Dict[str, str]): Object retention configuration
                    - mode (str): Object retention mode
                - softDeletePolicy (Dict[str, str]): Soft delete policy
                    - retentionDurationSeconds (str): Retention duration in seconds
                    - effectiveTime (str): When policy became effective (RFC 3339 format)
                - encryption (Dict[str, str]): Encryption configuration
                    - defaultKmsKeyName (str): Default KMS key resource name
                - owner (Dict[str, str]): Bucket owner information
                    - entity (str): Owner entity
                    - entityId (str): Owner entity ID
                - labels (Dict[str, str]): User-defined labels as arbitrary key-value pairs where:
                    - Keys are user-defined strings (max 63 characters)
                    - Values are user-defined strings (max 63 characters)
                - [Additional fields as specified in bucket_request]
            - HTTP status code (200 for success, 400/404/412 for errors)

    Raises:
        TypeError: If bucket is not a string, or if optional string parameters are not strings.
        ValueError: If predefinedAcl, predefined_default_object_acl, or projection have invalid values.
        ValidationError: If bucket_request contains invalid data according to BucketRequest model.
    """
    # Input validation
    if not isinstance(bucket, str):
        return {"error": "Bucket name must be a string"}, 400
    
    if if_metageneration_match is not None and not isinstance(if_metageneration_match, str):
        return {"error": "if_metageneration_match must be a string or None"}, 400
        
    if if_metageneration_not_match is not None and not isinstance(if_metageneration_not_match, str):
        return {"error": "if_metageneration_not_match must be a string or None"}, 400

    # Validate predefinedAcl using enum if available
    if predefinedAcl is not None:
        if PredefinedBucketAcl:
            valid_acls = [acl.value for acl in PredefinedBucketAcl]
        else:
            valid_acls = ["authenticatedRead", "private", "projectPrivate", "publicRead", "publicReadWrite"]
        
        if predefinedAcl not in valid_acls:
            return {"error": f"Invalid predefinedAcl. Must be one of: {valid_acls}"}, 400

    # Validate predefined_default_object_acl using enum if available  
    if predefined_default_object_acl is not None:
        if PredefinedDefaultObjectAcl:
            valid_default_acls = [acl.value for acl in PredefinedDefaultObjectAcl]
        else:
            valid_default_acls = ["authenticatedRead", "bucketOwnerFullControl", "bucketOwnerRead", 
                                 "private", "projectPrivate", "publicRead"]
        
        if predefined_default_object_acl not in valid_default_acls:
            return {"error": f"Invalid predefined_default_object_acl. Must be one of: {valid_default_acls}"}, 400

    # Validate projection using enum if available
    if projection is not None:
        if BucketProjection:
            valid_projections = [proj.value for proj in BucketProjection]
        else:
            valid_projections = ["full", "noAcl"]
            
        if projection not in valid_projections:
            return {"error": f"Invalid projection. Must be one of: {valid_projections}"}, 400

    # Check if bucket exists
    if bucket not in DB.get("buckets", {}):
        return {"error": f"Bucket {bucket} not found"}, 404

    bucket_data = DB["buckets"][bucket]

    # Check metageneration conditions
    current_metageneration = str(bucket_data.get("metageneration", 0))
    
    if (if_metageneration_match is not None and 
        current_metageneration != if_metageneration_match):
        return {"error": "Metageneration mismatch"}, 412

    if (if_metageneration_not_match is not None and 
        current_metageneration == if_metageneration_not_match):
        return {"error": "Metageneration mismatch"}, 412

    # Apply predefined ACLs
    if predefinedAcl:
        bucket_data["acl"] = predefinedAcl
    if predefined_default_object_acl:
        bucket_data["defaultObjectAcl"] = predefined_default_object_acl

    # Validate and merge bucket_request if provided
    if bucket_request is not None:
        if not isinstance(bucket_request, dict):
            return {"error": "Invalid bucket_request; must be a dictionary"}, 400
        
        try:
            # Remove protected fields first so Pydantic does not reject them.
            protected_fields = ['id', 'kind', 'timeCreated', 'generation']
            sanitized_request = {k: v for k, v in bucket_request.items() if k not in protected_fields}

            if BucketRequest:
                # Validate the sanitized bucket request using Pydantic model
                validated_bucket = BucketRequest(**sanitized_request)
                validated_data = validated_bucket.model_dump(exclude_unset=True, exclude_none=True)
            else:
                validated_data = sanitized_request.copy()

            # Basic manual validations when Pydantic model is unavailable
            if "storageClass" in validated_data:
                valid_storage_classes = [
                    "STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE",
                    "MULTI_REGIONAL", "REGIONAL", "DURABLE_REDUCED_AVAILABILITY",
                ]
                if validated_data["storageClass"] not in valid_storage_classes:
                    return {"error": f"Invalid storageClass. Must be one of: {valid_storage_classes}"}, 400

            if "rpo" in validated_data:
                valid_rpo_values = ["DEFAULT", "ASYNC_TURBO"]
                if validated_data["rpo"] not in valid_rpo_values:
                    return {"error": f"Invalid rpo. Must be one of: {valid_rpo_values}"}, 400

            if "location" in validated_data and validated_data["location"] == "":
                return {"error": "Location cannot be empty string"}, 400
            
            # Merge validated data into bucket_data (patch semantics)
            for key, value in validated_data.items():
                bucket_data[key] = value
                
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                field = ".".join(str(x) for x in error["loc"])
                error_details.append(f"{field}: {error['msg']}")
            return {"error": f"Validation error: {'; '.join(error_details)}"}, 400
        except Exception as e:
            return {"error": f"Validation error: {str(e)}"}, 400

    # Increment metageneration
    bucket_data["metageneration"] = str(int(bucket_data.get("metageneration", 0)) + 1)
    
    # Update the updated timestamp
    bucket_data["updated"] = datetime.now().isoformat() + "Z"

    # Store updated data
    DB["buckets"][bucket] = bucket_data

    # Apply projection for response
    if projection == "noAcl":
        response_data = {k: v for k, v in bucket_data.items() 
                        if k not in ["acl", "defaultObjectAcl"]}
    else:
        response_data = bucket_data.copy()

    return response_data, 200



@tool_spec(
    spec={
        'name': 'set_bucket_iam_policy',
        'description': """ Updates an IAM policy for the specified bucket.
        
        This function replaces the existing IAM policy for a bucket with the provided policy.
        The policy must contain valid role bindings with properly formatted members and roles. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'bucket': {
                    'type': 'string',
                    'description': """ Name of the bucket whose IAM policy is being updated. Must be a valid,
                    non-empty bucket name that follows Google Cloud Storage naming conventions. """
                },
                'policy': {
                    'type': 'object',
                    'description': 'The IAM policy to set on the bucket. Must contain:',
                    'properties': {
                        'bindings': {
                            'type': 'array',
                            'description': 'List of role-member associations. Each binding contains:',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'role': {
                                        'type': 'string',
                                        'description': """ IAM role string. Valid roles:
                                                 - "roles/storage.admin": Full control of Google Cloud Storage resources.
                                                - "roles/storage.objectViewer": Read-only access to objects.
                                                - "roles/storage.objectCreator": Access to create objects.
                                                - "roles/storage.objectAdmin": Full control of objects.
                                                - "roles/storage.legacyObjectReader": Read-only access to objects without listing.
                                                - "roles/storage.legacyObjectOwner": Read/write access to existing objects without listing.
                                                - "roles/storage.legacyBucketReader": Read access to buckets with object listing.
                                                - "roles/storage.legacyBucketWriter": Read access with object creation/deletion.
                                                - "roles/storage.legacyBucketOwner": Read and write access to buckets. """
                                    },
                                    'members': {
                                        'type': 'array',
                                        'description': """ List of member identifiers. Valid formats:
                                                 - "allUsers": Anyone on the internet.
                                                - "allAuthenticatedUsers": Anyone with a Google account.
                                                - "user:<email>": Specific user email (e.g., "user:alice@gmail.com").
                                                - "serviceAccount:<email>": Service account email.
                                                - "group:<email>": Google group email.
                                                - "domain:<domain>": Google Apps domain (e.g., "domain:example.com").
                                                - "projectOwner:<projectid>": Project owners.
                                                - "projectEditor:<projectid>": Project editors.
                                                - "projectViewer:<projectid>": Project viewers. """,
                                        'items': {
                                            'type': 'string'
                                        }
                                    },
                                    'condition': {
                                        'type': 'object',
                                        'description': 'Optional condition expression with:',
                                        'properties': {
                                            'title': {
                                                'type': 'string',
                                                'description': 'Short description of the condition.'
                                            },
                                            'description': {
                                                'type': 'string',
                                                'description': 'Detailed explanation.'
                                            },
                                            'expression': {
                                                'type': 'string',
                                                'description': 'Common Expression Language (CEL) syntax string.'
                                            },
                                            'location': {
                                                'type': 'string',
                                                'description': 'Optional location for debugging.'
                                            }
                                        },
                                        'required': [
                                            'title',
                                            'expression'
                                        ]
                                    }
                                },
                                'required': [
                                    'role',
                                    'members'
                                ]
                            }
                        },
                        'etag': {
                            'type': 'string',
                            'description': 'HTTP 1.1 entity tag for the policy. If provided, used for optimistic concurrency control.'
                        },
                        'kind': {
                            'type': 'string',
                            'description': 'Resource kind, should be "storage#policy" if provided.'
                        },
                        'resourceId': {
                            'type': 'string',
                            'description': 'Resource ID the policy applies to. Ignored on input.'
                        },
                        'version': {
                            'type': 'integer',
                            'description': 'IAM policy format version. Defaults to 1 if not specified.'
                        }
                    },
                    'required': [
                        'bindings'
                    ]
                },
                'user_project': {
                    'type': 'string',
                    'description': """ The project to be billed for this request. Required for
                    Requester Pays buckets. Defaults to None. """
                }
            },
            'required': [
                'bucket',
                'policy'
            ]
        }
    }
)
def setIamPolicy(
    bucket: str,
    policy: Dict[str, Any],
    user_project: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Updates an IAM policy for the specified bucket.

    This function replaces the existing IAM policy for a bucket with the provided policy.
    The policy must contain valid role bindings with properly formatted members and roles.

    Args:
        bucket (str): Name of the bucket whose IAM policy is being updated. Must be a valid,
            non-empty bucket name that follows Google Cloud Storage naming conventions.
        policy (Dict[str, Any]): The IAM policy to set on the bucket. Must contain:
            - bindings (List[Dict[str, Any]]): List of role-member associations. Each binding contains:
                - role (str): IAM role string. Valid roles:
                    - "roles/storage.admin": Full control of Google Cloud Storage resources.
                    - "roles/storage.objectViewer": Read-only access to objects.
                    - "roles/storage.objectCreator": Access to create objects.
                    - "roles/storage.objectAdmin": Full control of objects.
                    - "roles/storage.legacyObjectReader": Read-only access to objects without listing.
                    - "roles/storage.legacyObjectOwner": Read/write access to existing objects without listing.
                    - "roles/storage.legacyBucketReader": Read access to buckets with object listing.
                    - "roles/storage.legacyBucketWriter": Read access with object creation/deletion.
                    - "roles/storage.legacyBucketOwner": Read and write access to buckets.
                - members (List[str]): List of member identifiers. Valid formats:
                    - "allUsers": Anyone on the internet.
                    - "allAuthenticatedUsers": Anyone with a Google account.
                    - "user:<email>": Specific user email (e.g., "user:alice@gmail.com").
                    - "serviceAccount:<email>": Service account email.
                    - "group:<email>": Google group email.
                    - "domain:<domain>": Google Apps domain (e.g., "domain:example.com").
                    - "projectOwner:<projectid>": Project owners.
                    - "projectEditor:<projectid>": Project editors.
                    - "projectViewer:<projectid>": Project viewers.
                - condition (Optional[Dict[str, Any]]): Optional condition expression with:
                    - title (str): Short description of the condition.
                    - description (Optional[str]): Detailed explanation.
                    - expression (str): Common Expression Language (CEL) syntax string.
                    - location (Optional[str]): Optional location for debugging.
            - etag (Optional[str]): HTTP 1.1 entity tag for the policy. If provided, used for optimistic concurrency control.
            - kind (Optional[str]): Resource kind, should be "storage#policy" if provided.
            - resourceId (Optional[str]): Resource ID the policy applies to. Ignored on input.
            - version (Optional[int]): IAM policy format version. Defaults to 1 if not specified.
        user_project (Optional[str]): The project to be billed for this request. Required for
            Requester Pays buckets. Defaults to None.

    Returns:
        Dict[str, Any]: The updated IAM policy object containing:
            - bindings (List[Dict[str, Any]]): List of role-member associations that were set. Each binding contains:
                - role (str): IAM role string assigned to members. One of:
                    - "roles/storage.admin": Full control of Google Cloud Storage resources.
                    - "roles/storage.objectViewer": Read-only access to objects.
                    - "roles/storage.objectCreator": Access to create objects.
                    - "roles/storage.objectAdmin": Full control of objects.
                    - "roles/storage.legacyObjectReader": Read-only access to objects without listing.
                    - "roles/storage.legacyObjectOwner": Read/write access to existing objects without listing.
                    - "roles/storage.legacyBucketReader": Read access to buckets with object listing.
                    - "roles/storage.legacyBucketWriter": Read access with object creation/deletion.
                    - "roles/storage.legacyBucketOwner": Read and write access to buckets.
                - members (List[str]): List of member identifiers granted the role. Each member can be:
                    - "allUsers": Anyone on the internet.
                    - "allAuthenticatedUsers": Anyone with a Google account.
                    - "user:<email>": Specific user email (e.g., "user:alice@gmail.com").
                    - "serviceAccount:<email>": Service account email.
                    - "group:<email>": Google group email.
                    - "domain:<domain>": Google Apps domain (e.g., "domain:example.com").
                    - "projectOwner:<projectid>": Project owners.
                    - "projectEditor:<projectid>": Project editors.
                    - "projectViewer:<projectid>": Project viewers.
                - condition (Optional[Dict[str, Any]]): Optional condition expression that restricts when the binding is applied. Contains:
                        - title (str): Short description of the condition.
                    - description (Optional[str]): Detailed explanation of the expression's intent.
                    - expression (str): Common Expression Language (CEL) syntax string that defines the condition.
                    - location (Optional[str]): Optional location string for debugging (e.g., file or position).
            - etag (str): HTTP 1.1 entity tag for the policy. Used for optimistic concurrency control.
            - kind (str): Resource kind, always "storage#policy".
            - resourceId (str): The resource ID the policy applies to (format: "projects/_/buckets/{bucket}").
            - version (int): IAM policy format version. Determines which features are available:
                - Version 1: Basic role bindings.
                - Version 3: Role bindings with conditions (conditional IAM).

    Raises:
        TypeError: If any argument is of an incorrect type.
        ValueError: If bucket name violates Google Cloud Storage naming conventions,
                   if policy structure is invalid, if roles are invalid, if member formats are invalid,
                   or if user_project format is invalid.
        BucketNotFoundError: If the specified bucket does not exist.
    """
    from google_cloud_storage.SimulationEngine.models import IamPolicyModel
    from pydantic import ValidationError
    
    # --- Input Validation ---
    
    # Validate bucket parameter
    if not isinstance(bucket, builtins.str):
        raise TypeError(f"Argument 'bucket' must be a string, got {type(bucket).__name__}.")
    
    if not bucket.strip():
        raise ValueError("Argument 'bucket' cannot be empty or contain only whitespace.")
    
    # Validate bucket name follows basic Google Cloud Storage naming conventions
    if len(bucket) < 3 or len(bucket) > 63:
        raise ValueError("Bucket name must be between 3 and 63 characters long.")
    
    if bucket.startswith('.') or bucket.endswith('.') or '..' in bucket:
        raise ValueError("Bucket name cannot start or end with dots, or contain consecutive dots.")
    
    # Validate policy parameter type
    if not isinstance(policy, builtins.dict):
        raise TypeError(f"Argument 'policy' must be a dictionary, got {type(policy).__name__}.")
    
    if not policy:
        raise ValueError("Argument 'policy' cannot be empty.")
    
    # Validate user_project parameter
    if user_project is not None:
        if not isinstance(user_project, builtins.str):
            raise TypeError(f"Argument 'user_project' must be a string or None, got {type(user_project).__name__}.")
        if not user_project.strip():
            raise ValueError("Argument 'user_project' cannot be empty or contain only whitespace if specified.")
    
    # Check if bucket exists
    if bucket not in DB["buckets"]:
        raise BucketNotFoundError(f"Bucket '{bucket}' not found.")
    
    # Use Pydantic validation for policy structure
    try:
        validated_policy = IamPolicyModel(**policy)
    except ValidationError as e:
        # Convert Pydantic validation errors to ValueError with descriptive messages
        for error in e.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            error_msg = error["msg"]
            raise ValueError(f"Policy validation error in '{field_path}': {error_msg}")
    
    # --- Core Logic ---
    
    # Generate etag for the policy
    policy_content = json.dumps({"bindings": [binding.model_dump() for binding in validated_policy.bindings]}, sort_keys=True)
    etag = hashlib.md5(f"{policy_content}_{time.time()}".encode()).hexdigest()
    
    # Build the complete policy structure
    complete_policy = {
        "bindings": [binding.model_dump() for binding in validated_policy.bindings],
        "etag": etag,
        "kind": "storage#policy",
        "resourceId": f"projects/_/buckets/{bucket}",
        "version": validated_policy.version
    }
    
    # Store the policy in the database
    DB["buckets"][bucket]["iamPolicy"] = complete_policy
    
    return complete_policy


@tool_spec(
    spec={
        'name': 'test_bucket_permissions',
        'description': 'Tests a set of permissions on the given bucket to see which, if any, are held by the caller.',
        'parameters': {
            'type': 'object',
            'properties': {
                'bucket': {
                    'type': 'string',
                    'description': 'Name of the bucket on which permissions are being tested.'
                },
                'permissions': {
                    'type': 'string',
                    'description': """ The list of permissions to test.
                    One of:
                    - storage.buckets.delete
                    - storage.buckets.get
                    - storage.buckets.getIamPolicy
                    - storage.buckets.create
                    - storage.buckets.list
                    - storage.buckets.setIamPolicy
                    - storage.buckets.update
                    - storage.objects.delete
                    - storage.objects.get
                    - storage.objects.getIamPolicy
                    - storage.objects.create
                    - storage.objects.list
                    - storage.objects.setIamPolicy
                    - storage.objects.update
                    - storage.managedFolders.delete
                    - storage.managedFolders.get
                    - storage.managedFolders.getIamPolicy
                    - storage.managedFolders.create
                    - storage.managedFolders.list
                    - storage.managedFolders.setIamPolicy """
                },
                'user_project': {
                    'type': 'string',
                    'description': """ The project to be billed for this request. Required for
                    Requester Pays buckets. """
                }
            },
            'required': [
                'bucket',
                'permissions'
            ]
        }
    }
)
def testIamPermissions(
    bucket: str,
    permissions: str,
    user_project: Optional[str] = None,
) -> Tuple[Dict[str, Any], int]:
    """
    Tests a set of permissions on the given bucket to see which, if any, are held by the caller.

    Args:
        bucket (str): Name of the bucket on which permissions are being tested.
        permissions (str): The list of permissions to test.
            One of:
            - storage.buckets.delete
            - storage.buckets.get
            - storage.buckets.getIamPolicy
            - storage.buckets.create
            - storage.buckets.list
            - storage.buckets.setIamPolicy
            - storage.buckets.update
            - storage.objects.delete
            - storage.objects.get
            - storage.objects.getIamPolicy
            - storage.objects.create
            - storage.objects.list
            - storage.objects.setIamPolicy
            - storage.objects.update
            - storage.managedFolders.delete
            - storage.managedFolders.get
            - storage.managedFolders.getIamPolicy
            - storage.managedFolders.create
            - storage.managedFolders.list
            - storage.managedFolders.setIamPolicy
        user_project (Optional[str]): The project to be billed for this request. Required for
            Requester Pays buckets.

    Returns:
        Tuple[Dict[str, Any], int]:
        - On error:
            - {"error": "Bucket <name> not found"}, 404
        - On success:
            - TestIamPermissionsResponse (Dict[str, Any]):
                - kind (str): Always "storage#testIamPermissionsResponse".
                - permissions (List[str]): A subset of the requested permissions that the caller has.

        Supported Permissions:
            - storage.buckets.delete
            - storage.buckets.get
            - storage.buckets.getIamPolicy
            - storage.buckets.create
            - storage.buckets.list
            - storage.buckets.setIamPolicy
            - storage.buckets.update
            - storage.objects.delete
            - storage.objects.get
            - storage.objects.getIamPolicy
            - storage.objects.create
            - storage.objects.list
            - storage.objects.setIamPolicy
            - storage.objects.update
            - storage.managedFolders.delete
            - storage.managedFolders.get
            - storage.managedFolders.getIamPolicy
            - storage.managedFolders.create
            - storage.managedFolders.list
            - storage.managedFolders.setIamPolicy
    """
    if bucket not in DB.get("buckets", {}):
        return {"error": f"Bucket {bucket} not found"}, 404

    # Testing permissions
    return {"permissions": [permissions]}, 200


@tool_spec(
    spec={
        'name': 'update_bucket_attributes',
        'description': """ Updates a bucket with complete replacement using PUT semantics.
        
        Changes to the bucket will be readable immediately after writing, but configuration changes
        may take time to propagate. Unlike patch(), this operation completely replaces the bucket
        configuration with the provided bucket_request data, requiring bucket_request to be provided. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'bucket': {
                    'type': 'string',
                    'description': 'Name of the bucket to update.'
                },
                'if_metageneration_match': {
                    'type': 'string',
                    'description': """ Makes the update conditional on whether the
                    bucket's current metageneration matches this value. Defaults to None. """
                },
                'if_metageneration_not_match': {
                    'type': 'string',
                    'description': """ Makes the update conditional on whether the
                    bucket's current metageneration does not match this value. Defaults to None. """
                },
                'predefinedAcl': {
                    'type': 'string',
                    'description': """ Apply a predefined set of access controls to the bucket.
                    Valid values:
                    - "authenticatedRead": Project team owners get OWNER access, allAuthenticatedUsers get READER access
                    - "private": Project team owners get OWNER access
                    - "projectPrivate": Project team members get access according to their roles
                    - "publicRead": Project team owners get OWNER access, allUsers get READER access
                    - "publicReadWrite": Project team owners get OWNER access, allUsers get WRITER access
                    Defaults to None. """
                },
                'predefined_default_object_acl': {
                    'type': 'string',
                    'description': """ Apply a predefined set of default object
                    access controls to the bucket. Valid values:
                    - "authenticatedRead": Object owner gets OWNER access, allAuthenticatedUsers get READER access
                    - "bucketOwnerFullControl": Object owner gets OWNER access, project team owners get OWNER access
                    - "bucketOwnerRead": Object owner gets OWNER access, project team owners get READER access
                    - "private": Object owner gets OWNER access
                    - "projectPrivate": Object owner gets OWNER access, project team members get access according to roles
                    - "publicRead": Object owner gets OWNER access, allUsers get READER access
                    Defaults to None. """
                },
                'projection': {
                    'type': 'string',
                    'description': """ Set of properties to return in the response. Valid values:
                    - "full": Include all properties
                    - "noAcl": Omit owner, acl and defaultObjectAcl properties
                    Defaults to None (returns all properties). """
                },
                'user_project': {
                    'type': 'string',
                    'description': """ The project to be billed for this request. Required for
                    Requester Pays buckets. Defaults to None. """
                },
                'bucket_request': {
                    'type': 'object',
                    'description': """ A dictionary representing the complete bucket
                    configuration to replace existing configuration. Will be validated against the BucketRequest model.
                    When provided, ALL of the following properties are REQUIRED:
                    Defaults to None. Note: While the parameter itself is optional, if provided, all nested properties are required. """,
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'Bucket name (will be preserved as original bucket name)'
                        },
                        'storageClass': {
                            'type': 'string',
                            'description': 'Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE, etc.)'
                        },
                        'location': {
                            'type': 'string',
                            'description': 'Bucket location'
                        },
                        'billing': {
                            'type': 'object',
                            'description': 'Billing configuration',
                            'properties': {
                                'requesterPays': {
                                    'type': 'boolean',
                                    'description': 'Whether requester pays is enabled (REQUIRED)'
                                }
                            },
                            'required': [
                                'requesterPays'
                            ]
                        },
                        'cors': {
                            'type': 'array',
                            'description': 'CORS configuration rules',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'maxAgeSeconds': {
                                        'type': 'integer',
                                        'description': 'Max age for preflight cache (REQUIRED)'
                                    },
                                    'method': {
                                        'type': 'array',
                                        'description': 'HTTP methods allowed (REQUIRED)',
                                        'items': {
                                            'type': 'string'
                                        }
                                    },
                                    'origin': {
                                        'type': 'array',
                                        'description': 'Origins allowed (REQUIRED)',
                                        'items': {
                                            'type': 'string'
                                        }
                                    },
                                    'responseHeader': {
                                        'type': 'array',
                                        'description': 'Headers allowed in response (REQUIRED)',
                                        'items': {
                                            'type': 'string'
                                        }
                                    }
                                },
                                'required': [
                                    'maxAgeSeconds',
                                    'method',
                                    'origin',
                                    'responseHeader'
                                ]
                            }
                        },
                        'customPlacementConfig': {
                            'type': 'object',
                            'description': 'Custom dual region placement',
                            'properties': {
                                'dataLocations': {
                                    'type': 'array',
                                    'description': 'List of regional locations (REQUIRED)',
                                    'items': {
                                        'type': 'string'
                                    }
                                }
                            },
                            'required': [
                                'dataLocations'
                            ]
                        },
                        'hierarchicalNamespace': {
                            'type': 'object',
                            'description': 'Hierarchical namespace config',
                            'properties': {
                                'enabled': {
                                    'type': 'boolean',
                                    'description': 'Whether hierarchical namespace is enabled (REQUIRED)'
                                }
                            },
                            'required': [
                                'enabled'
                            ]
                        },
                        'iamConfiguration': {
                            'type': 'object',
                            'description': 'IAM configuration',
                            'properties': {
                                'uniformBucketLevelAccess': {
                                    'type': 'object',
                                    'description': 'Uniform bucket-level access config',
                                    'properties': {
                                        'enabled': {
                                            'type': 'boolean',
                                            'description': 'Whether enabled (REQUIRED)'
                                        },
                                        'lockedTime': {
                                            'type': 'string',
                                            'description': 'When it was locked (RFC 3339 format) (REQUIRED)'
                                        }
                                    },
                                    'required': [
                                        'enabled',
                                        'lockedTime'
                                    ]
                                },
                                'bucketPolicyOnly': {
                                    'type': 'object',
                                    'description': 'Legacy bucket policy only config',
                                    'properties': {
                                        'enabled': {
                                            'type': 'boolean',
                                            'description': 'Whether enabled (REQUIRED)'
                                        },
                                        'lockedTime': {
                                            'type': 'string',
                                            'description': 'When it was locked (RFC 3339 format) (REQUIRED)'
                                        }
                                    },
                                    'required': [
                                        'enabled',
                                        'lockedTime'
                                    ]
                                },
                                'publicAccessPrevention': {
                                    'type': 'string',
                                    'description': 'Public access prevention ("inherited" or "enforced") (REQUIRED)'
                                }
                            },
                            'required': [
                                'uniformBucketLevelAccess',
                                'bucketPolicyOnly',
                                'publicAccessPrevention'
                            ]
                        },
                        'ipFilter': {
                            'type': 'object',
                            'description': 'IP filter configuration',
                            'properties': {
                                'mode': {
                                    'type': 'string',
                                    'description': 'Filter mode ("Enabled" or "Disabled") (REQUIRED)'
                                },
                                'publicNetworkSource': {
                                    'type': 'object',
                                    'description': 'Public network sources',
                                    'properties': {
                                        'allowedIpCidrRanges': {
                                            'type': 'array',
                                            'description': 'List of allowed IP CIDR ranges (REQUIRED)',
                                            'items': {
                                                'type': 'string'
                                            }
                                        }
                                    },
                                    'required': [
                                        'allowedIpCidrRanges'
                                    ]
                                },
                                'vpcNetworkSources': {
                                    'type': 'array',
                                    'description': 'VPC network sources',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'network': {
                                                'type': 'string',
                                                'description': 'VPC network resource name (REQUIRED)'
                                            },
                                            'allowedIpCidrRanges': {
                                                'type': 'array',
                                                'description': 'List of allowed IP CIDR ranges (REQUIRED)',
                                                'items': {
                                                    'type': 'string'
                                                }
                                            }
                                        },
                                        'required': [
                                            'network',
                                            'allowedIpCidrRanges'
                                        ]
                                    }
                                }
                            },
                            'required': [
                                'mode',
                                'publicNetworkSource',
                                'vpcNetworkSources'
                            ]
                        },
                        'lifecycle': {
                            'type': 'object',
                            'description': 'Lifecycle management rules',
                            'properties': {
                                'rule': {
                                    'type': 'array',
                                    'description': 'List of lifecycle rules (REQUIRED)',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'action': {
                                                'type': 'object',
                                                'description': 'Action to take (REQUIRED)',
                                                'properties': {
                                                    'type': {
                                                        'type': 'string',
                                                        'description': 'Action type (Delete, SetStorageClass, AbortIncompleteMultipartUpload) (REQUIRED)'
                                                    },
                                                    'storageClass': {
                                                        'type': 'string',
                                                        'description': 'Target storage class for SetStorageClass action (REQUIRED)'
                                                    }
                                                },
                                                'required': [
                                                    'type',
                                                    'storageClass'
                                                ]
                                            },
                                            'condition': {
                                                'type': 'object',
                                                'description': 'Conditions for applying the rule (REQUIRED)',
                                                'properties': {
                                                    'age': {
                                                        'type': 'integer',
                                                        'description': 'Age of object in days (REQUIRED)'
                                                    },
                                                    'createdBefore': {
                                                        'type': 'string',
                                                        'description': 'Date in RFC 3339 format (REQUIRED)'
                                                    },
                                                    'customTimeBefore': {
                                                        'type': 'string',
                                                        'description': 'Date in RFC 3339 format (REQUIRED)'
                                                    },
                                                    'daysSinceCustomTime': {
                                                        'type': 'integer',
                                                        'description': 'Days since custom time (REQUIRED)'
                                                    },
                                                    'daysSinceNoncurrentTime': {
                                                        'type': 'integer',
                                                        'description': 'Days since noncurrent time (REQUIRED)'
                                                    },
                                                    'isLive': {
                                                        'type': 'boolean',
                                                        'description': 'Whether object is live (REQUIRED)'
                                                    },
                                                    'matchesPattern': {
                                                        'type': 'string',
                                                        'description': 'Regular expression pattern (REQUIRED)'
                                                    },
                                                    'matchesPrefix': {
                                                        'type': 'array',
                                                        'description': 'Object name prefixes (REQUIRED)',
                                                        'items': {
                                                            'type': 'string'
                                                        }
                                                    },
                                                    'matchesSuffix': {
                                                        'type': 'array',
                                                        'description': 'Object name suffixes (REQUIRED)',
                                                        'items': {
                                                            'type': 'string'
                                                        }
                                                    },
                                                    'matchesStorageClass': {
                                                        'type': 'array',
                                                        'description': 'Storage classes to match (REQUIRED)',
                                                        'items': {
                                                            'type': 'string'
                                                        }
                                                    },
                                                    'noncurrentTimeBefore': {
                                                        'type': 'string',
                                                        'description': 'Date in RFC 3339 format (REQUIRED)'
                                                    },
                                                    'numNewerVersions': {
                                                        'type': 'integer',
                                                        'description': 'Number of newer versions (REQUIRED)'
                                                    }
                                                },
                                                'required': [
                                                    'age',
                                                    'createdBefore',
                                                    'customTimeBefore',
                                                    'daysSinceCustomTime',
                                                    'daysSinceNoncurrentTime',
                                                    'isLive',
                                                    'matchesPattern',
                                                    'matchesPrefix',
                                                    'matchesSuffix',
                                                    'matchesStorageClass',
                                                    'noncurrentTimeBefore',
                                                    'numNewerVersions'
                                                ]
                                            }
                                        },
                                        'required': [
                                            'action',
                                            'condition'
                                        ]
                                    }
                                }
                            },
                            'required': [
                                'rule'
                            ]
                        },
                        'autoclass': {
                            'type': 'object',
                            'description': 'Autoclass configuration',
                            'properties': {
                                'enabled': {
                                    'type': 'boolean',
                                    'description': 'Whether autoclass is enabled (REQUIRED)'
                                },
                                'toggleTime': {
                                    'type': 'string',
                                    'description': 'Time autoclass was toggled (RFC 3339 format) (REQUIRED)'
                                },
                                'terminalStorageClass': {
                                    'type': 'string',
                                    'description': 'Terminal storage class (NEARLINE or ARCHIVE) (REQUIRED)'
                                },
                                'terminalStorageClassUpdateTime': {
                                    'type': 'string',
                                    'description': 'Time terminal class was updated (RFC 3339) (REQUIRED)'
                                }
                            },
                            'required': [
                                'enabled',
                                'toggleTime',
                                'terminalStorageClass',
                                'terminalStorageClassUpdateTime'
                            ]
                        },
                        'versioning': {
                            'type': 'object',
                            'description': 'Versioning configuration',
                            'properties': {
                                'enabled': {
                                    'type': 'boolean',
                                    'description': 'Whether versioning is enabled (REQUIRED)'
                                }
                            },
                            'required': [
                                'enabled'
                            ]
                        },
                        'website': {
                            'type': 'object',
                            'description': 'Website configuration',
                            'properties': {
                                'mainPageSuffix': {
                                    'type': 'string',
                                    'description': 'Main page suffix (e.g., "index.html") (REQUIRED)'
                                },
                                'notFoundPage': {
                                    'type': 'string',
                                    'description': '404 page (e.g., "404.html") (REQUIRED)'
                                }
                            },
                            'required': [
                                'mainPageSuffix',
                                'notFoundPage'
                            ]
                        },
                        'logging': {
                            'type': 'object',
                            'description': 'Access logging configuration',
                            'properties': {
                                'logBucket': {
                                    'type': 'string',
                                    'description': 'Destination bucket for logs (REQUIRED)'
                                },
                                'logObjectPrefix': {
                                    'type': 'string',
                                    'description': 'Prefix for log objects (REQUIRED)'
                                }
                            },
                            'required': [
                                'logBucket',
                                'logObjectPrefix'
                            ]
                        },
                        'retentionPolicy': {
                            'type': 'object',
                            'description': 'Retention policy',
                            'properties': {
                                'effectiveTime': {
                                    'type': 'string',
                                    'description': 'When policy became effective (RFC 3339 format) (REQUIRED)'
                                },
                                'isLocked': {
                                    'type': 'boolean',
                                    'description': 'Whether policy is locked (REQUIRED)'
                                },
                                'retentionPeriod': {
                                    'type': 'string',
                                    'description': 'Retention period in seconds (REQUIRED)'
                                }
                            },
                            'required': [
                                'effectiveTime',
                                'isLocked',
                                'retentionPeriod'
                            ]
                        },
                        'objectRetention': {
                            'type': 'object',
                            'description': 'Object retention configuration',
                            'properties': {
                                'mode': {
                                    'type': 'string',
                                    'description': 'Object retention mode (REQUIRED)'
                                }
                            },
                            'required': [
                                'mode'
                            ]
                        },
                        'softDeletePolicy': {
                            'type': 'object',
                            'description': 'Soft delete policy',
                            'properties': {
                                'retentionDurationSeconds': {
                                    'type': 'string',
                                    'description': 'Retention duration in seconds (REQUIRED)'
                                },
                                'effectiveTime': {
                                    'type': 'string',
                                    'description': 'When policy became effective (RFC 3339 format) (REQUIRED)'
                                }
                            },
                            'required': [
                                'retentionDurationSeconds',
                                'effectiveTime'
                            ]
                        },
                        'encryption': {
                            'type': 'object',
                            'description': 'Encryption configuration',
                            'properties': {
                                'defaultKmsKeyName': {
                                    'type': 'string',
                                    'description': 'Default KMS key resource name (REQUIRED)'
                                }
                            },
                            'required': [
                                'defaultKmsKeyName'
                            ]
                        },
                        'owner': {
                            'type': 'object',
                            'description': 'Bucket owner information',
                            'properties': {
                                'entity': {
                                    'type': 'string',
                                    'description': 'Owner entity (REQUIRED)'
                                },
                                'entityId': {
                                    'type': 'string',
                                    'description': 'Owner entity ID (REQUIRED)'
                                }
                            },
                            'required': [
                                'entity',
                                'entityId'
                            ]
                        },
                        'labels': {
                            'type': 'object',
                            'description': """ User-defined labels as arbitrary key-value pairs where:
                                 - Keys are user-defined strings (max 63 characters) (REQUIRED)
                                - Values are user-defined strings (max 63 characters) (REQUIRED) """,
                            'properties': {},
                            'required': []
                        },
                        'defaultEventBasedHold': {
                            'type': 'boolean',
                            'description': 'Default event-based hold for new objects (REQUIRED)'
                        },
                        'rpo': {
                            'type': 'string',
                            'description': 'Recovery Point Objective ("DEFAULT" or "ASYNC_TURBO") (REQUIRED)'
                        },
                        'locationType': {
                            'type': 'string',
                            'description': 'Type of location (e.g., "region", "dual-region") (REQUIRED)'
                        },
                        'projectNumber': {
                            'type': 'string',
                            'description': 'Project number bucket belongs to (REQUIRED)'
                        },
                        'satisfiesPZS': {
                            'type': 'boolean',
                            'description': 'Whether bucket satisfies Zone Separation (REQUIRED)'
                        },
                        'satisfiesPZI': {
                            'type': 'boolean',
                            'description': 'Whether bucket satisfies Zone Isolation (REQUIRED)'
                        }
                    },
                    'required': [
                        'name',
                        'storageClass',
                        'location',
                        'billing',
                        'cors',
                        'customPlacementConfig',
                        'hierarchicalNamespace',
                        'iamConfiguration',
                        'ipFilter',
                        'lifecycle',
                        'autoclass',
                        'versioning',
                        'website',
                        'logging',
                        'retentionPolicy',
                        'objectRetention',
                        'softDeletePolicy',
                        'encryption',
                        'owner',
                        'labels',
                        'defaultEventBasedHold',
                        'rpo',
                        'locationType',
                        'projectNumber',
                        'satisfiesPZS',
                        'satisfiesPZI'
                    ]
                }
            },
            'required': [
                'bucket'
            ]
        }
    }
)
def update(
    bucket: str,
    if_metageneration_match: Optional[str] = None,
    if_metageneration_not_match: Optional[str] = None,
    predefinedAcl: Optional[str] = None,
    predefined_default_object_acl: Optional[str] = None,
    projection: Optional[str] = None,
    user_project: Optional[str] = None,
    bucket_request: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], int]:
    """
    Updates a bucket with complete replacement using PUT semantics.

    Changes to the bucket will be readable immediately after writing, but configuration changes
    may take time to propagate. Unlike patch(), this operation completely replaces the bucket
    configuration with the provided bucket_request data, requiring bucket_request to be provided.

    Args:
        bucket (str): Name of the bucket to update.
        if_metageneration_match (Optional[str]): Makes the update conditional on whether the
            bucket's current metageneration matches this value. Defaults to None.
        if_metageneration_not_match (Optional[str]): Makes the update conditional on whether the
            bucket's current metageneration does not match this value. Defaults to None.
        predefinedAcl (Optional[str]): Apply a predefined set of access controls to the bucket.
            Valid values:
            - "authenticatedRead": Project team owners get OWNER access, allAuthenticatedUsers get READER access
            - "private": Project team owners get OWNER access
            - "projectPrivate": Project team members get access according to their roles
            - "publicRead": Project team owners get OWNER access, allUsers get READER access
            - "publicReadWrite": Project team owners get OWNER access, allUsers get WRITER access
            Defaults to None.
        predefined_default_object_acl (Optional[str]): Apply a predefined set of default object
            access controls to the bucket. Valid values:
            - "authenticatedRead": Object owner gets OWNER access, allAuthenticatedUsers get READER access
            - "bucketOwnerFullControl": Object owner gets OWNER access, project team owners get OWNER access
            - "bucketOwnerRead": Object owner gets OWNER access, project team owners get READER access
            - "private": Object owner gets OWNER access
            - "projectPrivate": Object owner gets OWNER access, project team members get access according to roles
            - "publicRead": Object owner gets OWNER access, allUsers get READER access
            Defaults to None.
        projection (Optional[str]): Set of properties to return in the response. Valid values:
            - "full": Include all properties
            - "noAcl": Omit owner, acl and defaultObjectAcl properties
            Defaults to None (returns all properties).
        user_project (Optional[str]): The project to be billed for this request. Required for
            Requester Pays buckets. Defaults to None.
        bucket_request (Optional[Dict[str, Any]]): A dictionary representing the complete bucket
            configuration to replace existing configuration. Will be validated against the BucketRequest model.
            When provided, ALL of the following properties are REQUIRED:
            - name (str): Bucket name (will be preserved as original bucket name)
            - storageClass (str): Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE, etc.)
            - location (str): Bucket location
            - billing (Dict[str, bool]): Billing configuration
                - requesterPays (bool): Whether requester pays is enabled (REQUIRED)
            - cors (List[Dict[str, Any]]): CORS configuration rules
                - maxAgeSeconds (int): Max age for preflight cache (REQUIRED)
                - method (List[str]): HTTP methods allowed (REQUIRED)
                - origin (List[str]): Origins allowed (REQUIRED)
                - responseHeader (List[str]): Headers allowed in response (REQUIRED)
            - customPlacementConfig (Dict[str, List[str]]): Custom dual region placement
                - dataLocations (List[str]): List of regional locations (REQUIRED)
            - hierarchicalNamespace (Dict[str, bool]): Hierarchical namespace config
                - enabled (bool): Whether hierarchical namespace is enabled (REQUIRED)
            - iamConfiguration (Dict[str, Any]): IAM configuration
                - uniformBucketLevelAccess (Dict[str, Any]): Uniform bucket-level access config
                    - enabled (bool): Whether enabled (REQUIRED)
                    - lockedTime (str): When it was locked (RFC 3339 format) (REQUIRED)
                - bucketPolicyOnly (Dict[str, Any]): Legacy bucket policy only config
                    - enabled (bool): Whether enabled (REQUIRED)
                    - lockedTime (str): When it was locked (RFC 3339 format) (REQUIRED)
                - publicAccessPrevention (str): Public access prevention ("inherited" or "enforced") (REQUIRED)
            - ipFilter (Dict[str, Any]): IP filter configuration
                - mode (str): Filter mode ("Enabled" or "Disabled") (REQUIRED)
                - publicNetworkSource (Dict[str, List[str]]): Public network sources
                    - allowedIpCidrRanges (List[str]): List of allowed IP CIDR ranges (REQUIRED)
                - vpcNetworkSources (List[Dict[str, Any]]): VPC network sources
                    - network (str): VPC network resource name (REQUIRED)
                    - allowedIpCidrRanges (List[str]): List of allowed IP CIDR ranges (REQUIRED)
            - lifecycle (Dict[str, List[Dict[str, Any]]]): Lifecycle management rules
                - rule (List[Dict[str, Any]]): List of lifecycle rules (REQUIRED)
                    - action (Dict[str, str]): Action to take (REQUIRED)
                        - type (str): Action type (Delete, SetStorageClass, AbortIncompleteMultipartUpload) (REQUIRED)
                        - storageClass (str): Target storage class for SetStorageClass action (REQUIRED)
                    - condition (Dict[str, Any]): Conditions for applying the rule (REQUIRED)
                        - age (int): Age of object in days (REQUIRED)
                        - createdBefore (str): Date in RFC 3339 format (REQUIRED)
                        - customTimeBefore (str): Date in RFC 3339 format (REQUIRED)
                        - daysSinceCustomTime (int): Days since custom time (REQUIRED)
                        - daysSinceNoncurrentTime (int): Days since noncurrent time (REQUIRED)
                        - isLive (bool): Whether object is live (REQUIRED)
                        - matchesPattern (str): Regular expression pattern (REQUIRED)
                        - matchesPrefix (List[str]): Object name prefixes (REQUIRED)
                        - matchesSuffix (List[str]): Object name suffixes (REQUIRED)
                        - matchesStorageClass (List[str]): Storage classes to match (REQUIRED)
                        - noncurrentTimeBefore (str): Date in RFC 3339 format (REQUIRED)
                        - numNewerVersions (int): Number of newer versions (REQUIRED)
            - autoclass (Dict[str, Any]): Autoclass configuration
                - enabled (bool): Whether autoclass is enabled (REQUIRED)
                - toggleTime (str): Time autoclass was toggled (RFC 3339 format) (REQUIRED)
                - terminalStorageClass (str): Terminal storage class (NEARLINE or ARCHIVE) (REQUIRED)
                - terminalStorageClassUpdateTime (str): Time terminal class was updated (RFC 3339) (REQUIRED)
            - versioning (Dict[str, bool]): Versioning configuration
                - enabled (bool): Whether versioning is enabled (REQUIRED)
            - website (Dict[str, str]): Website configuration
                - mainPageSuffix (str): Main page suffix (e.g., "index.html") (REQUIRED)
                - notFoundPage (str): 404 page (e.g., "404.html") (REQUIRED)
            - logging (Dict[str, str]): Access logging configuration
                - logBucket (str): Destination bucket for logs (REQUIRED)
                - logObjectPrefix (str): Prefix for log objects (REQUIRED)
            - retentionPolicy (Dict[str, Any]): Retention policy
                - effectiveTime (str): When policy became effective (RFC 3339 format) (REQUIRED)
                - isLocked (bool): Whether policy is locked (REQUIRED)
                - retentionPeriod (str): Retention period in seconds (REQUIRED)
            - objectRetention (Dict[str, str]): Object retention configuration
                - mode (str): Object retention mode (REQUIRED)
            - softDeletePolicy (Dict[str, str]): Soft delete policy
                - retentionDurationSeconds (str): Retention duration in seconds (REQUIRED)
                - effectiveTime (str): When policy became effective (RFC 3339 format) (REQUIRED)
            - encryption (Dict[str, str]): Encryption configuration
                - defaultKmsKeyName (str): Default KMS key resource name (REQUIRED)
            - owner (Dict[str, str]): Bucket owner information
                - entity (str): Owner entity (REQUIRED)
                - entityId (str): Owner entity ID (REQUIRED)
            - labels (Dict[str, str]): User-defined labels as arbitrary key-value pairs where:
                - Keys are user-defined strings (max 63 characters) (REQUIRED)
                - Values are user-defined strings (max 63 characters) (REQUIRED)
            - defaultEventBasedHold (bool): Default event-based hold for new objects (REQUIRED)
            - rpo (str): Recovery Point Objective ("DEFAULT" or "ASYNC_TURBO") (REQUIRED)
            - locationType (str): Type of location (e.g., "region", "dual-region") (REQUIRED)
            - projectNumber (str): Project number bucket belongs to (REQUIRED)
            - satisfiesPZS (bool): Whether bucket satisfies Zone Separation (REQUIRED)
            - satisfiesPZI (bool): Whether bucket satisfies Zone Isolation (REQUIRED)
            Defaults to None. Note: While the parameter itself is optional, if provided, all nested properties are required.

    Returns:
        Tuple[Dict[str, Any], int]: A tuple containing:
            - Dictionary with complete bucket metadata (filtered by projection if specified):
                - name (str): Bucket name (preserved from original)
                - id (str): Bucket ID (preserved from original)
                - kind (str): Resource kind (always "storage#bucket")
                - storageClass (str): Storage class from bucket_request
                - location (str): Location from bucket_request
                - metageneration (str): Incremented metageneration
                - generation (str): Bucket generation (preserved from original)
                - timeCreated (str): Original creation time (preserved)
                - updated (str): Current update time (RFC 3339 format)
                - etag (str): Updated entity tag
                - projectNumber (str): Project number (preserved from original)
                - project (str): Project ID (preserved from original)
                - acl (List[Dict[str, Any]]): Access control list (omitted if projection="noAcl")
                - defaultObjectAcl (List[Dict[str, Any]]): Default object ACL (omitted if projection="noAcl")
                - billing (Dict[str, bool]): Billing configuration from bucket_request
                - cors (List[Dict[str, Any]]): CORS configuration from bucket_request
                - versioning (Dict[str, bool]): Versioning configuration from bucket_request
                - lifecycle (Dict[str, List[Dict[str, Any]]]): Lifecycle config from bucket_request
                - [All other fields as specified in bucket_request]
            - HTTP status code (200 for success, 400/404/412 for errors)

    Raises:
        TypeError: If bucket is not a string, or if optional string parameters are not strings.
        ValueError: If predefinedAcl, predefined_default_object_acl, or projection have invalid values.
        ValidationError: If bucket_request contains invalid data according to BucketRequest model.
        AttributeError: If bucket_request is None (required for update operation).
    """
    # Input validation
    if not isinstance(bucket, str):
        return {"error": "Bucket name must be a string"}, 400
    
    if if_metageneration_match is not None and not isinstance(if_metageneration_match, str):
        return {"error": "if_metageneration_match must be a string or None"}, 400
        
    if if_metageneration_not_match is not None and not isinstance(if_metageneration_not_match, str):
        return {"error": "if_metageneration_not_match must be a string or None"}, 400

    # Validate predefinedAcl using enum if available
    if predefinedAcl is not None:
        if PredefinedBucketAcl:
            valid_acls = [acl.value for acl in PredefinedBucketAcl]
        else:
            valid_acls = ["authenticatedRead", "private", "projectPrivate", "publicRead", "publicReadWrite"]
        
        if predefinedAcl not in valid_acls:
            return {"error": f"Invalid predefinedAcl. Must be one of: {valid_acls}"}, 400

    # Validate predefined_default_object_acl using enum if available
    if predefined_default_object_acl is not None:
        if PredefinedDefaultObjectAcl:
            valid_default_acls = [acl.value for acl in PredefinedDefaultObjectAcl]
        else:
            valid_default_acls = ["authenticatedRead", "bucketOwnerFullControl", "bucketOwnerRead", 
                                 "private", "projectPrivate", "publicRead"]
        
        if predefined_default_object_acl not in valid_default_acls:
            return {"error": f"Invalid predefined_default_object_acl. Must be one of: {valid_default_acls}"}, 400

    # Validate projection using enum if available
    if projection is not None:
        if BucketProjection:
            valid_projections = [proj.value for proj in BucketProjection]
        else:
            valid_projections = ["full", "noAcl"]
            
        if projection not in valid_projections:
            return {"error": f"Invalid projection. Must be one of: {valid_projections}"}, 400

    # Check if bucket exists
    if bucket not in DB.get("buckets", {}):
        return {"error": f"Bucket {bucket} not found"}, 404

    bucket_data = DB["buckets"][bucket]

    # Check metageneration conditions
    current_metageneration = str(bucket_data.get("metageneration", 0))
    
    if (if_metageneration_match is not None and 
        current_metageneration != if_metageneration_match):
        return {"error": "Metageneration mismatch"}, 412

    if (if_metageneration_not_match is not None and 
        current_metageneration == if_metageneration_not_match):
        return {"error": "Metageneration mismatch"}, 412

    # For update (PUT), we need bucket_request to be provided
    if bucket_request is None:
        return {"error": "bucket_request is required for update operation"}, 400
        
    if not isinstance(bucket_request, dict):
        return {"error": "Invalid bucket_request; must be a dictionary"}, 400

    try:
        protected_fields = ['id', 'kind', 'timeCreated', 'generation']
        sanitized_request = {k: v for k, v in bucket_request.items() if k not in protected_fields}
            
        if BucketRequest:
            # Validate the sanitized request using Pydantic model
            validated_bucket = BucketRequest(**sanitized_request)
            validated_data = validated_bucket.model_dump(exclude_none=False)
        else:
            # Fallback when models not available
            validated_data = sanitized_request.copy()
        
        # Preserve certain fields that should not be overridden
        preserved_fields = {
            'name': bucket_data.get('name', bucket),  # Keep original bucket name
            'id': bucket_data.get('id'),
            'kind': 'storage#bucket',
            'timeCreated': bucket_data.get('timeCreated'),
            'generation': bucket_data.get('generation'),
            'project': bucket_data.get('project'),  # Preserve project association
        }
        
        # Start with validated data and overlay preserved fields
        new_bucket_data = validated_data.copy()
        for key, value in preserved_fields.items():
            if value is not None:
                new_bucket_data[key] = value
        
        # Apply predefined ACLs if specified (they override bucket_request)
        if predefinedAcl:
            new_bucket_data["acl"] = predefinedAcl
        if predefined_default_object_acl:
            new_bucket_data["defaultObjectAcl"] = predefined_default_object_acl
            
    except ValidationError as e:
        error_details = []
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            error_details.append(f"{field}: {error['msg']}")
        return {"error": f"Validation error: {'; '.join(error_details)}"}, 400
    except Exception as e:
        return {"error": f"Validation error: {str(e)}"}, 400

    # Increment metageneration
    new_bucket_data["metageneration"] = str(int(bucket_data.get("metageneration", 0)) + 1)
    
    # Update the updated timestamp
    new_bucket_data["updated"] = datetime.now().isoformat() + "Z"

    # Replace the bucket data completely (update semantics)
    DB["buckets"][bucket] = new_bucket_data

    # Apply projection for response
    if projection == "noAcl":
        response_data = {k: v for k, v in new_bucket_data.items() 
                        if k not in ["acl", "defaultObjectAcl"]}
    else:
        response_data = new_bucket_data.copy()

    return response_data, 200
