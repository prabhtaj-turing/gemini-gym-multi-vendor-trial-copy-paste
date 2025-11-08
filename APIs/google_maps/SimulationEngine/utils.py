# google_maps/SimulationEngine/utils.py
import math
from google_maps.SimulationEngine.db import DB
from typing import Dict, Any
import requests
import json
import os
import re
from typing import Optional, List, Dict, Any, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def _create_place(place_data: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a new place in the database.

    Args:
        place_data (dict): A dictionary containing the place data. 
                           The "id" field is required. All other fields are optional.
                           A comprehensive `place_data` object can include the following fields:
                           - id (str): Unique identifier for the place.
                           - name (Optional[str]): Name of the place.
                           - rating (Optional[float]): Average user rating.
                           - userRatingCount (Optional[int]): Number of user ratings.
                           - formattedAddress (Optional[str]): Full address in display-friendly format.
                           - primaryType (Optional[str]): The place's primary classification type.
                           - types (Optional[List[str]]): Additional types describing the place.
                           - location (Optional[Dict[str, float]]): Geographic location of the place.
                               - latitude (float): Latitude coordinate.
                               - longitude (float): Longitude coordinate.
                           - businessStatus (Optional[str]): Current operating status (e.g., OPERATIONAL).
                           - priceLevel (Optional[str]): Price level of the place.
                           - openNow (Optional[bool]): Whether the place is currently open.
                           - takeout (Optional[bool]): If takeout is available.
                           - delivery (Optional[bool]): If delivery is available.
                           - dineIn (Optional[bool]): If dine-in is available.
                           - outdoorSeating (Optional[bool]): If outdoor seating is available.
                           - curbsidePickup (Optional[bool]): If curbside pickup is supported.
                           - servesBreakfast (Optional[bool]): If the place serves breakfast.
                           - servesLunch (Optional[bool]): If the place serves lunch.
                           - servesDinner (Optional[bool]): If the place serves dinner.
                           - servesBrunch (Optional[bool]): If the place serves brunch.
                           - servesCoffee (Optional[bool]): If the place serves coffee.
                           - servesDessert (Optional[bool]): If the place serves dessert.
                           - servesBeer (Optional[bool]): If the place serves beer.
                           - servesWine (Optional[bool]): If the place serves wine.
                           - servesCocktails (Optional[bool]): If the place serves cocktails.
                           - goodForChildren (Optional[bool]): If the place is child-friendly.
                           - goodForGroups (Optional[bool]): If the place is good for groups.
                           - goodForWatchingSports (Optional[bool]): If the place is suitable for watching sports.
                           - allowsDogs (Optional[bool]): If dogs are allowed.
                           - restroom (Optional[bool]): If restrooms are available.
                           - reservations (Optional[bool]): Whether reservations are accepted.
                           - paymentOptions (Optional[Dict[str, bool]]): Accepted payment methods.
                               - acceptsCashOnly (bool): Whether the place accepts cash payments only.
                               - acceptsCreditCards (bool): Whether the place accepts credit card payments.
                               - acceptsDebitCards (bool): Whether the place accepts debit card payments.
                               - acceptsNfc (bool): Whether the place accepts NFC/mobile payments.
                           - accessibilityOptions (Optional[Dict[str, bool]]): Accessibility features.
                               - wheelchairAccessibleEntrance (bool): Whether the entrance is wheelchair accessible.
                               - wheelchairAccessibleRestroom (bool): Whether the restroom is wheelchair accessible.
                               - wheelchairAccessibleParking (bool): Whether parking is wheelchair accessible.
                               - wheelchairAccessibleSeating (bool): Whether seating is wheelchair accessible.
                           - googleMapsUri (Optional[str]): URI to the place on Google Maps.
                           - websiteUri (Optional[str]): URI of the place's website.
                           - internationalPhoneNumber (Optional[str]): International formatted phone number.
                           - nationalPhoneNumber (Optional[str]): National formatted phone number.
                           - iconMaskBaseUri (Optional[str]): Base URI of the place icon.
                           - iconBackgroundColor (Optional[str]): Background color of the place icon.
                           - plusCode (Optional[Dict[str, str]]): Plus code information.
                               - globalCode (str): Global plus code for the location.
                               - compoundCode (str): Compound plus code for the location.
                           - primaryTypeDisplayName (Optional[Dict[str, str]]): Localized type display name.
                               - text (str): Display name text for the primary type.
                               - languageCode (str): Language code for the display name.
                           - photos (Optional[List[Dict[str, Any]]]): List of photo metadata.
                               - name (str): Resource name of the photo.
                               - widthPx (int): Width of the photo in pixels.
                               - heightPx (int): Height of the photo in pixels.
                               - googleMapsUri (str): Link to the photo on Google Maps.
                               - flagContentUri (str): URI to flag inappropriate content.
                           - postalAddress (Optional[Dict[str, Any]]): Structured address data.
                               - addressLines (List[str]): Unstructured address lines.
                               - recipients (List[str]): Recipient names (e.g., business or person).
                               - sublocality (str): Sublocality (e.g., district or neighborhood).
                               - postalCode (str): Postal or ZIP code.
                               - organization (str): Business or organization name.
                               - revision (int): Revision number of the address format.
                               - locality (str): City or town.
                               - administrativeArea (str): State, province, or region.
                               - languageCode (str): Language of the address.
                               - regionCode (str): Country/region code.
                               - sortingCode (str): Sorting code for mail delivery.
                           - reviewSummary (Optional[Dict[str, str]]): Summary for reviews.
                               - flagContentUri (str): URI to flag review summary.
                           - reviews (Optional[List[Dict[str, Any]]]): List of user reviews.
                               - name (str): Identifier of the review.
                               - googleMapsUri (str): Link to the full review.
                               - flagContentUri (str): URI to flag the review.
                               - rating (float): Rating given by the reviewer.
                               - relativePublishTimeDescription (str): Human-readable time since published.
                               - publishTime (str): ISO timestamp of review publication.
                               - authorAttribution (Dict[str, str]): Reviewer information.
                                   - displayName (str): Name of the reviewer.
                                   - photoUri (str): Photo URI of the reviewer.
                                   - uri (str): Link to reviewer's profile.

    Returns:
        dict: The created place data dictionary that was stored in the database.

    Raises:
        ValueError: If 'id' is missing or already exists.
    """
    # ID is required for a place to be uniquely identified.
    if "id" not in place_data:
        raise ValueError("Place data must contain an 'id' field.")

    if not DB.get(place_data["id"], None):
        DB[place_data["id"]] = place_data
    else:
        raise ValueError(f"Place with id '{place_data['id']}' already exists.")

    return place_data


def _haversine_distance(lat1, lon1, lat2, lon2):
    """
    A helper function that computes the Haversine distance between two geographic points in meters.

    Args:
        lat1 (float): Latitude of the first point.
        lon1 (float): Longitude of the first point.
        lat2 (float): Latitude of the second point.
        lon2 (float): Longitude of the second point.

    Returns:
        float: The distance in meters between the two points.
    """
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c