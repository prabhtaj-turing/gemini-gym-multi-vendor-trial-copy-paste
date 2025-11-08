from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
# google_maps/Places/__init__.py
from google_maps.SimulationEngine.db import DB
from google_maps.SimulationEngine.utils import _haversine_distance
from typing import Optional, Dict, Any, List, Union
from google_maps.SimulationEngine.models import GetRequest, Place, AutocompleteRequest, AutocompleteResponse, PlacePrediction, Suggestion, SearchNearbyRequest, SearchTextRequest
from pydantic import ValidationError
from google_maps.Places import Photos

@tool_spec(
    spec={
  'name': 'get_place_autocomplete_predictions',
  'description': 'Returns autocomplete predictions for a given input query.',
  'parameters': {
    'type': 'object',
    'properties': {
      'request_data': {
        'type': 'object',
        'description': 'Input parameters for the autocomplete request.',
        'properties': {
          'input': {
            'type': 'string',
            'description': 'The text entered by the user to generate predictions. (Required)'
          },
          'inputOffset': {
            'type': 'integer',
            'description': 'Offset from the beginning of the input string to interpret for prediction.'
          },
          'languageCode': {
            'type': 'string',
            'description': 'Preferred language for prediction results.'
          },
          'regionCode': {
            'type': 'string',
            'description': 'Unicode region code to influence results.'
          },
          'sessionToken': {
            'type': 'string',
            'description': 'Token used for session-scoped billing and grouping.'
          },
          'includeQueryPredictions': {
            'type': 'boolean',
            'description': 'Whether to include predictions that complete the entire query.'
          },
          'includePureServiceAreaBusinesses': {
            'type': 'boolean',
            'description': 'Whether to include service-area-only businesses.'
          },
          'includedPrimaryTypes': {
            'type': 'array',
            'description': 'List of place types to restrict the predictions to.',
            'items': {
              'type': 'string'
            }
          },
          'includedRegionCodes': {
            'type': 'array',
            'description': 'Restrict results to these CLDR region codes.',
            'items': {
              'type': 'string'
            }
          },
          'origin': {
            'type': 'object',
            'description': 'Geographic location of the user.',
            'properties': {
              'latitude': {
                'type': 'number',
                'description': 'The latitude of the origin.'
              },
              'longitude': {
                'type': 'number',
                'description': 'The longitude of the origin.'
              }
            },
            'required': [
              'latitude',
              'longitude'
            ]
          },
          'locationRestriction': {
            'type': 'object',
            'description': 'Restricts predictions to a circular area.',
            'properties': {
              'circle': {
                'type': 'object',
                'description': 'A dictionary defining the circle radius.',
                'properties': {
                  'radius': {
                    'type': 'number',
                    'description': 'Radius of the restriction in meters.'
                  }
                },
                'required': [
                  'radius'
                ]
              }
            },
            'required': [
              'circle'
            ]
          }
        },
        'required': [
          'input'
        ]
      }
    },
    'required': [
      'request_data'
    ]
  }
}
)
def autocomplete(request_data: Dict[str, Union[str, int, bool, List[str], Dict[str, Union[str, float]]]]) -> Dict[str, Union[str, List[Dict[str, Union[str, int, List[str]]]]]]:
    """
    Returns autocomplete predictions for a given input query.

    Args:
        request_data (Dict[str, Union[str, int, bool, List[str], Dict[str, Union[str, float]]]]): Input parameters for the autocomplete request.
            - input (str): The text entered by the user to generate predictions. (Required)
            - inputOffset (Optional[int]): Offset from the beginning of the input string to interpret for prediction.
            - languageCode (Optional[str]): Preferred language for prediction results.
            - regionCode (Optional[str]): Unicode region code to influence results.
            - sessionToken (Optional[str]): Token used for session-scoped billing and grouping.
            - includeQueryPredictions (Optional[bool]): Whether to include predictions that complete the entire query.
            - includePureServiceAreaBusinesses (Optional[bool]): Whether to include service-area-only businesses.
            - includedPrimaryTypes (Optional[List[str]]): List of place types to restrict the predictions to.
            - includedRegionCodes (Optional[List[str]]): Restrict results to these CLDR region codes.
            - origin (Optional[Dict[str, float]]): Geographic location of the user.
                - latitude (float): The latitude of the origin.
                - longitude (float): The longitude of the origin.
            - locationRestriction (Optional[Dict]): Restricts predictions to a circular area.
                - circle (Dict[str, float]): A dictionary defining the circle radius.
                    - radius (float): Radius of the restriction in meters.

    Returns:
        Dict[str, Union[str, List[Dict[str, Union[str, int, List[str]]]]]]: A dictionary representing autocomplete prediction suggestions.
            - suggestions (List[Dict[str,Union[str, int, bool, List, Dict]]]): List of prediction results.
                - placePrediction (Dict[str,Union[str, int, bool, List, Dict]]): Details for predicted places.
                    - place (str): Textual display name for the predicted place.
                    - id (str): Unique identifier for the place.
                    - distanceMeters (int): Distance from origin to the place in meters.
                    - types (List[str]): Types associated with the place.
                - queryPrediction (Dict[str,Union[str, int, bool, List, Dict]]): Full query predictions.
                    - text (Dict[str,Union[str, int, bool, List, Dict]]):
                        - text (str): Predicted full query text.
                        - matches (List[Dict[str, int]]): Substring match details.
                            - startOffset (int): Start position of matched substring.
                            - endOffset (int): End position of matched substring.
                            
    Raises:
        ValueError: If the request_data is invalid.
    """
    try:
        params = AutocompleteRequest(**request_data)
    except ValidationError as e:
        # Provide a cleaner error message instead of the full Pydantic dump.
        error = e.errors()[0]
        raise ValueError(f"Invalid request data: {error['msg']}")

    suggestions = []
    query = params.input.lower()

    for place_id, place_data in DB.items():
        if query not in place_data.get("name", "").lower():
            continue

        # Filter by languageCode.
        if params.languageCode:
            primary_lang = place_data.get("primaryTypeDisplayName", {}).get(
                "languageCode"
            )
            postal_lang = place_data.get("postalAddress", {}).get("languageCode")
            if (
                primary_lang != params.languageCode
                and postal_lang != params.languageCode
            ):
                continue

        # Filter by regionCode.
        place_region = place_data.get("postalAddress", {}).get("regionCode")
        if params.regionCode and place_region != params.regionCode:
            continue

        if params.includedRegionCodes and place_region not in params.includedRegionCodes:
            continue

        # Filter by includedPrimaryTypes.
        if params.includedPrimaryTypes and place_data.get(
            "primaryType"
        ) not in params.includedPrimaryTypes:
            continue

        # Filter by locationRestriction.
        if params.locationRestriction and params.locationRestriction.circle:
            circle = params.locationRestriction.circle
            if circle.center and circle.radius is not None:
                place_location = place_data.get("location")
                if not place_location:
                    continue

                distance = _haversine_distance(
                    circle.center.latitude,
                    circle.center.longitude,
                    place_location["latitude"],
                    place_location["longitude"],
                )
                if distance > circle.radius:
                    continue

        # Filter by includePureServiceAreaBusinesses.
        if (
            params.includePureServiceAreaBusinesses is False
            and place_data.get("pureServiceAreaBusiness")
        ):
            continue

        distance = None
        if params.origin and place_data.get("location"):
            distance = int(
                _haversine_distance(
                    params.origin.latitude,
                    params.origin.longitude,
                    place_data["location"]["latitude"],
                    place_data["location"]["longitude"],
                )
            )

        prediction = PlacePrediction(
            place=place_data["name"],
            id=place_id,
            distanceMeters=distance,
            types=place_data.get("types", []),
        )
        suggestions.append(Suggestion(placePrediction=prediction))

    return AutocompleteResponse(suggestions=suggestions).model_dump()

