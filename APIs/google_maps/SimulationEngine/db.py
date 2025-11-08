# google_maps/SimulationEngine/db.py
import json
import os

DB = {
    "place_empire": {
        "areaSummary": {
            "contentBlocks": [
                {
                    "content": {"text": "", "languageCode": ""},
                    "flagContentUri": "",
                    "topic": "",
                }
            ],
            "flagContentUri": "",
        },
        "userRatingCount": 0,
        "servesBeer": False,
        "businessStatus": "",
        "formattedAddress": "",
        "currentSecondaryOpeningHours": [
            {
                "nextCloseTime": "",
                "openNow": True,
                "nextOpenTime": "",
                "periods": [
                    {
                        "open": {
                            "day": 0,
                            "hour": 0,
                            "minute": 0,
                            "date": {"year": 0, "month": 0, "day": 0},
                        },
                        "close": {
                            "day": 0,
                            "hour": 0,
                            "minute": 0,
                            "date": {"year": 0, "month": 0, "day": 0},
                        },
                    }
                ],
                "specialDays": [],
                "weekdayDescriptions": [],
                "secondaryHoursType": "",
            }
        ],
        "pureServiceAreaBusiness": False,
        "servesCoffee": False,
        "delivery": False,
        "takeout": False,
        "iconMaskBaseUri": "",
        "containingPlaces": [{"name": "", "id": ""}],
        "plusCode": {"globalCode": "", "compoundCode": ""},
        "restroom": True,
        "location": {"latitude": 0, "longitude": 0},
        "primaryTypeDisplayName": {"text": "", "languageCode": ""},
        "utcOffsetMinutes": 0,
        "adrFormatAddress": "",
        "id": "",
        "evChargeOptions": {"connectorAggregation": [], "connectorCount": 0},
        "googleMapsUri": "",
        "servesBreakfast": False,
        "goodForGroups": True,
        "goodForWatchingSports": False,
        "shortFormattedAddress": "",
        "liveMusic": False,
        "websiteUri": "",
        "photos": [
            {
                "flagContentUri": "",
                "authorAttributions": [{"displayName": "", "uri": "", "photoUri": ""}],
                "googleMapsUri": "",
                "widthPx": 0,
                "heightPx": 0,
                "name": "",
            }
        ],
        "reservable": False,
        "currentOpeningHours": {
            "nextCloseTime": "",
            "openNow": True,
            "nextOpenTime": "",
            "periods": [
                {
                    "open": {
                        "day": 0,
                        "hour": 0,
                        "minute": 0,
                        "date": {"year": 0, "month": 0, "day": 0},
                    },
                    "close": {
                        "day": 0,
                        "hour": 0,
                        "minute": 0,
                        "date": {"year": 0, "month": 0, "day": 0},
                    },
                }
            ],
            "specialDays": [],
            "weekdayDescriptions": [],
            "secondaryHoursType": "",
        },
        "servesVegetarianFood": False,
        "reviews": [
            {
                "googleMapsUri": "",
                "authorAttribution": {"displayName": "", "uri": "", "photoUri": ""},
                "relativePublishTimeDescription": "",
                "publishTime": "",
                "flagContentUri": "",
                "rating": 0,
                "name": "",
                "text": {"text": "", "languageCode": ""},
                "originalText": {"text": "", "languageCode": ""},
            }
        ],
        "servesWine": False,
        "goodForChildren": True,
        "internationalPhoneNumber": "",
        "menuForChildren": False,
        "servesCocktails": False,
        "priceLevel": "",
        "timeZone": {"id": "", "version": ""},
        "servesDessert": False,
        "addressComponents": [
            {"shortText": "", "types": [], "languageCode": "", "longText": ""}
        ],
        "viewport": {
            "low": {"latitude": 0, "longitude": 0},
            "high": {"latitude": 0, "longitude": 0},
        },
        "rating": 0,
        "iconBackgroundColor": "",
        "servesBrunch": False,
        "priceRange": {
            "startPrice": {"units": "", "nanos": 0, "currencyCode": ""},
            "endPrice": {"units": "", "nanos": 0, "currencyCode": ""},
        },
        "primaryType": "",
        "attributions": [{"provider": "", "providerUri": ""}],
        "regularOpeningHours": {
            "nextCloseTime": "",
            "openNow": True,
            "nextOpenTime": "",
            "periods": [
                {
                    "open": {
                        "day": 0,
                        "hour": 0,
                        "minute": 0,
                        "date": {"year": 0, "month": 0, "day": 0},
                    },
                    "close": {
                        "day": 0,
                        "hour": 0,
                        "minute": 0,
                        "date": {"year": 0, "month": 0, "day": 0},
                    },
                }
            ],
            "specialDays": [],
            "weekdayDescriptions": [],
            "secondaryHoursType": "",
        },
        "allowsDogs": False,
        "outdoorSeating": False,
        "dineIn": False,
        "name": "",
        "parkingOptions": {
            "freeStreetParking": False,
            "paidParkingLot": True,
            "freeGarageParking": False,
            "freeParkingLot": False,
            "paidGarageParking": True,
            "paidStreetParking": True,
            "valetParking": False,
        },
        "curbsidePickup": False,
        "googleMapsLinks": {
            "reviewsUri": "",
            "writeAReviewUri": "",
            "photosUri": "",
            "directionsUri": "",
            "placeUri": "",
        },
        "servesDinner": False,
        "regularSecondaryOpeningHours": [],
        "editorialSummary": {"text": "", "languageCode": ""},
        "paymentOptions": {
            "acceptsNfc": False,
            "acceptsCreditCards": True,
            "acceptsDebitCards": True,
            "acceptsCashOnly": False,
        },
        "generativeSummary": {
            "descriptionFlagContentUri": "",
            "overviewFlagContentUri": "",
            "description": {"text": "", "languageCode": ""},
            "overview": {"text": "", "languageCode": ""},
            "references": {"places": [], "reviews": []},
        },
        "fuelOptions": {"fuelPrices": []},
        "accessibilityOptions": {
            "wheelchairAccessibleParking": True,
            "wheelchairAccessibleRestroom": True,
            "wheelchairAccessibleSeating": False,
            "wheelchairAccessibleEntrance": True,
        },
        "types": [],
        "subDestinations": [],
        "displayName": {"text": "", "languageCode": ""},
        "addressDescriptor": {
            "landmarks": [
                {
                    "straightLineDistanceMeters": 0,
                    "types": [],
                    "spatialRelationship": "",
                    "displayName": {"text": "", "languageCode": ""},
                    "name": "",
                    "placeId": "",
                    "travelDistanceMeters": 0,
                }
            ],
            "areas": [
                {
                    "name": "",
                    "containment": "",
                    "displayName": {"text": "", "languageCode": ""},
                    "placeId": "",
                }
            ],
        },
        "servesLunch": False,
        "nationalPhoneNumber": "",
    }
}


def save_state(filepath: str) -> None:
    """
    Saves the current state of the in-memory DB to a JSON file.

    Args:
        filepath (str): The file path where the state will be saved.

    Returns:
        None: This function does not return anything.

    Raises:
        OSError: If the file cannot be opened or written to.
        TypeError: If the data in the in-memory DB is not JSON-serializable.
    """
    global DB
    with open(filepath, "w") as f:
        json.dump(DB, f)


def load_state(filepath: str) -> None:
    """
    Loads and replaces the in-memory DB with data from a JSON file.

    Args:
        filepath (str): The file path from which the state will be loaded.

    Returns:
        None: This function does not return anything.

    Raises:
        OSError: If the file cannot be opened or read.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    global DB
    with open(filepath, "r") as f:
        state = json.load(f)
    # Instead of reassigning DB, update it in place:
    DB.clear()
    DB.update(state)

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
