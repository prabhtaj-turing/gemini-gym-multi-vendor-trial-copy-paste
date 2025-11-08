import unittest
import copy
from datetime import datetime, timezone
import uuid # Keep for _validate_uuid if it's still used in other tests

from google_slides.SimulationEngine import utils 
from google_slides.SimulationEngine.db import DB
from google_slides.SimulationEngine import custom_errors # Import the module
from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_slides.SimulationEngine.models import PresentationModel
from google_slides.SimulationEngine.models import CreatePresentationRequest
from .. import (batch_update_presentation, create_presentation, get_presentation)

class TestGetPresentation(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        self.user_id = "me"
        utils._ensure_user(self.user_id) 
        DB.clear()

        DB.update({
              "users": {
                "me": {
                  "about": {
                    "kind": "drive#about",
                    "storageQuota": {
                      "limit": "0",
                      "usageInDrive": "0",
                      "usageInDriveTrash": "0",
                      "usage": "0"
                    },
                    "driveThemes": False,
                    "canCreateDrives": False,
                    "importFormats": {},
                    "exportFormats": {},
                    "appInstalled": False,
                    "user": {
                      "displayName": "",
                      "kind": "drive#user",
                      "me": True,
                      "permissionId": "",
                      "emailAddress": ""
                    },
                    "folderColorPalette": "",
                    "maxImportSizes": {},
                    "maxUploadSize": "0"
                  },
                  "files": {
                    "pres1": {
                      "id": "pres1",
                      "driveId": "",
                      "name": "Project Plan",
                      "mimeType": "application/vnd.google-apps.presentation",
                      "createdTime": "2025-03-01T10:00:00Z",
                      "modifiedTime": "2025-03-10T10:00:00Z",
                      "trashed": False,
                      "starred": False,
                      "parents": [
                        "drive-1"
                      ],
                      "owners": [
                        "john.doe@gmail.com"
                      ],
                      "size": "102400",
                      "permissions": [
                        {
                          "id": "permission-1",
                          "role": "owner",
                          "type": "user",
                          "emailAddress": "john.doe@gmail.com"
                        }
                      ],
                      "presentationId": "pres1",
                      "title": "Test Presentation 1",
                      "slides": [
                        {
                          "objectId": "slide1_page1",
                          "pageType": "SLIDE",
                          "pageProperties": {
                            "backgroundColor": {
                              "opaqueColor": {
                                "rgbColor": {
                                  "red": 1.0,
                                  "green": 0.0,
                                  "blue": 0.0
                                }
                              }
                            }
                          },
                          "slideProperties": {
                            "masterObjectId": "master1",
                            "layoutObjectId": "layout_for_slide1"
                          },
                          "pageElements": [
                            {
                              "objectId": "element1_slide1",
                              "size": {
                                "width": {
                                  "magnitude": 200,
                                  "unit": "PT"
                                },
                                "height": {
                                  "magnitude": 100,
                                  "unit": "PT"
                                }
                              },
                              "transform": {
                                "scaleX": 1.0,
                                "translateY": 50.0
                              },
                              "shape": {
                                "shapeType": "RECTANGLE",
                                "text": {}
                              }
                            },
                            {
                              "objectId": "element2_slide1_text",
                              "size": {
                                "width": {
                                  "magnitude": 300,
                                  "unit": "PT"
                                },
                                "height": {
                                  "magnitude": 150,
                                  "unit": "PT"
                                }
                              },
                              "transform": {
                                "scaleX": 1.0,
                                "translateY": 200.0
                              },
                              "shape": {
                                "shapeType": "TEXT_BOX",
                                "text": {
                                  "textElements": [
                                    {
                                      "textRun": {
                                        "content": "Hello ",
                                        "style": {
                                          "fontFamily": "Calibri",
                                          "fontSize": {
                                            "magnitude": 12,
                                            "unit": "PT"
                                          }
                                        }
                                      }
                                    },
                                    {
                                      "textRun": {
                                        "content": "World!",
                                        "style": {
                                          "fontFamily": "Times New Roman",
                                          "fontSize": {
                                            "magnitude": 14,
                                            "unit": "PT"
                                          }
                                        }
                                      }
                                    }
                                  ]
                                }
                              }
                            }
                          ],
                          "revisionId": "rev_slide1"
                        },
                        {
                          "objectId": "slide_minimal",
                          "pageType": "SLIDE",
                          "pageProperties": {
                            "backgroundColor": {
                              "opaqueColor": {
                                "rgbColor": {
                                  "red": 0.95,
                                  "green": 0.95,
                                  "blue": 0.95
                                }
                              }
                            }
                          },
                          "pageElements": [],
                          "revisionId": "rev_slide_minimal",
                          "slideProperties": {
                            "masterObjectId": "master1",
                            "layoutObjectId": "layout_for_slide1"
                          }
                        }
                      ],
                      "masters": [
                        {
                          "objectId": "master_new1",
                          "pageType": "MASTER",
                          "pageProperties": {
                            "backgroundColor": {
                              "opaqueColor": {
                                "rgbColor": {
                                  "red": 0.95,
                                  "green": 0.95,
                                  "blue": 0.95
                                }
                              }
                            }
                          },
                          "masterProperties": {
                            "displayName": "Master Title Placeholder"
                          },
                          "pageElements": [
                            {
                              "objectId": "master_textbox1",
                              "size": {
                                "width": {
                                  "magnitude": 400,
                                  "unit": "PT"
                                },
                                "height": {
                                  "magnitude": 100,
                                  "unit": "PT"
                                }
                              },
                              "transform": {
                                "scaleX": 1.0,
                                "scaleY": 1.0,
                                "translateX": 50.0,
                                "translateY": 50.0,
                                "unit": "PT"
                              },
                              "shape": {
                                "shapeType": "TEXT_BOX",
                                "text": {
                                  "textElements": [
                                    {
                                      "textRun": {
                                        "content": "Master Title Placeholder",
                                        "style": {
                                          "fontFamily": "Arial",
                                          "fontSize": {
                                            "magnitude": 24,
                                            "unit": "PT"
                                          },
                                          "bold": True
                                        }
                                      }
                                    }
                                  ]
                                }
                              }
                            }
                          ],
                          "revisionId": "rev_master_new1"
                        }
                      ],
                      "layouts": [
                        {
                          "objectId": "layout_basic_title_content",
                          "pageType": "LAYOUT",
                          "layoutProperties": {"displayName": "Basic Title and Content"},
                          "pageProperties": {
                            "backgroundColor": {
                              "opaqueColor": {
                                "rgbColor": {
                                  "red": 1.0,
                                  "green": 1.0,
                                  "blue": 1.0
                                }
                              }
                            }
                          },
                          "pageElements": [
                            {
                              "objectId": "title_placeholder_layout",
                              "size": {
                                "width": {
                                  "magnitude": 500,
                                  "unit": "PT"
                                },
                                "height": {
                                  "magnitude": 60,
                                  "unit": "PT"
                                }
                              },
                              "transform": {
                                "scaleX": 1.0,
                                "scaleY": 1.0,
                                "translateX": 40.0,
                                "translateY": 40.0,
                                "unit": "PT"
                              },
                              "shape": {
                                "shapeType": "TEXT_BOX"
                              },
                            },
                            {
                              "objectId": "body_placeholder_layout",
                              "size": {
                                "width": {
                                  "magnitude": 500,
                                  "unit": "PT"
                                },
                                "height": {
                                  "magnitude": 300,
                                  "unit": "PT"
                                }
                              },
                              "transform": {
                                "scaleX": 1.0,
                                "scaleY": 1.0,
                                "translateX": 40.0,
                                "translateY": 120.0,
                                "unit": "PT"
                              },
                              "shape": {
                                "shapeType": "TEXT_BOX"
                              },
                            }
                          ],
                          "revisionId": "rev_layout_basic"
                        }
                      ],
                      "pageSize": {
                        "width": {
                          "magnitude": 9144000,
                          "unit": "EMU"
                        },
                        "height": {
                          "magnitude": 5143500,
                          "unit": "EMU"
                        }
                      },
                      "locale": "",
                      "revisionId": "pres_rev_xyz123_uuid"
                    },
                    'file-1':
                            {
                                "id": "file-1",
                                "name": "Test File 1",
                                "mimeType": "application/pdf",
                                "createdTime": "2025-03-01T10:00:00Z",
                                "modifiedTime": "2025-03-10T10:00:00Z",
                                "trashed": False,
                                "starred": False,
                                "parents": [
                                    "drive-1"
                                ],
                                "owners": [
                                    "john.doe@gmail.com"
                                ],
                                "size": "102400",
                                "permissions": [
                                    {
                                        "id": "permission-1",
                                        "role": "owner",
                                        "type": "user",
                                        "emailAddress": "john.doe@gmail.com"
                                    }
                                ]
                            }
                    }
                },
                "drives": {},
                "comments": {},
                "replies": {},
                "labels": {},
                "accessproposals": {},
                "counters": {
                  "file": 0,
                  "drive": 0,
                  "comment": 0,
                  "reply": 0,
                  "label": 0,
                  "accessproposal": 0,
                  "revision": 0
                }
              }
            })

        # --- Define source data for primary test presentations ---
        self.full_presentation_id = "pres1" 
        self.full_presentation_data = {
            "presentationId": self.full_presentation_id, 
            "title": "Test Presentation 1",
            "slides": [
                    {
                        "objectId": "slide1_page1",
                        "pageType": "SLIDE",
                        "pageProperties": {
                        "backgroundColor": {
                            "opaqueColor": {
                            "rgbColor": {
                                "red": 1.0,
                                "green": 0.0,
                                "blue": 0.0
                            }
                            }
                        }
                        },
                        "slideProperties": {
                        "masterObjectId": "master1",
                        "layoutObjectId": "layout_for_slide1"
                        },
                        "pageElements": [
                        {
                            "objectId": "element1_slide1",
                            "size": {
                            "width": {
                                "magnitude": 200,
                                "unit": "PT"
                            },
                            "height": {
                                "magnitude": 100,
                                "unit": "PT"
                            }
                            },
                            "transform": {
                            "scaleX": 1.0,
                            "translateY": 50.0
                            },
                            "shape": {
                            "shapeType": "RECTANGLE",
                            "text": {}
                            }
                        },
                        {
                            "objectId": "element2_slide1_text",
                            "size": {
                            "width": {
                                "magnitude": 300,
                                "unit": "PT"
                            },
                            "height": {
                                "magnitude": 150,
                                "unit": "PT"
                            }
                            },
                            "transform": {
                            "scaleX": 1.0,
                            "translateY": 200.0
                            },
                            "shape": {
                            "shapeType": "TEXT_BOX",
                            "text": {
                                "textElements": [
                                {
                                    "textRun": {
                                    "content": "Hello ",
                                    "style": {
                                        "fontFamily": "Calibri",
                                        "fontSize": {
                                        "magnitude": 12,
                                        "unit": "PT"
                                        }
                                    }
                                    }
                                },
                                {
                                    "textRun": {
                                    "content": "World!",
                                    "style": {
                                        "fontFamily": "Times New Roman",
                                        "fontSize": {
                                        "magnitude": 14,
                                        "unit": "PT"
                                        }
                                    }
                                    }
                                }
                                ]
                            }
                            }
                        }
                        ],
                        "revisionId": "rev_slide1"
                    },
                    {
                        "objectId": "slide_minimal",
                        "pageType": "SLIDE",
                        "pageProperties": {
                        "backgroundColor": {
                            "opaqueColor": {
                            "rgbColor": {
                                "red": 0.95,
                                "green": 0.95,
                                "blue": 0.95
                            }
                            }
                        }
                        },
                        "pageElements": [],
                        "revisionId": "rev_slide_minimal",
                        "slideProperties": {
                        "masterObjectId": "master1",
                        "layoutObjectId": "layout_for_slide1"
                        }
                    }
                    ],
                    "masters": [
                    {
                        "objectId": "master_new1",
                        "pageType": "MASTER",
                        "pageProperties": {
                        "backgroundColor": {
                            "opaqueColor": {
                            "rgbColor": {
                                "red": 0.95,
                                "green": 0.95,
                                "blue": 0.95
                            }
                            }
                        }
                        },
                        "masterProperties": {
                        "displayName": "Master Title Placeholder"
                        },
                        "pageElements": [
                        {
                            "objectId": "master_textbox1",
                            "size": {
                            "width": {
                                "magnitude": 400,
                                "unit": "PT"
                            },
                            "height": {
                                "magnitude": 100,
                                "unit": "PT"
                            }
                            },
                            "transform": {
                            "scaleX": 1.0,
                            "scaleY": 1.0,
                            "translateX": 50.0,
                            "translateY": 50.0,
                            "unit": "PT"
                            },
                            "shape": {
                            "shapeType": "TEXT_BOX",
                            "text": {
                                "textElements": [
                                {
                                    "textRun": {
                                    "content": "Master Title Placeholder",
                                    "style": {
                                        "fontFamily": "Arial",
                                        "fontSize": {
                                        "magnitude": 24,
                                        "unit": "PT"
                                        },
                                        "bold": True
                                    }
                                    }
                                }
                                ]
                            }
                            }
                        }
                        ],
                        "revisionId": "rev_master_new1"
                    }
                    ],
                    "layouts": [
                    {
                        "objectId": "layout_basic_title_content",
                        "pageType": "LAYOUT",
                        "layoutProperties": {"displayName": "Basic Title and Content"},
                        "pageProperties": {
                        "backgroundColor": {
                            "opaqueColor": {
                            "rgbColor": {
                                "red": 1.0,
                                "green": 1.0,
                                "blue": 1.0
                            }
                            }
                        }
                        },
                        "pageElements": [
                        {
                            "objectId": "title_placeholder_layout",
                            "size": {
                            "width": {
                                "magnitude": 500,
                                "unit": "PT"
                            },
                            "height": {
                                "magnitude": 60,
                                "unit": "PT"
                            }
                            },
                            "transform": {
                            "scaleX": 1.0,
                            "scaleY": 1.0,
                            "translateX": 40.0,
                            "translateY": 40.0,
                            "unit": "PT"
                            },
                            "shape": {
                            "shapeType": "TEXT_BOX"
                            },
                        },
                        {
                            "objectId": "body_placeholder_layout",
                            "size": {
                            "width": {
                                "magnitude": 500,
                                "unit": "PT"
                            },
                            "height": {
                                "magnitude": 300,
                                "unit": "PT"
                            }
                            },
                            "transform": {
                            "scaleX": 1.0,
                            "scaleY": 1.0,
                            "translateX": 40.0,
                            "translateY": 120.0,
                            "unit": "PT"
                            },
                            "shape": {
                            "shapeType": "TEXT_BOX"
                            },
                        }
                        ],
                        "revisionId": "rev_layout_basic"
                    }
                    ],
                    "pageSize": {
                    "width": {
                        "magnitude": 9144000,
                        "unit": "EMU"
                    },
                    "height": {
                        "magnitude": 5143500,
                        "unit": "EMU"
                    }
                    },
                    "locale": "",
                    "revisionId": "pres_rev_xyz123_uuid"
                    }
        self.full_presentation_slides_data = PresentationModel.model_validate(self.full_presentation_data).model_dump()
    
    def test_create_and_get_presentation(self):
        request = {"title": "Test Presentation 2"}
        created_presentation = create_presentation(request)
        presentation_id = created_presentation["presentationId"]
        got_presentation = get_presentation(presentationId=presentation_id)
        print(created_presentation)
        print(got_presentation)
        self.assertEqual(got_presentation["title"], created_presentation["title"])
        self.assertEqual(got_presentation["revisionId"], created_presentation["revisionId"])
        self.assertEqual(got_presentation["pageSize"], created_presentation["pageSize"])
        self.assertEqual(got_presentation["slides"], created_presentation["slides"])
        self.assertEqual(got_presentation["masters"], created_presentation["masters"])
        self.assertEqual(got_presentation["layouts"], created_presentation["layouts"])
        self.assertEqual(got_presentation["notesMaster"], created_presentation["notesMaster"])
        self.assertEqual(got_presentation["locale"], created_presentation["locale"])
    
    def test_create_update_get_presentation(self):
        request = {"title": "Test Presentation 2"}
        created_presentation = create_presentation(request)
        presentationId = created_presentation["presentationId"]
        updated_presentation = batch_update_presentation(
                    presentationId= presentationId,
                    requests= [
                        {
                            "createSlide": {
                                "objectId": "new_slide_id"
                            }
                        },
                        {
                            "createShape": {
                                "objectId": "new_shape_id",
                                "shapeType": "TEXT_BOX",
                                "elementProperties": {
                                    "pageObjectId": "new_slide_id",
                                    "size": {
                                        "width": {"magnitude": 200, "unit": "PT"},
                                        "height": {"magnitude": 100, "unit": "PT"}
                                    }
                                }
                            }
                        },
                        {
                            "insertText": {
                                "objectId": "new_shape_id",
                                "text": "Some text"
                            }
                        }
                    ],
                )
        got_presentation = get_presentation(presentationId=presentationId)
        print("got_presentation")
        print(got_presentation)
        self.assertEqual(got_presentation["presentationId"], updated_presentation["presentationId"])