@tool_spec(
    spec={
        'name': 'get_place_details',
        'description': 'Retrieves detailed information about a place using its resource name.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': "Required. The resource name of the place in the format 'places/{place_id}'."
                },
                'languageCode': {
                    'type': 'string',
                    'description': 'Preferred language for localized content if available.'
                },
                'sessionToken': {
                    'type': 'string',
                    'description': 'Autocomplete session token for billing. Must be base64-safe and <= 36 ASCII chars.'
                },
                'regionCode': {
                    'type': 'string',
                    'description': 'Unicode CLDR region code to influence localized place details.'
                }
            },
            'required': [
                'name'
            ]
        }
    }
)

def get(
    name: str,
    languageCode: Optional[str] = None,
    sessionToken: Optional[str] = None,
    regionCode: Optional[str] = None,
) -> Dict[str, Union[str, int, float, bool, List, Dict]]: 
    """
    Retrieves detailed information about a place using its resource name.

    Args:
        name (str): Required. The resource name of the place in the format "places/{place_id}".
        languageCode (Optional[str]): Preferred language for localized content if available.
        sessionToken (Optional[str]): Autocomplete session token for billing. Must be base64-safe and <= 36 ASCII chars.
        regionCode (Optional[str]): Unicode CLDR region code to influence localized place details.

    Returns:
        Dict[str, Union[str, int, float, bool, List, Dict]]: A dictionary containing all available place details.

            - id (str): Unique place identifier.
            - name (str): Name of the place.
            - rating (float): Average user rating.
            - userRatingCount (int): Number of user ratings.
            - formattedAddress (str): Full formatted address.
            - shortFormattedAddress (str): Abbreviated address format.
            - adrFormatAddress (str): HTML-structured address.
            - primaryType (str): Main classification type.
            - types (List[str]): All associated place types.
            - pureServiceAreaBusiness (bool): Indicates a service-only business.
            - businessStatus (str): Operational status (e.g., OPERATIONAL).
            - priceLevel (str): Relative cost category.
            - utcOffsetMinutes (int): Time zone offset from UTC.
            - internationalPhoneNumber (str): International phone format.
            - nationalPhoneNumber (str): Localized phone number.
            - googleMapsUri (str): Link to place on Google Maps.
            - websiteUri (str): Place's website URL.
            - iconMaskBaseUri (str): Base URI for icon imagery.
            - iconBackgroundColor (str): Icon background color code.

            - allowsDogs (bool): Whether pets are allowed.
            - goodForChildren (bool): Child-friendly status.
            - goodForGroups (bool): Suitable for groups.
            - goodForWatchingSports (bool): Suitable for watching sports.
            - dineIn (bool): Dine-in option available.
            - delivery (bool): Delivery service available.
            - takeout (bool): Takeout service available.
            - curbsidePickup (bool): Curbside pickup available.
            - reservable (bool): Reservations supported.
            - servesBreakfast (bool): Serves breakfast.
            - servesLunch (bool): Serves lunch.
            - servesBrunch (bool): Serves brunch.
            - servesDinner (bool): Serves dinner.
            - servesCoffee (bool): Coffee served.
            - servesDessert (bool): Serves dessert.
            - servesBeer (bool): Serves beer.
            - servesWine (bool): Serves wine.
            - servesCocktails (bool): Serves cocktails.
            - servesVegetarianFood (bool): Vegetarian options available.
            - menuForChildren (bool): Children's menu offered.
            - liveMusic (bool): Live music available.
            - restroom (bool): Restroom facilities available.

            - paymentOptions (Dict[str, bool]): Accepted payment methods.
                - acceptsCashOnly (bool): Accepts only cash.
                - acceptsCreditCards (bool): Accepts credit cards.
                - acceptsDebitCards (bool): Accepts debit cards.
                - acceptsNfc (bool): Accepts NFC payments.

            - accessibilityOptions (Dict[str, bool]): Accessibility features.
                - wheelchairAccessibleEntrance (bool)
                - wheelchairAccessibleRestroom (bool)
                - wheelchairAccessibleParking (bool)
                - wheelchairAccessibleSeating (bool)

            - primaryTypeDisplayName (Dict[str, str]): Localized type name.
                - text (str): Display label.
                - languageCode (str): Language of label.

            - location (Dict[str, float]): Geographic coordinates.
                - latitude (float)
                - longitude (float)

            - reviewSummary (Dict[str, str]):
                - flagContentUri (str): URI to flag review summary content.

            - currentOpeningHours (Dict[str, Union[bool, str, List[Union[str, Dict[str, Union[int, bool]]]]]]): Operating schedule details.
                - openNow (bool): Whether the place is open.
                - secondaryHoursType (str): Type of alternate hours.
                - nextOpenTime (str): ISO time for next open.
                - nextCloseTime (str): ISO time for next close.
                - weekdayDescriptions (List[str]): Human-readable daily hours.
                - periods (List[Dict[str, Dict[str, Union[int, bool]]]]): Time blocks for each day.
                    - open (Dict[str, Union[int, bool]]):
                        - day (int)
                        - hour (int)
                        - minute (int)
                        - truncated (bool)
                - specialDays (List[Dict[str, Dict[str, int]]]): Special openings/closures.
                    - date (Dict[str, int]):
                        - day (int)
                        - month (int)
                        - year (int)

            - attributions (List[Dict[str, str]]): Data providers.
                - provider (str)
                - providerUri (str)

            - generativeSummary (Dict[str, str]):
                - overviewFlagContentUri (str): Flag URI for summary.

            - neighborhoodSummary (Dict[str, str]):
                - flagContentUri (str): Flag URI for neighborhood section.

            - postalAddress (Dict[str, Union[str, int, List[str]]]): Complete structured address.
                - addressLines (List[str])
                - recipients (List[str])
                - sublocality (str)
                - postalCode (str)
                - organization (str)
                - revision (int)
                - locality (str)
                - administrativeArea (str)
                - languageCode (str)
                - regionCode (str)
                - sortingCode (str)

            - plusCode (Dict[str, str]): Open location code.
                - globalCode (str)
                - compoundCode (str)

            - googleMapsLinks (Dict[str, str]): Google Maps links.
                - photosUri (str)
                - writeAReviewUri (str)
                - placeUri (str)
                - reviewsUri (str)
                - directionsUri (str)

            - subDestinations (List[Dict[str, str]]): Sub-places within the entity.
                - name (str)
                - id (str)

            - containingPlaces (List[Dict[str, str]]): Parent or container places.
                - name (str)
                - id (str)

            - photos (List[Dict[str, Union[str, int]]]): Associated photos.
                - name (str)
                - widthPx (int)
                - heightPx (int)
                - googleMapsUri (str)
                - flagContentUri (str)

            - addressComponents (List[Dict[str, Union[str, List[str]]]]): Address components.
                - longText (str)
                - shortText (str)
                - languageCode (str)
                - types (List[str])

            - addressDescriptor (Dict[str, List[Dict[str, Union[str, float, List[str]]]]]): Location context descriptors.
                - areas (List[Dict[str, str]]): Contained area information.
                    - name (str)
                    - placeId (str)
                    - containment (str)
                - landmarks (List[Dict[str, Union[str, float, List[str]]]]): Nearby landmarks.
                    - placeId (str)
                    - name (str)
                    - spatialRelationship (str)
                    - straightLineDistanceMeters (float)
                    - travelDistanceMeters (float)
                    - types (List[str])

            - reviews (List[Dict[str, Union[str, float, Dict[str, str]]]]): Reviews by users.
                - name (str)
                - googleMapsUri (str)
                - flagContentUri (str)
                - rating (float)
                - relativePublishTimeDescription (str)
                - publishTime (str)
                - authorAttribution (Dict[str, str]):
                    - displayName (str)
                    - photoUri (str)
                    - uri (str)

            - fuelOptions (Dict[str, List[Dict[str, str]]]): Fuel pricing details.
                - fuelPrices (List[Dict[str, str]]):
                    - type (str)
                    - updateTime (str)

            - priceRange (Dict[str, Dict[str, Union[int, str]]]): Price tier estimates.
                - endPrice (Dict[str, Union[int, str]]):
                    - nanos (int)
                    - currencyCode (str)
                    - units (str)

            - evChargeOptions (Dict[str, Union[int, List[Dict[str, Union[str, int, float]]]]]): EV charger availability.
                - connectorCount (int)
                - connectorAggregation (List[Dict[str, Union[str, int, float]]]):
                    - availabilityLastUpdateTime (str)
                    - availableCount (int)
                    - outOfServiceCount (int)
                    - maxChargeRateKw (float)
                    - type (str)
                    - count (int)

            - evChargeAmenitySummary (Dict[str, Union[str, Dict[str, List[str]]]]):
                - flagContentUri (str)
                - store (Dict[str, List[str]]):
                    - referencedPlaces (List[str])

            - parkingOptions (Dict[str, bool]): Parking availability.
                - paidGarageParking (bool)
                - valetParking (bool)
                - paidParkingLot (bool)
                - freeStreetParking (bool)
                - freeGarageParking (bool)
                - freeParkingLot (bool)
                - paidStreetParking (bool)

            - timeZone (Dict[str, str]): Time zone data.
                - id (str)
                - version (str)


    Raises:
        TypeError: If name, or if provided, languageCode, sessionToken, or regionCode are not a string.
        ValueError: 
         - If languageCode is not a valid ISO 639-1 language code or is empty.
         - If sessionToken is not base64-safe or is empty.
         - If regionCode is not a valid CLDR region code or is empty.
         - If name is not in the correct format (places/{place_id}) or is empty
         - If place is not found in the DB or languageCode or regionCode do not match the place.
        
    """
    try:
        params = GetRequest(
            name=name,
            languageCode=languageCode,
            sessionToken=sessionToken,
            regionCode=regionCode,
        )
    except ValidationError as e:
        error = e.errors()[0]
        msg = error['msg']
        loc = error['loc'][0] if error['loc'] else 'request'
        
        # Pydantic's "string_type" error for a field means it's a TypeError
        if 'string' in error['type']:
            raise TypeError(f"{loc} must be a string")
        
        # For other validation errors, raise ValueError
        msg = msg.removeprefix("Value error, ")
        raise ValueError(msg)

    # Extract place_id from name
    place_id = params.name.split("/")[1]
    
    # Look up the place in the global DB
    if place_id not in DB:
        raise ValueError("place not found in DB")

    place_data = DB[place_id].copy()
    
    # Validate languageCode if provided
    if params.languageCode:
        if "primaryTypeDisplayName" in place_data:
                if "languageCode" in place_data["primaryTypeDisplayName"]:
                    if place_data["primaryTypeDisplayName"]["languageCode"] != params.languageCode:
                        raise ValueError("languageCode does not match the place")
            
    
    # Validate sessionToken if provided
    if params.sessionToken:
        # Add session token tracking if provided (for billing purposes)
        place_data["_sessionToken"] = params.sessionToken
    
    # Validate regionCode if provided
    if params.regionCode:
        if "plusCode" in place_data:
                if "compoundCode" in place_data["plusCode"]:
                    if params.regionCode not in place_data["plusCode"]["compoundCode"] :
                        raise ValueError("regionCode does not match the place")
    
    return place_data

