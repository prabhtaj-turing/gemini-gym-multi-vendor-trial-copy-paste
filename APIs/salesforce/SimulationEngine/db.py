# APIs/salesforce/SimulationEngine/db.py

"""
Database structure and persistence helpers for Salesforce API Simulation.
"""
import json
import datetime
from datetime import datetime, timedelta
from typing import Dict, Any
import os


# ---------------------------------------------------------------------------------------
# In-Memory Database Structure
# ---------------------------------------------------------------------------------------
DB: dict = {
    "Event": {},
    "Task": {
        "layouts": [
            {
                "description": "Standard layout for Task object.",
                "id": "00h000000000001AAA",
                "name": "TaskLayout",
                "label": "Task Layout",
                "editLayoutSections": [
                    {
                        "heading": "Task Information",
                        "columns": 2,
                        "useFfPage": False,
                        "rows": [
                            [
                                {
                                    "behavior": "Required",
                                    "editable": True,
                                    "label": "Subject",
                                    "readable": True,
                                    "required": True,
                                    "field": "Subject",
                                    "type": "Field"
                                },
                                {
                                    "behavior": "Edit",
                                    "editable": True,
                                    "label": "Due Date",
                                    "readable": True,
                                    "required": False,
                                    "field": "ActivityDate",
                                    "type": "Field"
                                }
                            ],
                            [
                                {
                                    "behavior": "Edit",
                                    "editable": True,
                                    "label": "Status",
                                    "readable": True,
                                    "required": True,
                                    "field": "Status",
                                    "type": "Field"
                                },
                                {
                                    "behavior": "Edit",
                                    "editable": True,
                                    "label": "Priority",
                                    "readable": True,
                                    "required": True,
                                    "field": "Priority",
                                    "type": "Field"
                                }
                            ],
                            [
                                {
                                    "behavior": "Edit",
                                    "editable": True,
                                    "label": "Name",
                                    "readable": True,
                                    "required": False,
                                    "field": "WhoId",
                                    "type": "Field"
                                },
                                {
                                    "behavior": "Edit",
                                    "editable": True,
                                    "label": "Related To",
                                    "readable": True,
                                    "required": False,
                                    "field": "WhatId",
                                    "type": "Field"
                                }
                            ],
                            [
                                {
                                    "behavior": "Edit",
                                    "editable": True,
                                    "label": "Assigned To",
                                    "readable": True,
                                    "required": True,
                                    "field": "OwnerId",
                                    "type": "Field"
                                },
                                {
                                    "behavior": "EmptySpace",
                                    "type": "EmptySpace"
                                }
                            ]
                        ]
                    },
                    {
                        "heading": "Additional Information",
                        "columns": 2,
                        "useFfPage": False,
                        "rows": [
                            [
                                {
                                    "behavior": "Edit",
                                    "editable": True,
                                    "label": "Phone",
                                    "readable": True,
                                    "required": False,
                                    "field": "Phone",
                                    "type": "Field"
                                },
                                {
                                    "behavior": "Edit",
                                    "editable": True,
                                    "label": "Email",
                                    "readable": True,
                                    "required": False,
                                    "field": "Email",
                                    "type": "Field"
                                }
                            ]
                        ]
                    },
                    {
                        "heading": "Description Information",
                        "columns": 1,
                        "useFfPage": False,
                        "rows": [
                            [
                                {
                                    "behavior": "Edit",
                                    "editable": True,
                                    "label": "Comments",
                                    "readable": True,
                                    "required": False,
                                    "field": "Description",
                                    "type": "Field"
                                }
                            ]
                        ]
                    }
                ],
                "detailLayoutSections": [
                    {
                        "heading": "Task Information",
                        "columns": 2,
                        "useFfPage": False,
                        "rows": [
                            [
                                {
                                    "behavior": "Required",
                                    "editable": False,
                                    "label": "Subject",
                                    "readable": True,
                                    "required": True,
                                    "field": "Subject",
                                    "type": "Field"
                                },
                                {
                                    "behavior": "Readonly",
                                    "editable": False,
                                    "label": "Due Date",
                                    "readable": True,
                                    "required": False,
                                    "field": "ActivityDate",
                                    "type": "Field"
                                }
                            ],
                            [
                                {
                                    "behavior": "Readonly",
                                    "editable": False,
                                    "label": "Status",
                                    "readable": True,
                                    "required": True,
                                    "field": "Status",
                                    "type": "Field"
                                },
                                {
                                    "behavior": "Readonly",
                                    "editable": False,
                                    "label": "Priority",
                                    "readable": True,
                                    "required": True,
                                    "field": "Priority",
                                    "type": "Field"
                                }
                            ],
                            [
                                {
                                    "behavior": "Readonly",
                                    "editable": False,
                                    "label": "Name",
                                    "readable": True,
                                    "required": False,
                                    "field": "WhoId",
                                    "type": "Field"
                                },
                                {
                                    "behavior": "Readonly",
                                    "editable": False,
                                    "label": "Related To",
                                    "readable": True,
                                    "required": False,
                                    "field": "WhatId",
                                    "type": "Field"
                                }
                            ],
                            [
                                {
                                    "behavior": "Readonly",
                                    "editable": False,
                                    "label": "Assigned To",
                                    "readable": True,
                                    "required": True,
                                    "field": "OwnerId",
                                    "type": "Field"
                                },
                                {
                                    "behavior": "EmptySpace",
                                    "type": "EmptySpace"
                                }
                            ]
                        ]
                    },
                    {
                        "heading": "Additional Information",
                        "columns": 2,
                        "useFfPage": False,
                        "rows": [
                            [
                                {
                                    "behavior": "Readonly",
                                    "editable": False,
                                    "label": "Phone",
                                    "readable": True,
                                    "required": False,
                                    "field": "Phone",
                                    "type": "Field"
                                },
                                {
                                    "behavior": "Readonly",
                                    "editable": False,
                                    "label": "Email",
                                    "readable": True,
                                    "required": False,
                                    "field": "Email",
                                    "type": "Field"
                                }
                            ]
                        ]
                    },
                    {
                        "heading": "Description Information",
                        "columns": 1,
                        "useFfPage": False,
                        "rows": [
                            [
                                {
                                    "behavior": "Readonly",
                                    "editable": False,
                                    "label": "Comments",
                                    "readable": True,
                                    "required": False,
                                    "field": "Description",
                                    "type": "Field"
                                }
                            ]
                        ]
                    }
                ],
                "standardButtons": [
                    "Edit",
                    "Delete",
                    "View",
                    "MarkComplete",
                    "Clone"
                ],
                "layoutAssignments": [
                    {
                        "layoutId": "00h000000000001AAA",
                        "recordTypeId": None,
                        "profileId": None
                    },
                    {
                        "layoutId": "00h000000000001AAA",
                        "recordTypeId": "012000000000000BBB",
                        "profileId": "00e000000000000CCC"
                    }
                ]
            }

        ],
        "tasks": [
            {
                "description": "Mock Task records with system timestamps.",
                "id": "00T000000000001DDD",
                "Subject": "Follow up with Prospect X",
                "Status": "Open",
                "Priority": "Normal",
                "ActivityDate": "2023-11-10",
                "OwnerId": "005000000000001EEE",
                "WhoId": "003000000000001FFF",
                "WhatId": "001000000000001GGG",
                "CreatedDate": "2023-10-25T09:00:00.000Z",
                "SystemModstamp": "2023-10-25T09:00:00.000Z",
                "IsDeleted": False
            },
            {
                "id": "00T000000000002HHH",
                "Subject": "Schedule demo for Account Y",
                "Status": "In Progress",
                "Priority": "High",
                "ActivityDate": "2023-11-15",
                "OwnerId": "005000000000001EEE",
                "WhoId": "003000000000002III",
                "WhatId": "001000000000002JJJ",
                "CreatedDate": "2023-10-26T10:00:00.000Z",
                "SystemModstamp": "2023-10-27T11:30:00.000Z",
                "IsDeleted": False
            },
            {
                "id": "00T000000000003KKK",
                "Subject": "Log call with Customer Z",
                "Status": "Completed",
                "Priority": "Normal",
                "ActivityDate": "2023-10-20",
                "OwnerId": "005000000000002LLL",
                "WhoId": "003000000000003MMM",
                "WhatId": "001000000000003NNN",
                "CreatedDate": "2023-10-19T14:00:00.000Z",
                "SystemModstamp": "2023-10-20T09:00:00.000Z",
                "IsDeleted": False
            }

        ],
        "deletedTasks": [
            {
                "description": "Mock deleted Task records for getDeleted.",
                "id": "00T000000000004OOO",
                "deletedDate": "2023-10-27T10:05:30.000Z"
            },
            {
                "id": "00T000000000005PPP",
                "deletedDate": "2023-10-28T09:15:00.000Z"
            }

        ]
    },
    "TaskSObject": {
        "activateable": False,
        "associateEntityType": None,
        "associateParentEntity": None,
        "actionOverrides": [
            {
                "formFactor": "Large",
                "isAvailableInTouch": True,
                "name": "New",
                "pageId": "07p5g000001ABCD",
                "url": "/apex/c__NewProjectOverride"
            },
            {
                "formFactor": "Small",
                "isAvailableInTouch": True,
                "name": "Tab",
                "pageId": "07p5g000001EFGH",
                "url": None
            }
        ],
        "childRelationships": [
            {
                "cascadeDelete": True,
                "childSObject": "TaskWhoRelation",
                "deprecatedAndHidden": False,
                "field": "TaskId",
                "junctionIdListNames": [],
                "junctionReferenceTo": [],
                "relationshipName": "TaskWhoRelations",
                "restrictedDelete": False
            },
            {
                "cascadeDelete": False,
                "childSObject": "Attachment",
                "deprecatedAndHidden": False,
                "field": "ParentId",
                "junctionIdListNames": [],
                "junctionReferenceTo": [],
                "relationshipName": "Attachments",
                "restrictedDelete": False
            },
            {
                "cascadeDelete": True,
                "childSObject": "ContentDocumentLink",
                "deprecatedAndHidden": False,
                "field": "LinkedEntityId",
                "junctionIdListNames": [],
                "junctionReferenceTo": [],
                "relationshipName": "ContentDocumentLinks",
                "restrictedDelete": False
            }
        ],
        "compactLayoutable": True,
        "createable": True,
        "custom": False,
        "customSetting": False,
        "dataTranslationEnabled": False,
        "deepCloneable": False,
        "defaultImplementation": None,
        "deletable": True,
        "deprecatedAndHidden": False,
        "extendedBy": None,
        "extendsInterfaces": None,
        "feedEnabled": True,
        "fields": [
            {
                "name": "Id", "label": "Task ID", "type": "id", "soapType": "tns:ID", "length": 18,
                "byteLength": 18, "nillable": False, "permissionable": True, "createable": False,
                "updateable": False, "filterable": True, "groupable": True, "sortable": True,
                "custom": False, "calculated": False, "idLookup": True, "defaultedOnCreate": True, "digits": 0, "nameField": False, "precision": 0, "scale": 0, "unique": False
            },
            {
                "name": "Subject", "label": "Subject", "type": "string", "soapType": "xsd:string", "length": 255,
                "byteLength": 765, "nillable": True, "permissionable": True, "createable": True,
                "updateable": True, "filterable": True, "groupable": True, "sortable": True,
                "custom": False, "calculated": False, "idLookup": False, "defaultedOnCreate": False,
                "inlineHelpText": "A brief summary of the to-do item.",
                "digits": 0, "nameField": False, "unique": False
            },
            {
                "name": "ActivityDate", "label": "Due Date", "type": "date", "soapType": "xsd:date", "length": 0,
                "byteLength": 0, "nillable": True, "permissionable": True, "createable": True,
                "updateable": True, "filterable": True, "groupable": True, "sortable": True,
                "custom": False, "calculated": False, "idLookup": False, "defaultedOnCreate": False,
                "digits": 0, "nameField": False, "unique": False
            },
            {
                "name": "Status", "label": "Status", "type": "picklist", "soapType": "xsd:string", "length": 255,
                "byteLength": 765, "nillable": False, "permissionable": True, "createable": True,
                "updateable": True, "filterable": True, "groupable": True, "sortable": True,
                "custom": False, "calculated": False, "idLookup": False, "defaultedOnCreate": True,
                "restrictedPicklist": False, "dependentPicklist": False, "digits": 0, "nameField": False, "unique": False,
                "picklistValues": [
                    {"active": True, "defaultValue": True,
                     "label": "Not Started", "value": "Not Started", "validFor": None},
                    {"active": True, "defaultValue": False,
                     "label": "In Progress", "value": "In Progress", "validFor": None},
                    {"active": True, "defaultValue": False,
                     "label": "Completed", "value": "Completed", "validFor": None},
                    {"active": True, "defaultValue": False,
                     "label": "Waiting on someone else", "value": "Waiting on someone else", "validFor": None},
                    {"active": True, "defaultValue": False,
                     "label": "Deferred", "value": "Deferred", "validFor": None}
                ]
            },
            {
                "name": "Priority", "label": "Priority", "type": "picklist", "soapType": "xsd:string", "length": 255,
                "byteLength": 765, "nillable": False, "permissionable": True, "createable": True,
                "updateable": True, "filterable": True, "groupable": True, "sortable": True,
                "custom": False, "calculated": False, "idLookup": False, "defaultedOnCreate": True,
                "restrictedPicklist": False, "dependentPicklist": False, "digits": 0, "nameField": False, "unique": False,
                "picklistValues": [
                    {"active": True, "defaultValue": False,
                     "label": "High", "value": "High", "validFor": None},
                    {"active": True, "defaultValue": True,
                     "label": "Normal", "value": "Normal", "validFor": None},
                    {"active": True, "defaultValue": False,
                     "label": "Low", "value": "Low", "validFor": None}
                ]
            },
            {
                "name": "IsClosed", "label": "Closed", "type": "boolean", "soapType": "xsd:boolean", "length": 0,
                "byteLength": 0, "nillable": False, "permissionable": True, "createable": False,
                "updateable": False, "filterable": True, "groupable": True, "sortable": True,
                "custom": False, "calculated": True, "idLookup": False, "defaultedOnCreate": True,
                "digits": 0, "nameField": False, "unique": False
            },
            {
                "name": "WhoId", "label": "Name ID", "type": "reference", "soapType": "tns:ID", "length": 18,
                "byteLength": 18, "nillable": True, "permissionable": True, "createable": True,
                "updateable": True, "filterable": True, "groupable": True, "sortable": True,
                "custom": False, "calculated": False, "idLookup": False, "defaultedOnCreate": False,
                "polymorphicForeignKey": True, "referenceTo": ["Contact", "Lead"], "relationshipName": "Who", "precision": 0, "scale": 0, "unique": False
            },
            {
                "name": "WhatId", "label": "Related To ID", "type": "reference", "soapType": "tns:ID", "length": 18,
                "byteLength": 18, "nillable": True, "permissionable": True, "createable": True,
                "updateable": True, "filterable": True, "groupable": True, "sortable": True,
                "custom": False, "calculated": False, "idLookup": False, "defaultedOnCreate": False,
                "polymorphicForeignKey": True, "referenceTo": ["Account", "Opportunity", "Campaign", "Case", "Contract"],
                "relationshipName": "What", "precision": 0, "scale": 0, "unique": False
            },
            {
                "name": "OwnerId", "label": "Assigned To ID", "type": "reference", "soapType": "tns:ID", "length": 18,
                "byteLength": 18, "nillable": False, "permissionable": True, "createable": True,
                "updateable": True, "filterable": True, "groupable": True, "sortable": True,
                "custom": False, "calculated": False, "idLookup": False, "defaultedOnCreate": True,
                "referenceTo": ["User", "Group"], "relationshipName": "Owner", "precision": 0, "scale": 0, "unique": False
            },
            {
                "name": "Description", "label": "Comments", "type": "textarea", "soapType": "xsd:string", "length": 32000,
                "byteLength": 32000, "nillable": True, "permissionable": True, "createable": True,
                "updateable": True, "filterable": False, "groupable": False, "sortable": False,
                "custom": False, "calculated": False, "idLookup": False, "defaultedOnCreate": False,
                "precision": 0, "scale": 0, "unique": False
            },
            {
                "name": "SystemModstamp", "label": "System Modstamp", "type": "datetime", "soapType": "xsd:dateTime", "length": 0,
                "byteLength": 0, "nillable": False, "permissionable": True, "createable": False,
                "updateable": False, "filterable": True, "groupable": False, "sortable": True,
                "custom": False, "calculated": True, "idLookup": False, "defaultedOnCreate": True,
                "precision": 0, "scale": 0, "unique": False
            }
        ],
        "implementedBy": None,
        "implementsInterfaces": None,
        "isInterface": False,
        "keyPrefix": "00T",
        "label": "Task",
        "labelPlural": "Tasks",
        "layoutable": True,
        "mergeable": False,
        "mruEnabled": True,
        "name": "Task",
        "namedLayoutInfos": {
            "name": "Default"
        },
        "networkScopeFieldName": None,
        "queryable": True,
        "recordTypeInfos": [
            {
                "available": True, "defaultRecordTypeMapping": True, "master": True,
                "name": "Master", "developerName": "Master",
                "recordTypeId": "012000000000000AAA",
                "urls": {"layout": "/services/data/v58.0/sobjects/Task/describe/layouts/012000000000000AAA"}
            },
            {
                "available": True, "defaultRecordTypeMapping": False, "master": False,
                "name": "Sales Follow-up", "developerName": "Sales_Follow_up",
                "recordTypeId": "0125g000001AbCdEfG",
                "urls": {"layout": "/services/data/v58.0/sobjects/Task/describe/layouts/0125g000001AbCdEfG"}
            }
        ],
        "replicateable": True,
        "retrieveable": True,
        "searchable": True,
        "searchLayoutable": True,
        "supportedScopes": [
            {"label": "My tasks", "name": "mine"},
            {"label": "My team's tasks", "name": "team"}
        ],
        "triggerable": True,
        "undeletable": True,
        "updateable": True,
        "urlDetail": "https://yourInstance.salesforce.com/{ID}",
        "urlEdit": "https://yourInstance.salesforce.com/{ID}/e",
        "urlNew": "https://yourInstance.salesforce.com/00T/e"
    },
    "DeletedTask": {
        "deleted-task-1": {
            "Id": "deleted-task-1",
            "Subject": "Follow up with client",
            "Status": "Completed",
            "Priority": "High",
            "ActivityDate": "2024-01-15",
            "Description": "Call client to discuss proposal",
            "OwnerId": "005XXXXXXXXXXXXXXX",
            "WhoId": "003XXXXXXXXXXXXXXX",
            "WhatId": "006XXXXXXXXXXXXXXX",
            "deletedDate": "2024-01-20T10:30:00Z"
        },
        "deleted-task-2": {
            "Id": "deleted-task-2",
            "Subject": "Review quarterly report",
            "Status": "Not Started",
            "Priority": "Normal",
            "ActivityDate": "2024-01-25",
            "Description": "Review and approve Q4 financial report",
            "OwnerId": "005XXXXXXXXXXXXXXX",
            "WhoId": None,
            "WhatId": "006XXXXXXXXXXXXXXX",
            "deletedDate": "2024-01-22T14:45:00Z"
        },
        "deleted-task-3": {
            "Id": "deleted-task-3",
            "Subject": "Schedule team meeting",
            "Status": "In Progress",
            "Priority": "Low",
            "ActivityDate": "2024-01-18",
            "Description": "Coordinate with team for weekly sync",
            "OwnerId": "005XXXXXXXXXXXXXXX",
            "WhoId": None,
            "WhatId": None,
            "deletedDate": "2024-01-19T09:15:00Z"
        },
        "deleted-task-4": {
            "Id": "deleted-task-4",
            "Subject": "Update customer database",
            "Status": "Completed",
            "Priority": "Normal",
            "ActivityDate": "2024-01-10",
            "Description": "Clean up and update customer contact information",
            "OwnerId": "005XXXXXXXXXXXXXXX",
            "WhoId": "003XXXXXXXXXXXXXXX",
            "WhatId": "001XXXXXXXXXXXXXXX",
            "deletedDate": "2024-01-12T16:20:00Z"
        },
        "deleted-task-5": {
            "Id": "deleted-task-5",
            "Subject": "Prepare presentation slides",
            "Status": "Waiting on someone else",
            "Priority": "High",
            "ActivityDate": "2024-01-30",
            "Description": "Create slides for board meeting presentation",
            "OwnerId": "005XXXXXXXXXXXXXXX",
            "WhoId": None,
            "WhatId": "006XXXXXXXXXXXXXXX",
            "deletedDate": "2024-01-28T11:00:00Z"
        },
        "deleted-task-6": {
            "Id": "deleted-task-6",
            "Subject": "Send follow-up emails",
            "Status": "Completed",
            "Priority": "Normal",
            "ActivityDate": "2024-01-05",
            "Description": "Send follow-up emails to prospects from last week",
            "OwnerId": "005XXXXXXXXXXXXXXX",
            "WhoId": "003XXXXXXXXXXXXXXX",
            "WhatId": None,
            "deletedDate": "2024-01-08T13:30:00Z"
        },
        "deleted-task-7": {
            "Id": "deleted-task-7",
            "Subject": "Review competitor analysis",
            "Status": "Not Started",
            "Priority": "High",
            "ActivityDate": "2024-01-20",
            "Description": "Analyze competitor strategies and market positioning",
            "OwnerId": "005XXXXXXXXXXXXXXX",
            "WhoId": None,
            "WhatId": "006XXXXXXXXXXXXXXX",
            "deletedDate": "2024-01-21T15:45:00Z"
        },
        "deleted-task-8": {
            "Id": "deleted-task-8",
            "Subject": "Update project timeline",
            "Status": "In Progress",
            "Priority": "Normal",
            "ActivityDate": "2024-01-15",
            "Description": "Update project timeline based on recent developments",
            "OwnerId": "005XXXXXXXXXXXXXXX",
            "WhoId": None,
            "WhatId": "006XXXXXXXXXXXXXXX",
            "deletedDate": "2024-01-16T08:20:00Z"
        }
    }
}

# -------------------------------------------------------------------
# Persistence Helpers
# -------------------------------------------------------------------


def save_state(filepath: str) -> None:
    """Saves the current state of the API to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(DB, f)


def load_state(filepath: str) -> None:
    """Loads the API state from a JSON file."""
    global DB
    with open(filepath, "r") as f:
        state = json.load(f)
    # Instead of reassigning DB, update it in place:
    DB.clear()

    DB.update(state)