@tool_spec(
    spec={
        'name': 'search_nearby_places',
        'description': """ Searches for places in the static database based on provided filters.
        
        Filters can include primary types, secondary types (included or excluded),
        a specific language code for the display name, and a geographical
        location restriction with a center point and a radius. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'request': {
                    'type': 'object',
                    'description': """ A dictionary representing the
                    GoogleMapsPlacesV1SearchNearbyRequest. It contains the following keys: """,
                    'properties': {
                        'locationRestriction': {
                            'type': 'object',
                            'description': 'Required. The region to search.',
                            'properties': {
                                'circle': {
                                    'type': 'object',
                                    'description': 'A circle defined by a center point and radius.',
                                    'properties': {
                                        'center': {
                                            'type': 'object',
                                            'description': """ Required. The center latitude and
                                                       longitude. The range of latitude must be within [-90.0, 90.0],
                                                      and longitude within [-180.0, 180.0]. """,
                                            'properties': {
                                                'latitude': {
                                                    'type': 'number',
                                                    'description': 'The latitude of the center point.'
                                                },
                                                'longitude': {
                                                    'type': 'number',
                                                    'description': 'The longitude of the center point.'
                                                }
                                            },
                                            'required': [
                                                'latitude',
                                                'longitude'
                                            ]
                                        },
                                        'radius': {
                                            'type': 'number',
                                            'description': """ Required. The radius in meters. Must be
                                                       within [0.0, 50000.0]. """
                                        }
                                    },
                                    'required': [
                                        'center',
                                        'radius'
                                    ]
                                }
                            },
                            'required': [
                                'circle'
                            ]
                        },
                        'languageCode': {
                            'type': 'string',
                            'description': """ The preferred language for place details.
                               If unspecified, a preference for English is used. See the full list
                              of supported languages: https://developers.google.com/maps/faq#languagesupport. """
                        },
                        'regionCode': {
                            'type': 'string',
                            'description': """ The Unicode country/region code (CLDR)
                               of the request's origin. This can affect results based on applicable law.
                              See https://www.unicode.org/cldr/charts/latest/supplemental/territory_language_information.html. """
                        },
                        'includedTypes': {
                            'type': 'array',
                            'description': """ Included Place types (e.g., "restaurant").
                               Up to 50 types from Table A may be specified.
                              See https://developers.google.com/maps/documentation/places/web-service/place-types. """,
                            'items': {
                                'type': 'string'
                            }
                        },
                        'excludedTypes': {
                            'type': 'array',
                            'description': """ Excluded Place types. Up to 50 types
                               from Table A may be specified. """,
                            'items': {
                                'type': 'string'
                            }
                        },
                        'includedPrimaryTypes': {
                            'type': 'array',
                            'description': """ Included primary Place types.
                               A place can only have a single primary type. Up to 50 types from
                              Table A may be specified. """,
                            'items': {
                                'type': 'string'
                            }
                        },
                        'excludedPrimaryTypes': {
                            'type': 'array',
                            'description': """ Excluded primary Place types.
                               Up to 50 types from Table A may be specified. """,
                            'items': {
                                'type': 'string'
                            }
                        },
                        'maxResultCount': {
                            'type': 'integer',
                            'description': """ Maximum number of results to return.
                               Must be between 1 and 20. Defaults to 20. """
                        },
                        'rankPreference': {
                            'type': 'string',
                            'description': """ Specifies the ranking of the results.
                               Valid values: "POPULARITY" (default, ranks by popularity), "DISTANCE" (ranks by distance), "RANK_PREFERENCE_UNSPECIFIED" (defaults to POPULARITY). """
                        },
                        'routingParameters': {
                            'type': 'object',
                            'description': """ Parameters to configure
                               routing calculations to the search results. """,
                            'properties': {
                                'origin': {
                                    'type': 'object',
                                    'description': 'Overrides the default routing origin.',
                                    'properties': {
                                        'latitude': {
                                            'type': 'number',
                                            'description': 'Latitude in degrees.'
                                        },
                                        'longitude': {
                                            'type': 'number',
                                            'description': 'Longitude in degrees.'
                                        }
                                    },
                                    'required': [
                                        'latitude',
                                        'longitude'
                                    ]
                                },
                                'travelMode': {
                                    'type': 'string',
                                    'description': """ Specifies the mode of travel.
                                           One of: "DRIVE", "BICYCLE", "WALK", "TWO_WHEELER". Defaults to "DRIVE". """
                                },
                                'routeModifiers': {
                                    'type': 'object',
                                    'description': 'Conditions to satisfy for the route.',
                                    'properties': {
                                        'avoidTolls': {
                                            'type': 'boolean',
                                            'description': 'Avoid toll roads.'
                                        },
                                        'avoidHighways': {
                                            'type': 'boolean',
                                            'description': 'Avoid highways.'
                                        },
                                        'avoidFerries': {
                                            'type': 'boolean',
                                            'description': 'Avoid ferries.'
                                        },
                                        'avoidIndoor': {
                                            'type': 'boolean',
                                            'description': 'Avoid indoor navigation (for WALKING mode).'
                                        }
                                    },
                                    'required': []
                                },
                                'routingPreference': {
                                    'type': 'string',
                                    'description': """ Specifies how to compute routing summaries.
                                           One of: "TRAFFIC_UNAWARE", "TRAFFIC_AWARE", "TRAFFIC_AWARE_OPTIMAL".
                                          Defaults to "TRAFFIC_UNAWARE". """
                                }
                            },
                            'required': []
                        }
                    },
                    'required': [
                        'locationRestriction'
                    ]
                }
            },
            'required': [
                'request'
            ]
        }
    }
)
def searchNearby(request: Dict[str, Union[str, int, bool, List[str], Dict[str, Union[str, int, float, bool, List[str], Dict[str, Union[str, int, float]]]]]]) -> Dict[str, List[Dict[str, Union[str, int, float, bool, List[str], Dict[str, Union[str, int, float, bool, List[str]]]]]]]:
    """Searches for places in the static database based on provided filters.

    Filters can include primary types, secondary types (included or excluded),
    a specific language code for the display name, and a geographical
    location restriction with a center point and a radius.

    Args:
        request (Dict[str, Union[str, int, bool, List[str], Dict[str, Union[str, int, float, bool, List[str], Dict[str, Union[str, int, float]]]]]]): A dictionary representing the
            GoogleMapsPlacesV1SearchNearbyRequest. It contains the following keys:
            - locationRestriction (Dict[str, Union[str, int, float, bool, List[str], Dict[str, Union[str, int, float]]]]): Required. The region to search.
                - circle (Dict[str, Union[str, int, float]]): A circle defined by a center point and radius.
                    - center (Dict[str, float]): Required. The center latitude and
                      longitude. The range of latitude must be within [-90.0, 90.0],
                      and longitude within [-180.0, 180.0].
                        - latitude (float): The latitude of the center point.
                        - longitude (float): The longitude of the center point.
                    - radius (float): Required. The radius in meters. Must be
                      within [0.0, 50000.0].
            - languageCode (Optional[str]): The preferred language for place details.
              If unspecified, a preference for English is used. See the full list
              of supported languages: https://developers.google.com/maps/faq#languagesupport.
            - regionCode (Optional[str]): The Unicode country/region code (CLDR)
              of the request's origin. This can affect results based on applicable law.
              See https://www.unicode.org/cldr/charts/latest/supplemental/territory_language_information.html.
            - includedTypes (Optional[List[str]]): Included Place types (e.g., "restaurant").
              Up to 50 types from Table A may be specified.
              See https://developers.google.com/maps/documentation/places/web-service/place-types.
            - excludedTypes (Optional[List[str]]): Excluded Place types. Up to 50 types
              from Table A may be specified.
            - includedPrimaryTypes (Optional[List[str]]): Included primary Place types.
              A place can only have a single primary type. Up to 50 types from
              Table A may be specified.
            - excludedPrimaryTypes (Optional[List[str]]): Excluded primary Place types.
              Up to 50 types from Table A may be specified.
            - maxResultCount (Optional[int]): Maximum number of results to return.
              Must be between 1 and 20. Defaults to 20.
            - rankPreference (Optional[str]): Specifies the ranking of the results.
              Valid values: "POPULARITY" (default, ranks by popularity), "DISTANCE" (ranks by distance), "RANK_PREFERENCE_UNSPECIFIED" (defaults to POPULARITY).
            - routingParameters (Optional[Dict[str, Union[str, int, float, bool, List[str], Dict[str, Union[str, int, float, bool]]]]]): Parameters to configure
              routing calculations to the search results.
                - origin (Optional[Dict[str, float]]): Overrides the default routing origin.
                    - latitude (float): Latitude in degrees.
                    - longitude (float): Longitude in degrees.
                - travelMode (Optional[str]): Specifies the mode of travel.
                  One of: "DRIVE", "BICYCLE", "WALK", "TWO_WHEELER". Defaults to "DRIVE".
                - routeModifiers (Optional[Dict[str, bool]]): Conditions to satisfy for the route.
                    - avoidTolls (Optional[bool]): Avoid toll roads.
                    - avoidHighways (Optional[bool]): Avoid highways.
                    - avoidFerries (Optional[bool]): Avoid ferries.
                    - avoidIndoor (Optional[bool]): Avoid indoor navigation (for WALKING mode).
                - routingPreference (Optional[str]): Specifies how to compute routing summaries.
                  One of: "TRAFFIC_UNAWARE", "TRAFFIC_AWARE", "TRAFFIC_AWARE_OPTIMAL".
                  Defaults to "TRAFFIC_UNAWARE".

    Returns:
        Dict[str, List[Dict[str, Union[str, int, float, bool, List[str], Dict[str, Union[str, int, float, bool, List[str]]]]]]]: A dictionary containing matched places and associated routing summaries.
            - places (List[Dict[str, Union[str, int, float, bool, List[str], Dict[str, Union[str, int, float, bool, List[str]]]]]]): List of place results.
                - id (str): Unique place identifier.
                - name (str): Display name of the place.
                - rating (float): Average user rating.
                - userRatingCount (int): Total number of ratings.
                - formattedAddress (str): Full readable address.
                - shortFormattedAddress (str): Abbreviated address.
                - adrFormatAddress (str): Address in HTML format.
                - primaryType (str): Main type category.
                - types (List[str]): All associated place types.
                - pureServiceAreaBusiness (bool): True if no physical location.
                - businessStatus (str): Operational status.
                - priceLevel (str): Price level from free to very expensive.
                - utcOffsetMinutes (int): Time zone offset in minutes.
                - internationalPhoneNumber (str): Phone number with country code.
                - nationalPhoneNumber (str): Regional phone number format.
                - googleMapsUri (str): Link to the place on Google Maps.
                - websiteUri (str): Website URL of the place.
                - iconMaskBaseUri (str): Base URI for place icon.
                - iconBackgroundColor (str): Icon background hex color.
                - allowsDogs (bool): True if dogs are allowed.
                - goodForChildren (bool): True if child-friendly.
                - goodForGroups (bool): Suitable for group visits.
                - goodForWatchingSports (bool): Good for watching sports.
                - dineIn (bool): Dine-in available.
                - delivery (bool): Delivery service offered.
                - takeout (bool): Takeout available.
                - curbsidePickup (bool): Supports curbside pickup.
                - reservable (bool): Reservations accepted.
                - servesBreakfast (bool): Serves breakfast.
                - servesLunch (bool): Serves lunch.
                - servesBrunch (bool): Serves brunch.
                - servesDinner (bool): Serves dinner.
                - servesCoffee (bool): Coffee available.
                - servesDessert (bool): Dessert available.
                - servesBeer (bool): Serves beer.
                - servesWine (bool): Serves wine.
                - servesCocktails (bool): Serves cocktails.
                - servesVegetarianFood (bool): Has vegetarian options.
                - menuForChildren (bool): Has children's menu.
                - liveMusic (bool): Offers live music.
                - paymentOptions (Dict[str, bool]): Accepted payment methods.
                    - acceptsCashOnly (bool): Accepts only cash.
                    - acceptsCreditCards (bool): Accepts credit cards.
                    - acceptsDebitCards (bool): Accepts debit cards.
                    - acceptsNfc (bool): Accepts NFC payments.
                - accessibilityOptions (Dict[str, bool]): Accessibility support.
                    - wheelchairAccessibleEntrance (bool)
                    - wheelchairAccessibleRestroom (bool)
                    - wheelchairAccessibleParking (bool)
                    - wheelchairAccessibleSeating (bool)
                - primaryTypeDisplayName (Dict[str, str]): Localized display info.
                    - text (str): Display text.
                    - languageCode (str): Language code of display name.
                - location (Dict[str, float]): Geographic coordinates.
                    - latitude (float)
                    - longitude (float)
                - reviewSummary (Dict[str, str]):
                    - flagContentUri (str): URI to report summary issues.
                - currentOpeningHours (Dict[str, Union[str, int, bool, List[str], Dict[str, Union[str, int, bool]]]]): Opening hours data.
                    - openNow (bool): Currently open or not.
                    - secondaryHoursType (str): Secondary hours category.
                    - nextOpenTime (str): ISO timestamp of next opening.
                    - nextCloseTime (str): ISO timestamp of next closing.
                    - weekdayDescriptions (List[str]): Human-friendly weekday hours.
                    - periods (List[Dict[str, Union[str, int, bool, Dict[str, Union[str, int, bool]]]]]): Opening/closing time blocks.
                        - open (Dict[str, Union[str, int, bool]]):
                            - day (int)
                            - hour (int)
                            - minute (int)
                            - truncated (bool): If truncated for display.
                    - specialDays (List[Dict[str, Union[str, int, Dict[str, int]]]]): Special openings.
                        - date (Dict[str, int]):
                            - day (int)
                            - month (int)
                            - year (int)
                - attributions (List[Dict[str, str]]): Content provider credits.
                    - provider (str): Name of provider.
                    - providerUri (str): Link to the provider.
                - generativeSummary (Dict[str, str]):
                    - overviewFlagContentUri (str): Report AI summary content.
                - neighborhoodSummary (Dict[str, str]):
                    - flagContentUri (str): Report neighborhood summary issues.
                - postalAddress (Dict[str, Union[str, int, List[str]]]): Structured address fields.
                    - addressLines (List[str])
                    - recipients (List[str])
                    - sublocality (str)
                    - postalCode (str)
                    - organization (str)
                    - revision (int)
                    - locality (str)
                    - administrativeArea (str)
                    - languageCode (str)
                    - regionCode (str)
                    - sortingCode (str)
                - plusCode (Dict[str, str]): Global location code.
                    - globalCode (str)
                    - compoundCode (str)
                - googleMapsLinks (Dict[str, str]): Useful Google Maps URIs.
                    - photosUri (str)
                    - writeAReviewUri (str)
                    - placeUri (str)
                    - reviewsUri (str)
                    - directionsUri (str)
                - subDestinations (List[Dict[str, str]]): Sub-entities inside place.
                    - name (str)
                    - id (str)
                - containingPlaces (List[Dict[str, str]]): Parent place data.
                    - name (str)
                    - id (str)
                - photos (List[Dict[str, Union[str, int]]]): Associated photos.
                    - name (str)
                    - widthPx (int)
                    - heightPx (int)
                    - googleMapsUri (str)
                    - flagContentUri (str)
                - addressComponents (List[Dict[str, Union[str, List[str]]]]): Address parts.
                    - longText (str)
                    - shortText (str)
                    - languageCode (str)
                    - types (List[str])
                - addressDescriptor (Dict[str, List[Dict[str, Union[str, float, List[str]]]]]): Additional location details.
                    - areas (List[Dict[str, str]]): Contextual areas.
                        - name (str)
                        - placeId (str)
                        - containment (str)
                    - landmarks (List[Dict[str, Union[str, float, List[str]]]]): Notable nearby locations.
                        - placeId (str)
                        - name (str)
                        - spatialRelationship (str)
                        - straightLineDistanceMeters (float)
                        - travelDistanceMeters (float)
                        - types (List[str])
                - reviews (List[Dict[str, Union[str, float, Dict[str, str]]]]): User-generated reviews.
                    - name (str)
                    - googleMapsUri (str)
                    - flagContentUri (str)
                    - rating (float)
                    - relativePublishTimeDescription (str)
                    - publishTime (str)
                    - authorAttribution (Dict[str, str]):
                        - displayName (str)
                        - photoUri (str)
                        - uri (str)
                - fuelOptions (Dict[str, List[Dict[str, str]]]): Nearby fuel pricing data.
                    - fuelPrices (List[Dict[str, str]]):
                        - type (str)
                        - updateTime (str)
                - priceRange (Dict[str, Dict[str, Union[str, int]]]): Pricing information.
                    - endPrice (Dict[str, Union[int, str]]):
                        - nanos (int)
                        - currencyCode (str)
                        - units (str)
                - evChargeOptions (Dict[str, Union[int, List[Dict[str, Union[str, int, float]]]]]): EV charger details.
                    - connectorCount (int)
                    - connectorAggregation (List[Dict[str, Union[str, int, float]]]):
                        - availabilityLastUpdateTime (str)
                        - availableCount (int)
                        - maxChargeRateKw (float)
                        - outOfServiceCount (int)
                        - type (str)
                        - count (int)
                - evChargeAmenitySummary (Dict[str, Union[str, Dict[str, List[str]]]]): EV summaries.
                    - flagContentUri (str)
                    - store (Dict[str, List[str]]):
                        - referencedPlaces (List[str])
                - parkingOptions (Dict[str, bool]): Parking availability.
                    - paidGarageParking (bool)
                    - valetParking (bool)
                    - paidParkingLot (bool)
                    - freeStreetParking (bool)
                    - freeGarageParking (bool)
                    - freeParkingLot (bool)
                    - paidStreetParking (bool)
                - timeZone (Dict[str, str]): Time zone metadata.
                    - id (str)
                    - version (str)
            - routingSummaries (List[Dict[str, Union[str, List[Dict[str, Union[str, int]]]]]]): Optional travel summaries.
                - directionsUri (str): Link to the directions.
                - legs (List[Dict[str, Union[str, int]]]):  Segmented route steps.
                    - duration (str): Duration of travel.
                    - distanceMeters (int): Travel distance in meters.

    Raises:
        ValidationError: If the request parameters fail validation (e.g., invalid maxResultCount,
            invalid latitude/longitude ranges, invalid enum values).
    
    Limitations:
        - Only supports circle-based location restrictions (rectangle not implemented)
        - regionCode parameter is accepted but not used in filtering
        - rankPreference parameter is accepted but not used in result ordering
        - routingParameters are accepted but routing summaries are not computed
        - Maximum of 20 results can be returned (maxResultCount <= 20)
    """
    # Validate request using Pydantic model
    validated_request = SearchNearbyRequest(**request)
    # Convert back to dictionary for backward compatibility
    request = validated_request.model_dump()
    
    filtered_places = []
    routing_summaries = []
    
    # Retrieve maxResultCount, default to 20 if not provided.
    max_result_count = request.get("maxResultCount", 20)
    included_primary_types = request.get("includedPrimaryTypes", [])
    excluded_primary_types = request.get("excludedPrimaryTypes", [])
    included_types = request.get("includedTypes", [])
    excluded_types = request.get("excludedTypes", [])
    
    # Placeholder for language code filtering if your DB supports it
    # This example assumes all data is in a single language.
    language_code = request.get("languageCode")
    
    # This example does not implement rankPreference, regionCode, or routingParameters
    # but acknowledges them for signature completeness.
    
    filtered_places = []
    for place_id, place_data in DB.items():
        # Apply filters
        if included_primary_types and place_data.get("primaryType") not in included_primary_types:
            continue
        if excluded_primary_types and place_data.get("primaryType") in excluded_primary_types:
            continue
        if included_types and not any(t in place_data.get("types", []) for t in included_types):
            continue
        if excluded_types and any(t in place_data.get("types", []) for t in excluded_types):
            continue
        
        # Location restriction
        location_restriction = request.get("locationRestriction", {})
        circle = location_restriction.get("circle")
        if circle:
            place_loc = place_data.get("location")
            if place_loc:
                distance = _haversine_distance(
                    circle["center"]["latitude"],
                    circle["center"]["longitude"],
                    place_loc["latitude"],
                    place_loc["longitude"],
                )
                if distance > circle["radius"]:
                    continue
        
        # Language code filter (basic example)
        if language_code:
            # This is a simplistic check. A real implementation would be more robust.
            if place_data.get("primaryTypeDisplayName", {}).get("languageCode") != language_code:
                continue
        
        # place = Place(
        #     id=place_data.get("id"),
        #     name=place_data.get("name"),
        #     address=place_data.get("formattedAddress"),
        #     location=place_data.get("location", {}),
        #     phone_number=place_data.get("internationalPhoneNumber"),
        #     website=place_data.get("websiteUri"),
        # )
        filtered_places.append(place_data)
    
    return {"places": filtered_places[:max_result_count]}

@tool_spec(
    spec={
        'name': 'search_places_by_text',
        'description': """ Performs a text-based search for places using optional filters.
        
        This function processes a search request structured according to the
        GoogleMapsPlacesV1SearchTextRequest schema. Supported filters include:
        'strictTypeFiltering', 'priceLevels', 'locationBias', 'openNow',
        'minRating', 'includePureServiceAreaBusinesses', 'locationRestriction',
        'languageCode', 'pageSize', 'regionCode', 'textQuery', and others. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'request': {
                    'type': 'object',
                    'description': 'Dictionary representing search request object containing the text query and optional filtering parameters.:',
                    'properties': {
                        'textQuery': {
                            'type': 'string',
                            'description': 'Required. The text query for the textual search.'
                        },
                        'languageCode': {
                            'type': 'string',
                            'description': """ The preferred language for place details.
                               See https://developers.google.com/maps/faq#languagesupport for supported languages. """
                        },
                        'regionCode': {
                            'type': 'string',
                            'description': """ The Unicode country/region code (CLDR)
                               of the request's origin. This can affect results based on applicable law.
                              See https://www.unicode.org/cldr/charts/latest/supplemental/territory_language_information.html. """
                        },
                        'rankPreference': {
                            'type': 'string',
                            'description': """ Specifies how results are ranked.
                               Valid values: "DISTANCE" (ranks by distance), "RELEVANCE" (default, ranks by relevance), "RANK_PREFERENCE_UNSPECIFIED" (defaults to RELEVANCE). """
                        },
                        'includedType': {
                            'type': 'string',
                            'description': """ The requested place type. Only one type is supported.
                               For a full list of types, see https://developers.google.com/maps/documentation/places/web-service/place-types. """
                        },
                        'openNow': {
                            'type': 'boolean',
                            'description': 'If true, restricts the search to places that are currently open. Defaults to false.'
                        },
                        'minRating': {
                            'type': 'number',
                            'description': """ Filters out results with a rating strictly less than this limit.
                               Valid values are between 0.0 and 5.0, in 0.5 increments. """
                        },
                        'maxResultCount': {
                            'type': 'integer',
                            'description': "Deprecated. Use 'pageSize' instead. Maximum number of results to return (up to 20)."
                        },
                        'pageSize': {
                            'type': 'integer',
                            'description': 'The maximum number of results per page. Defaults to 20. The maximum value is 20.'
                        },
                        'pageToken': {
                            'type': 'string',
                            'description': 'A token from a previous search to retrieve the next page of results.'
                        },
                        'priceLevels': {
                            'type': 'array',
                            'description': """ Restricts the search to places with the specified price levels.
                               Allowed values include: "PRICE_LEVEL_FREE", "PRICE_LEVEL_INEXPENSIVE",
                              "PRICE_LEVEL_MODERATE", "PRICE_LEVEL_EXPENSIVE", "PRICE_LEVEL_VERY_EXPENSIVE". """,
                            'items': {
                                'type': 'string'
                            }
                        },
                        'strictTypeFiltering': {
                            'type': 'boolean',
                            'description': "If true, only results of the specified 'includedType' will be returned. Defaults to false."
                        },
                        'locationBias': {
                            'type': 'object',
                            'description': 'Biases the search results to a specific region. Cannot be set with \'locationRestriction\'. Can be a \'rectangle\' or \'circle\'.',
                            'properties': {
                                'rectangle': {
                                    'type': 'object',
                                    'description': 'A rectangle defined by northeast and southwest corners.',
                                    'properties': {
                                        'low': {
                                            'type': 'object',
                                            'description': 'The southwest point.',
                                            'properties': {
                                                'latitude': {
                                                    'type': 'number',
                                                    'description': 'The latitude of the southwest point.'
                                                },
                                                'longitude': {
                                                    'type': 'number',
                                                    'description': 'The longitude of the southwest point.'
                                                }
                                            },
                                            'required': [
                                                'latitude',
                                                'longitude'
                                            ]
                                        },
                                        'high': {
                                            'type': 'object',
                                            'description': 'The northeast point.',
                                            'properties': {
                                                'latitude': {
                                                    'type': 'number',
                                                    'description': 'The latitude of the northeast point.'
                                                },
                                                'longitude': {
                                                    'type': 'number',
                                                    'description': 'The longitude of the northeast point.'
                                                }
                                            },
                                            'required': [
                                                'latitude',
                                                'longitude'
                                            ]
                                        }
                                    },
                                    'required': [
                                        'low',
                                        'high'
                                    ]
                                },
                                'circle': {
                                    'type': 'object',
                                    'description': 'A circle defined by a center point and radius.',
                                    'properties': {
                                        'center': {
                                            'type': 'object',
                                            'description': 'The center of the circle.',
                                            'properties': {
                                                'latitude': {
                                                    'type': 'number',
                                                    'description': 'The latitude of the center point.'
                                                },
                                                'longitude': {
                                                    'type': 'number',
                                                    'description': 'The longitude of the center point.'
                                                }
                                            },
                                            'required': [
                                                'latitude',
                                                'longitude'
                                            ]
                                        },
                                        'radius': {
                                            'type': 'number',
                                            'description': 'The radius of the circle in meters.'
                                        }
                                    },
                                    'required': [
                                        'center',
                                        'radius'
                                    ]
                                }
                            },
                            'required': []
                        },
                        'locationRestriction': {
                            'type': 'object',
                            'description': 'Restricts the search to a specific region. Cannot be set with \'locationBias\'.',
                            'properties': {
                                'rectangle': {
                                    'type': 'object',
                                    'description': 'A rectangle defined by northeast and southwest corners.',
                                    'properties': {
                                        'low': {
                                            'type': 'object',
                                            'description': 'The southwest point.',
                                            'properties': {
                                                'latitude': {
                                                    'type': 'number',
                                                    'description': 'The latitude of the southwest point.'
                                                },
                                                'longitude': {
                                                    'type': 'number',
                                                    'description': 'The longitude of the southwest point.'
                                                }
                                            },
                                            'required': [
                                                'latitude',
                                                'longitude'
                                            ]
                                        },
                                        'high': {
                                            'type': 'object',
                                            'description': 'The northeast point.',
                                            'properties': {
                                                'latitude': {
                                                    'type': 'number',
                                                    'description': 'The latitude of the northeast point.'
                                                },
                                                'longitude': {
                                                    'type': 'number',
                                                    'description': 'The longitude of the northeast point.'
                                                }
                                            },
                                            'required': [
                                                'latitude',
                                                'longitude'
                                            ]
                                        }
                                    },
                                    'required': [
                                        'low',
                                        'high'
                                    ]
                                }
                            },
                            'required': [
                                'rectangle'
                            ]
                        },
                        'evOptions': {
                            'type': 'object',
                            'description': 'Electric vehicle (EV) filtering options.',
                            'properties': {
                                'minimumChargingRateKw': {
                                    'type': 'number',
                                    'description': 'Minimum required charging rate in kilowatts.'
                                },
                                'connectorTypes': {
                                    'type': 'array',
                                    'description': """ List of preferred EV connector types. Places without any of the specified connectors are excluded. Valid values include:
                                             - "EV_CONNECTOR_TYPE_UNSPECIFIED": Unspecified connector.
                                            - "EV_CONNECTOR_TYPE_OTHER": Other connector types.
                                            - "EV_CONNECTOR_TYPE_J1772": J1772 type 1 connector.
                                            - "EV_CONNECTOR_TYPE_TYPE_2": IEC 62196 type 2 connector (MENNEKES).
                                            - "EV_CONNECTOR_TYPE_CHADEMO": CHAdeMO connector.
                                            - "EV_CONNECTOR_TYPE_CCS_COMBO_1": Combined Charging System, type-1 J-1772.
                                            - "EV_CONNECTOR_TYPE_CCS_COMBO_2": Combined Charging System, type-2 Mennekes.
                                            - "EV_CONNECTOR_TYPE_TESLA": Generic Tesla connector. May vary by region (e.g., NACS, CCS2, GB/T).
                                            - "EV_CONNECTOR_TYPE_UNSPECIFIED_GB_T": GB/T standard connector (China).
                                            - "EV_CONNECTOR_TYPE_UNSPECIFIED_WALL_OUTLET": Unspecified wall outlet.
                                            - "EV_CONNECTOR_TYPE_NACS": North American Charging System (NACS), SAE J3400 standard. """,
                                    'items': {
                                        'type': 'string'
                                    }
                                }
                            },
                            'required': []
                        },
                        'routingParameters': {
                            'type': 'object',
                            'description': 'Parameters that affect routing calculations.',
                            'properties': {
                                'origin': {
                                    'type': 'object',
                                    'description': 'The origin for routing calculations.',
                                    'properties': {
                                        'latitude': {
                                            'type': 'number',
                                            'description': 'The latitude of the origin.'
                                        },
                                        'longitude': {
                                            'type': 'number',
                                            'description': 'The longitude of the origin.'
                                        }
                                    },
                                    'required': [
                                        'latitude',
                                        'longitude'
                                    ]
                                },
                                'travelMode': {
                                    'type': 'string',
                                    'description': """ Specifies the mode of travel.
                                           One of: "DRIVE", "BICYCLE", "WALK", "TWO_WHEELER". Defaults to "DRIVE". """
                                },
                                'routeModifiers': {
                                    'type': 'object',
                                    'description': 'Modifiers for the route.',
                                    'properties': {
                                        'avoidTolls': {
                                            'type': 'boolean',
                                            'description': 'Avoid toll roads.'
                                        },
                                        'avoidHighways': {
                                            'type': 'boolean',
                                            'description': 'Avoid highways.'
                                        },
                                        'avoidFerries': {
                                            'type': 'boolean',
                                            'description': 'Avoid ferries.'
                                        },
                                        'avoidIndoor': {
                                            'type': 'boolean',
                                            'description': 'Avoid indoor navigation.'
                                        }
                                    },
                                    'required': []
                                },
                                'routingPreference': {
                                    'type': 'string',
                                    'description': """ Specifies how to compute routing summaries.
                                           One of: "TRAFFIC_UNAWARE", "TRAFFIC_AWARE", "TRAFFIC_AWARE_OPTIMAL".
                                          Defaults to "TRAFFIC_UNAWARE". """
                                }
                            },
                            'required': []
                        },
                        'searchAlongRouteParameters': {
                            'type': 'object',
                            'description': 'Specifies a polyline to bias search results along a route.',
                            'properties': {
                                'polyline': {
                                    'type': 'object',
                                    'description': 'The route polyline.',
                                    'properties': {
                                        'encodedPolyline': {
                                            'type': 'string',
                                            'description': 'An encoded polyline string.'
                                        }
                                    },
                                    'required': [
                                        'encodedPolyline'
                                    ]
                                }
                            },
                            'required': [
                                'polyline'
                            ]
                        },
                        'includePureServiceAreaBusinesses': {
                            'type': 'boolean',
                            'description': """ If true, includes businesses that
                               do not have a physical address on Google Maps (e.g., plumbers, cleaning services). """
                        }
                    },
                    'required': [
                        'textQuery'
                    ]
                }
            },
            'required': [
                'request'
            ]
        }
    }
)
def searchText(request: Dict[str, Union[str, int, bool, dict, list]]) -> Dict[str, Union[str, List[dict]]]:
    """
    Performs a text-based search for places using optional filters.

    This function processes a search request structured according to the
    GoogleMapsPlacesV1SearchTextRequest schema. Supported filters include:
    'strictTypeFiltering', 'priceLevels', 'locationBias', 'openNow',
    'minRating', 'includePureServiceAreaBusinesses', 'locationRestriction',
    'languageCode', 'pageSize', 'regionCode', 'textQuery', and others.

    Args:
        request (Dict[str, Union[str, int, bool, dict, list]]): Dictionary representing search request object containing the text query and optional filtering parameters.:
            - 'textQuery' (str): Required. The text query for the textual search.
            - 'languageCode' (Optional[str]): The preferred language for place details.
              See https://developers.google.com/maps/faq#languagesupport for supported languages.
            - 'regionCode' (Optional[str]): The Unicode country/region code (CLDR)
              of the request's origin. This can affect results based on applicable law.
              See https://www.unicode.org/cldr/charts/latest/supplemental/territory_language_information.html.
            - 'rankPreference' (Optional[str]): Specifies how results are ranked.
              Valid values: "DISTANCE" (ranks by distance), "RELEVANCE" (default, ranks by relevance), "RANK_PREFERENCE_UNSPECIFIED" (defaults to RELEVANCE).
            - 'includedType' (Optional[str]): The requested place type. Only one type is supported.
              For a full list of types, see https://developers.google.com/maps/documentation/places/web-service/place-types.
            - 'openNow' (Optional[bool]): If true, restricts the search to places that are currently open. Defaults to false.
            - 'minRating' (Optional[float]): Filters out results with a rating strictly less than this limit.
              Valid values are between 0.0 and 5.0, in 0.5 increments.
            - 'maxResultCount' (Optional[int]): Deprecated. Use 'pageSize' instead. Maximum number of results to return (up to 20).
            - 'pageSize' (Optional[int]): The maximum number of results per page. Defaults to 20. The maximum value is 20.
            - 'pageToken' (Optional[str]): A token from a previous search to retrieve the next page of results.
            - 'priceLevels' (Optional[List[str]]): Restricts the search to places with the specified price levels.
              Allowed values include: "PRICE_LEVEL_FREE", "PRICE_LEVEL_INEXPENSIVE",
              "PRICE_LEVEL_MODERATE", "PRICE_LEVEL_EXPENSIVE", "PRICE_LEVEL_VERY_EXPENSIVE".
            - 'strictTypeFiltering' (Optional[bool]): If true, only results of the specified 'includedType' will be returned. Defaults to false.
            - 'locationBias' (Optional[Dict[str, Dict[str, Dict[str, float]]]]): Biases the search results to a specific region. Cannot be set with 'locationRestriction'. Can be a 'rectangle' or 'circle'.
                - 'rectangle' (Optional[Dict[str, Dict[str, float]]]): A rectangle defined by northeast and southwest corners.
                    - 'low' (Dict[str, float]): The southwest point.
                        - 'latitude' (float): The latitude of the southwest point.
                        - 'longitude' (float): The longitude of the southwest point.
                    - 'high' (Dict[str, float]): The northeast point.
                        - 'latitude' (float): The latitude of the northeast point.
                        - 'longitude' (float): The longitude of the northeast point.
                - 'circle' (Optional[Dict[str, Dict[str, float]]]): A circle defined by a center point and radius.
                    - 'center' (Dict[str, float]): The center of the circle.
                        - 'latitude' (float): The latitude of the center point.
                        - 'longitude' (float): The longitude of the center point.
                    - 'radius' (float): The radius of the circle in meters.
            - 'locationRestriction' (Optional[Dict[str, Dict[str, Dict[str, Dict[str, float]]]]]): Restricts the search to a specific region. Cannot be set with 'locationBias'.
                - 'rectangle' (Dict[str, Dict[str, Dict[str, float]]]): A rectangle defined by northeast and southwest corners.
                    - 'low' (Dict[str, float]): The southwest point.
                        - 'latitude' (float): The latitude of the southwest point.
                        - 'longitude' (float): The longitude of the southwest point.
                    - 'high' (Dict[str, float]): The northeast point.
                        - 'latitude' (float): The latitude of the northeast point.
                        - 'longitude' (float): The longitude of the northeast point.
            - 'evOptions' (Optional[Dict[str, Union[List[str], float]]]): Electric vehicle (EV) filtering options.
                - 'minimumChargingRateKw' (Optional[float]): Minimum required charging rate in kilowatts.
                - 'connectorTypes' (Optional[List[str]]): List of preferred EV connector types. Places without any of the specified connectors are excluded. Valid values include:
                    - "EV_CONNECTOR_TYPE_UNSPECIFIED": Unspecified connector.
                    - "EV_CONNECTOR_TYPE_OTHER": Other connector types.
                    - "EV_CONNECTOR_TYPE_J1772": J1772 type 1 connector.
                    - "EV_CONNECTOR_TYPE_TYPE_2": IEC 62196 type 2 connector (MENNEKES).
                    - "EV_CONNECTOR_TYPE_CHADEMO": CHAdeMO connector.
                    - "EV_CONNECTOR_TYPE_CCS_COMBO_1": Combined Charging System, type-1 J-1772.
                    - "EV_CONNECTOR_TYPE_CCS_COMBO_2": Combined Charging System, type-2 Mennekes.
                    - "EV_CONNECTOR_TYPE_TESLA": Generic Tesla connector. May vary by region (e.g., NACS, CCS2, GB/T).
                    - "EV_CONNECTOR_TYPE_UNSPECIFIED_GB_T": GB/T standard connector (China).
                    - "EV_CONNECTOR_TYPE_UNSPECIFIED_WALL_OUTLET": Unspecified wall outlet.
                    - "EV_CONNECTOR_TYPE_NACS": North American Charging System (NACS), SAE J3400 standard.
            - 'routingParameters' (Optional[Dict[str, Dict[str, Dict[str, float]]]]): Parameters that affect routing calculations.
                - 'origin' (Optional[Dict[str, float]]): The origin for routing calculations.
                    - 'latitude' (float): The latitude of the origin.
                    - 'longitude' (float): The longitude of the origin.
                - 'travelMode' (Optional[str]): Specifies the mode of travel.
                    One of: "DRIVE", "BICYCLE", "WALK", "TWO_WHEELER". Defaults to "DRIVE".
                - 'routeModifiers' (Optional[Dict[str, bool]]): Modifiers for the route.
                    - 'avoidTolls' (Optional[bool]): Avoid toll roads.
                    - 'avoidHighways' (Optional[bool]): Avoid highways.
                    - 'avoidFerries' (Optional[bool]): Avoid ferries.
                    - 'avoidIndoor' (Optional[bool]): Avoid indoor navigation.
                - 'routingPreference' (Optional[str]): Specifies how to compute routing summaries.
                    One of: "TRAFFIC_UNAWARE", "TRAFFIC_AWARE", "TRAFFIC_AWARE_OPTIMAL".
                    Defaults to "TRAFFIC_UNAWARE".
            - 'searchAlongRouteParameters' (Optional[Dict[str, Dict[str, str]]]): Specifies a polyline to bias search results along a route.
                - 'polyline' (Dict[str, str]): The route polyline.
                    - 'encodedPolyline' (str): An encoded polyline string.
            - 'includePureServiceAreaBusinesses' (Optional[bool]): If true, includes businesses that
              do not have a physical address on Google Maps (e.g., plumbers, cleaning services).

    Returns:
        Dict[str, Union[str, List[dict]]]: : Dictionary containing search results and metadata.
        
            - places (List[dict]): List of matching places.
                Each place contains:
                - id (str): Unique place identifier.
                - name (str): Name of the place.
                - address (str): Formatted address.
                - location (Dict[str, float]): Geographic coordinates.
                    - latitude (float): Latitude.
                    - longitude (float): Longitude.
                - phone_number (str): International phone number.
                - website (str): Website URL.
            - nextPageToken (str): Token for retrieving next page (currently always empty).
            - searchUri (str): URI that can replicate the search (currently not implemented).

    Raises:
        ValidationError: If the request parameters fail validation (e.g., missing textQuery,
            invalid minRating range, invalid price levels, invalid enum values).
        TypeError: If request is not a dictionary.
        ValueError: If required fields are missing or invalid.
    
    Limitations:
        - locationBias parameter is accepted but not used in filtering
        - pageToken parameter is accepted but pagination is not implemented
        - regionCode parameter is accepted but not used in filtering
        - searchAlongRouteParameters are accepted but not implemented
        - evOptions are accepted but EV filtering is not implemented
        - rankPreference parameter is accepted but not used in result ordering
        - routingParameters are accepted but routing summaries are not computed
        - Maximum of 20 results can be returned (pageSize/maxResultCount <= 20)
        - nextPageToken is always empty (pagination not implemented)
        - contextualContents are always empty (not implemented)
    """
    # Validate request using Pydantic model
    validated_request = SearchTextRequest(**request)
    # Convert back to dictionary for backward compatibility
    request = validated_request.model_dump()
    
    filtered_places = []

    # Determine the maximum number of results (using pageSize if provided, else maxResultCount defaulting to 20)
    max_results = request.get("pageSize") or request.get("maxResultCount") or 10

    # Get text query; required (already validated by Pydantic)
    text_query = request.get("textQuery", "").lower()

    # Optional filters:
    strict_type_filtering = request.get("strictTypeFiltering", False)
    included_type = request.get("includedType")
    price_levels = request.get("priceLevels", [])
    open_now = request.get("openNow", False)
    min_rating = request.get("minRating", None)
    include_pure_service_area_businesses = request.get("includePureServiceAreaBusinesses", True)

    # These parameters are acknowledged but not fully implemented in this simulation
    # as they require more complex logic or data.
    region_code = request.get("regionCode")
    rank_preference = request.get("rankPreference")
    search_along_route_parameters = request.get("searchAlongRouteParameters")
    ev_options = request.get("evOptions")
    routing_parameters = request.get("routingParameters")
    if routing_parameters:
        if 'travelMode' not in routing_parameters:
            routing_parameters['travelMode'] = 'DRIVE'
        if 'routingPreference' not in routing_parameters:
            routing_parameters['routingPreference'] = 'TRAFFIC_UNAWARE'
    session_token = request.get("sessionToken")
    language_code = request.get('language_code')

    results = []
    for place_id, place in DB.items():
        # Basic text search in name and address
        if text_query.lower() not in place.get("name", "").lower() and \
           text_query.lower() not in place.get("formattedAddress", "").lower():
            continue

        # Filtering logic
        if open_now and not place.get("currentOpeningHours", {}).get("openNow", False):
            continue
        if price_levels and place.get("priceLevel") not in price_levels:
            continue
        if min_rating and place.get("rating", 0) < min_rating:
            continue
        if strict_type_filtering and included_type and place.get("primaryType") != included_type:
            continue
        if include_pure_service_area_businesses is False and place.get("pureServiceAreaBusiness"):
            continue

        # Location bias/restriction (simple implementation)
        location_bias = request.get("locationBias") or request.get("locationRestriction")
        if location_bias and "circle" in location_bias:
            place_loc = place.get("location")
            if not place_loc:
                continue  # Skip places with no location if restriction is applied

            center = location_bias["circle"]["center"]
            radius = location_bias["circle"]["radius"]
            distance = _haversine_distance(
                center["latitude"], center["longitude"],
                place_loc["latitude"], place_loc["longitude"]
            )
            if distance > radius:
                continue
        
        # Language code check (simplified)
        if language_code and place.get("primaryTypeDisplayName", {}).get("languageCode") != language_code:
            continue

        # result_place = Place(
        #     id=place.get("id"),
        #     name=place.get("name"),
        #     address=place.get("formattedAddress"),
        #     location=place.get("location", {}),
        #     phone_number=place.get("internationalPhoneNumber"),
        #     website=place.get("websiteUri"),
        # )
        results.append(place)

    return {"places": results[:max_results]}
