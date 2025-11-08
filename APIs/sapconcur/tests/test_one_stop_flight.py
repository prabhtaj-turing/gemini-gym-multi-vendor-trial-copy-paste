"""
Test suite for flight search functions in the SAP Concur API simulation.
"""

import copy
import unittest
import uuid

from ..SimulationEngine import custom_errors, models
from ..SimulationEngine.db import DB
from ..flights import search_direct_flight, search_onestop_flight
from common_utils.base_case import BaseTestCaseWithErrorHandler


# Initial DB state for flight search tests
FLIGHT_SEARCH_INITIAL_DB_STATE = {
    "users": {
        "550e8400-e29b-41d4-a716-446655441000": {
            "id": "550e8400-e29b-41d4-a716-446655441000",
            "external_id": "emp-1001",
            "user_name": "john.doe@company.com",
            "given_name": "John",
            "family_name": "Doe",
            "display_name": "John Doe",
            "active": True,
            "email": "john.doe@company.com",
            "locale": "en-US",
            "timezone": "America/New_York",
            "created_at": "2023-06-15T09:30:00Z",
            "last_modified": "2023-10-20T14:22:00Z",
        }
    },
    "trips": {
        "550e8400-e29b-41d4-a716-446655441001": {
            "trip_id": "550e8400-e29b-41d4-a716-446655441001",
            "trip_name": "Q3 Sales Conference",
            "user_id": "550e8400-e29b-41d4-a716-446655441000",
            "start_date": "2023-09-10",
            "end_date": "2023-09-15",
            "destination_summary": "Los Angeles, CA",
            "status": "CONFIRMED",
            "created_date": "2023-07-20T11:30:00Z",
            "last_modified_date": "2023-08-15T14:20:00Z",
            "booking_type": "AIR",
            "is_virtual_trip": False,
            "is_canceled": False,
            "is_guest_booking": False,
            "booking_ids": [
                "550e8400-e29b-41d4-a716-446655441002",
                "550e8400-e29b-41d4-a716-446655441003",
                "550e8400-e29b-41d4-a716-446655441004",
            ],
        }
    },
    "bookings": {
        "9fd1bc79-510c-448b-ad58-e9ac31740bb1": {
            "booking_id": "9fd1bc79-510c-448b-ad58-e9ac31740bb1",
            "booking_source": "HAT Airlines",
            "record_locator": "ZU8VTC",
            "trip_id": "a763eb82-f7b2-46a7-afe3-a6d148bd6dbe",
            "date_booked_local": "2024-05-07T18:16:10",
            "form_of_payment_name": "Mastercard Card ****2008",
            "form_of_payment_type": "CREDIT_CARD",
            "delivery": "Electronic",
            "status": "CONFIRMED",
            "passengers": [
                {
                    "passenger_id": "af557fcd-b688-48ca-ae43-d90929b6a221",
                    "name_first": "Harper",
                    "name_last": "Thomas",
                    "text_name": "Thomas/Harper",
                    "pax_type": "ADT",
                    "dob": "1991-03-20",
                }
            ],
            "segments": [
                {
                    "segment_id": "073a9c79-4c73-49cf-ac1e-017ee64a0930",
                    "type": "AIR",
                    "status": "CONFIRMED",
                    "confirmation_number": "HAT0508093",
                    "start_date": "2024-05-08 02:02:00",
                    "end_date": "2024-05-08 04:09:00",
                    "vendor": "HAT",
                    "vendor_name": "HAT Airlines",
                    "currency": "USD",
                    "total_rate": 636,
                    "departure_airport": "ORD",
                    "arrival_airport": "ATL",
                    "flight_number": "HAT093",
                    "aircraft_type": "Boeing 737",
                    "fare_class": "J",
                    "is_direct": True,
                    "baggage": {"count": 1, "weight_kg": 23, "nonfree_count": 0},
                    "scheduled_departure_time": "02:00:00",
                    "scheduled_arrival_time": "04:00:00",
                    "flight_schedule_data": {
                        "2024-05-01": {
                            "actual_departure_time_est": "2024-05-01T02:05:00",
                            "actual_arrival_time_est": "2024-05-01T03:56:00",
                            "scheduled_departure_time_est": "02:00:00",
                            "scheduled_arrival_time_est": "04:00:00",
                        },
                        "2024-05-02": {
                            "actual_departure_time_est": "2024-05-02T02:04:00",
                            "actual_arrival_time_est": "2024-05-02T03:34:00",
                            "scheduled_departure_time_est": "02:00:00",
                            "scheduled_arrival_time_est": "04:00:00",
                        },
                        "2024-05-03": {
                            "actual_departure_time_est": "2024-05-03T01:30:00",
                            "actual_arrival_time_est": "2024-05-03T03:26:00",
                            "scheduled_departure_time_est": "02:00:00",
                            "scheduled_arrival_time_est": "04:00:00",
                        },
                        "2024-05-04": {
                            "actual_departure_time_est": "2024-05-04T02:26:00",
                            "actual_arrival_time_est": "2024-05-04T04:05:00",
                            "scheduled_departure_time_est": "02:00:00",
                            "scheduled_arrival_time_est": "04:00:00",
                        },
                        "2024-05-05": {
                            "actual_departure_time_est": "2024-05-05T01:54:00",
                            "actual_arrival_time_est": "2024-05-05T04:09:00",
                            "scheduled_departure_time_est": "02:00:00",
                            "scheduled_arrival_time_est": "04:00:00",
                        },
                        "2024-05-06": {
                            "actual_departure_time_est": "2024-05-06T01:36:00",
                            "actual_arrival_time_est": "2024-05-06T03:53:00",
                            "scheduled_departure_time_est": "02:00:00",
                            "scheduled_arrival_time_est": "04:00:00",
                        },
                        "2024-05-07": {
                            "actual_departure_time_est": "2024-05-07T02:26:00",
                            "actual_arrival_time_est": "2024-05-07T04:11:00",
                            "scheduled_departure_time_est": "02:00:00",
                            "scheduled_arrival_time_est": "04:00:00",
                        },
                        "2024-05-08": {
                            "actual_departure_time_est": "2024-05-08T02:02:00",
                            "actual_arrival_time_est": "2024-05-08T04:09:00",
                            "scheduled_departure_time_est": "02:00:00",
                            "scheduled_arrival_time_est": "04:00:00",
                        },
                        "2024-05-09": {
                            "actual_departure_time_est": "2024-05-09T02:20:00",
                            "actual_arrival_time_est": "2024-05-09T04:42:00",
                            "scheduled_departure_time_est": "02:00:00",
                            "scheduled_arrival_time_est": "04:00:00",
                        },
                        "2024-05-10": {
                            "actual_departure_time_est": "2024-05-10T01:36:00",
                            "actual_arrival_time_est": "2024-05-10T03:33:00",
                            "scheduled_departure_time_est": "02:00:00",
                            "scheduled_arrival_time_est": "04:00:00",
                        },
                        "2024-05-11": {
                            "actual_departure_time_est": "2024-05-11T01:40:00",
                            "actual_arrival_time_est": "2024-05-11T03:59:00",
                            "scheduled_departure_time_est": "02:00:00",
                            "scheduled_arrival_time_est": "04:00:00",
                        },
                        "2024-05-12": {
                            "actual_departure_time_est": "2024-05-12T02:20:00",
                            "actual_arrival_time_est": "2024-05-12T04:17:00",
                            "scheduled_departure_time_est": "02:00:00",
                            "scheduled_arrival_time_est": "04:00:00",
                        },
                        "2024-05-13": {
                            "actual_departure_time_est": "2024-05-13T02:13:00",
                            "actual_arrival_time_est": "2024-05-13T03:49:00",
                            "scheduled_departure_time_est": "02:00:00",
                            "scheduled_arrival_time_est": "04:00:00",
                        },
                        "2024-05-14": {
                            "actual_departure_time_est": "2024-05-14T02:07:00",
                            "actual_arrival_time_est": "2024-05-14T04:36:00",
                            "scheduled_departure_time_est": "02:00:00",
                            "scheduled_arrival_time_est": "04:00:00",
                        },
                        "2024-05-15": {
                            "actual_departure_time_est": "2024-05-15T02:17:00",
                            "actual_arrival_time_est": "2024-05-15T03:56:00",
                            "scheduled_departure_time_est": "02:00:00",
                            "scheduled_arrival_time_est": "04:00:00",
                        },
                    },
                    "availability_data": {
                        "2024-05-16": {
                            "basic_economy": 17,
                            "economy": 18,
                            "business": 9,
                        },
                        "2024-05-17": {
                            "basic_economy": 17,
                            "economy": 19,
                            "business": 7,
                        },
                        "2024-05-18": {
                            "basic_economy": 2,
                            "economy": 4,
                            "business": 20,
                        },
                        "2024-05-19": {"basic_economy": 5, "economy": 9, "business": 4},
                        "2024-05-20": {
                            "basic_economy": 7,
                            "economy": 14,
                            "business": 11,
                        },
                        "2024-05-21": {
                            "basic_economy": 14,
                            "economy": 10,
                            "business": 17,
                        },
                        "2024-05-22": {
                            "basic_economy": 8,
                            "economy": 18,
                            "business": 1,
                        },
                        "2024-05-23": {"basic_economy": 9, "economy": 0, "business": 1},
                        "2024-05-24": {"basic_economy": 5, "economy": 7, "business": 3},
                        "2024-05-25": {
                            "basic_economy": 19,
                            "economy": 19,
                            "business": 3,
                        },
                        "2024-05-26": {
                            "basic_economy": 7,
                            "economy": 16,
                            "business": 13,
                        },
                        "2024-05-27": {
                            "basic_economy": 19,
                            "economy": 7,
                            "business": 7,
                        },
                        "2024-05-28": {
                            "basic_economy": 15,
                            "economy": 10,
                            "business": 16,
                        },
                        "2024-05-29": {
                            "basic_economy": 5,
                            "economy": 4,
                            "business": 12,
                        },
                        "2024-05-30": {
                            "basic_economy": 10,
                            "economy": 19,
                            "business": 18,
                        },
                    },
                    "pricing_data": {
                        "2024-05-16": {
                            "basic_economy": 97,
                            "economy": 171,
                            "business": 401,
                        },
                        "2024-05-17": {
                            "basic_economy": 51,
                            "economy": 196,
                            "business": 287,
                        },
                        "2024-05-18": {
                            "basic_economy": 75,
                            "economy": 140,
                            "business": 284,
                        },
                        "2024-05-19": {
                            "basic_economy": 74,
                            "economy": 139,
                            "business": 266,
                        },
                        "2024-05-20": {
                            "basic_economy": 75,
                            "economy": 120,
                            "business": 360,
                        },
                        "2024-05-21": {
                            "basic_economy": 53,
                            "economy": 127,
                            "business": 391,
                        },
                        "2024-05-22": {
                            "basic_economy": 55,
                            "economy": 195,
                            "business": 397,
                        },
                        "2024-05-23": {
                            "basic_economy": 95,
                            "economy": 113,
                            "business": 433,
                        },
                        "2024-05-24": {
                            "basic_economy": 70,
                            "economy": 178,
                            "business": 364,
                        },
                        "2024-05-25": {
                            "basic_economy": 58,
                            "economy": 188,
                            "business": 292,
                        },
                        "2024-05-26": {
                            "basic_economy": 87,
                            "economy": 159,
                            "business": 278,
                        },
                        "2024-05-27": {
                            "basic_economy": 97,
                            "economy": 169,
                            "business": 260,
                        },
                        "2024-05-28": {
                            "basic_economy": 68,
                            "economy": 125,
                            "business": 295,
                        },
                        "2024-05-29": {
                            "basic_economy": 91,
                            "economy": 177,
                            "business": 496,
                        },
                        "2024-05-30": {
                            "basic_economy": 97,
                            "economy": 179,
                            "business": 344,
                        },
                    },
                    "operational_status": {
                        "2024-05-01": "landed",
                        "2024-05-02": "landed",
                        "2024-05-03": "landed",
                        "2024-05-04": "landed",
                        "2024-05-05": "landed",
                        "2024-05-06": "landed",
                        "2024-05-07": "landed",
                        "2024-05-08": "landed",
                        "2024-05-09": "landed",
                        "2024-05-10": "landed",
                        "2024-05-11": "landed",
                        "2024-05-12": "landed",
                        "2024-05-13": "landed",
                        "2024-05-14": "landed",
                        "2024-05-15": "landed",
                        "2024-05-16": "available",
                        "2024-05-17": "available",
                        "2024-05-18": "available",
                        "2024-05-19": "available",
                        "2024-05-20": "available",
                        "2024-05-21": "available",
                        "2024-05-22": "available",
                        "2024-05-23": "available",
                        "2024-05-24": "available",
                        "2024-05-25": "available",
                        "2024-05-26": "available",
                        "2024-05-27": "available",
                        "2024-05-28": "available",
                        "2024-05-29": "available",
                        "2024-05-30": "available",
                    },
                    "estimated_departure_times": {},
                    "estimated_arrival_times": {},
                },
                {
                    "segment_id": "a0418297-a1a5-4146-9998-915fedb90ef1",
                    "type": "AIR",
                    "status": "CONFIRMED",
                    "confirmation_number": "HAT0508110",
                    "start_date": "2024-05-24 14:18:00",
                    "end_date": "2024-05-24 17:18:00",
                    "vendor": "HAT",
                    "vendor_name": "HAT Airlines",
                    "currency": "USD",
                    "total_rate": 1690,
                    "departure_airport": "ATL",
                    "arrival_airport": "LGA",
                    "flight_number": "HAT110",
                    "aircraft_type": "Boeing 737",
                    "fare_class": "J",
                    "is_direct": True,
                    "baggage": {"count": 1, "weight_kg": 23, "nonfree_count": 0},
                    "scheduled_departure_time": "14:00:00",
                    "scheduled_arrival_time": "16:30:00",
                    "flight_schedule_data": {
                        "2024-05-01": {
                            "actual_departure_time_est": "2024-05-01T13:34:00",
                            "actual_arrival_time_est": "2024-05-01T16:24:00",
                            "scheduled_departure_time_est": "14:00:00",
                            "scheduled_arrival_time_est": "16:30:00",
                        },
                        "2024-05-02": {
                            "actual_departure_time_est": "2024-05-02T14:13:00",
                            "actual_arrival_time_est": "2024-05-02T16:26:00",
                            "scheduled_departure_time_est": "14:00:00",
                            "scheduled_arrival_time_est": "16:30:00",
                        },
                        "2024-05-03": {
                            "actual_departure_time_est": "2024-05-03T13:39:00",
                            "actual_arrival_time_est": "2024-05-03T16:22:00",
                            "scheduled_departure_time_est": "14:00:00",
                            "scheduled_arrival_time_est": "16:30:00",
                        },
                        "2024-05-04": {
                            "actual_departure_time_est": "2024-05-04T14:20:00",
                            "actual_arrival_time_est": "2024-05-04T16:32:00",
                            "scheduled_departure_time_est": "14:00:00",
                            "scheduled_arrival_time_est": "16:30:00",
                        },
                        "2024-05-05": {
                            "actual_departure_time_est": "2024-05-05T13:59:00",
                            "actual_arrival_time_est": "2024-05-05T16:47:00",
                            "scheduled_departure_time_est": "14:00:00",
                            "scheduled_arrival_time_est": "16:30:00",
                        },
                        "2024-05-06": {
                            "actual_departure_time_est": "2024-05-06T14:08:00",
                            "actual_arrival_time_est": "2024-05-06T16:45:00",
                            "scheduled_departure_time_est": "14:00:00",
                            "scheduled_arrival_time_est": "16:30:00",
                        },
                        "2024-05-07": {
                            "actual_departure_time_est": "2024-05-07T14:01:00",
                            "actual_arrival_time_est": "2024-05-07T16:57:00",
                            "scheduled_departure_time_est": "14:00:00",
                            "scheduled_arrival_time_est": "16:30:00",
                        },
                        "2024-05-08": {
                            "actual_departure_time_est": "2024-05-08T14:18:00",
                            "actual_arrival_time_est": "2024-05-08T17:18:00",
                            "scheduled_departure_time_est": "14:00:00",
                            "scheduled_arrival_time_est": "16:30:00",
                        },
                        "2024-05-09": {
                            "actual_departure_time_est": "2024-05-09T13:58:00",
                            "actual_arrival_time_est": "2024-05-09T16:47:00",
                            "scheduled_departure_time_est": "14:00:00",
                            "scheduled_arrival_time_est": "16:30:00",
                        },
                        "2024-05-10": {
                            "actual_departure_time_est": "2024-05-10T14:19:00",
                            "actual_arrival_time_est": "2024-05-10T16:50:00",
                            "scheduled_departure_time_est": "14:00:00",
                            "scheduled_arrival_time_est": "16:30:00",
                        },
                        "2024-05-11": {
                            "actual_departure_time_est": "2024-05-11T14:17:00",
                            "actual_arrival_time_est": "2024-05-11T17:04:00",
                            "scheduled_departure_time_est": "14:00:00",
                            "scheduled_arrival_time_est": "16:30:00",
                        },
                        "2024-05-12": {
                            "actual_departure_time_est": "2024-05-12T14:27:00",
                            "actual_arrival_time_est": "2024-05-12T17:04:00",
                            "scheduled_departure_time_est": "14:00:00",
                            "scheduled_arrival_time_est": "16:30:00",
                        },
                        "2024-05-13": {
                            "actual_departure_time_est": "2024-05-13T13:43:00",
                            "actual_arrival_time_est": "2024-05-13T16:29:00",
                            "scheduled_departure_time_est": "14:00:00",
                            "scheduled_arrival_time_est": "16:30:00",
                        },
                        "2024-05-14": {
                            "actual_departure_time_est": "2024-05-14T13:32:00",
                            "actual_arrival_time_est": "2024-05-14T15:32:00",
                            "scheduled_departure_time_est": "14:00:00",
                            "scheduled_arrival_time_est": "16:30:00",
                        },
                        "2024-05-15": {
                            "actual_departure_time_est": "2024-05-15T14:06:00",
                            "actual_arrival_time_est": None,
                            "scheduled_departure_time_est": "14:00:00",
                            "scheduled_arrival_time_est": "16:30:00",
                        },
                        "2024-05-24": {
                            "actual_departure_time_est": "2024-05-24T14:18:00",
                            "actual_arrival_time_est": "2024-05-24T17:18:00",
                            "scheduled_departure_time_est": "14:00:00",
                            "scheduled_arrival_time_est": "16:30:00",
                        },
                    },
                    "availability_data": {
                        "2024-05-16": {
                            "basic_economy": 17,
                            "economy": 11,
                            "business": 4,
                        },
                        "2024-05-17": {
                            "basic_economy": 17,
                            "economy": 20,
                            "business": 0,
                        },
                        "2024-05-18": {
                            "basic_economy": 16,
                            "economy": 20,
                            "business": 7,
                        },
                        "2024-05-19": {
                            "basic_economy": 9,
                            "economy": 18,
                            "business": 12,
                        },
                        "2024-05-20": {
                            "basic_economy": 15,
                            "economy": 9,
                            "business": 17,
                        },
                        "2024-05-21": {
                            "basic_economy": 12,
                            "economy": 18,
                            "business": 6,
                        },
                        "2024-05-22": {
                            "basic_economy": 7,
                            "economy": 1,
                            "business": 16,
                        },
                        "2024-05-23": {
                            "basic_economy": 6,
                            "economy": 0,
                            "business": 14,
                        },
                        "2024-05-24": {
                            "basic_economy": 8,
                            "economy": 9,
                            "business": 16,
                        },
                        "2024-05-25": {
                            "basic_economy": 12,
                            "economy": 1,
                            "business": 15,
                        },
                        "2024-05-26": {
                            "basic_economy": 17,
                            "economy": 4,
                            "business": 8,
                        },
                        "2024-05-27": {
                            "basic_economy": 9,
                            "economy": 1,
                            "business": 16,
                        },
                        "2024-05-28": {"basic_economy": 3, "economy": 0, "business": 4},
                        "2024-05-29": {
                            "basic_economy": 14,
                            "economy": 6,
                            "business": 13,
                        },
                        "2024-05-30": {
                            "basic_economy": 12,
                            "economy": 16,
                            "business": 1,
                        },
                    },
                    "pricing_data": {
                        "2024-05-16": {
                            "basic_economy": 76,
                            "economy": 146,
                            "business": 442,
                        },
                        "2024-05-17": {
                            "basic_economy": 83,
                            "economy": 155,
                            "business": 302,
                        },
                        "2024-05-18": {
                            "basic_economy": 93,
                            "economy": 151,
                            "business": 450,
                        },
                        "2024-05-19": {
                            "basic_economy": 53,
                            "economy": 117,
                            "business": 354,
                        },
                        "2024-05-20": {
                            "basic_economy": 67,
                            "economy": 168,
                            "business": 424,
                        },
                        "2024-05-21": {
                            "basic_economy": 86,
                            "economy": 157,
                            "business": 353,
                        },
                        "2024-05-22": {
                            "basic_economy": 84,
                            "economy": 189,
                            "business": 205,
                        },
                        "2024-05-23": {
                            "basic_economy": 62,
                            "economy": 179,
                            "business": 419,
                        },
                        "2024-05-24": {
                            "basic_economy": 62,
                            "economy": 105,
                            "business": 496,
                        },
                        "2024-05-25": {
                            "basic_economy": 50,
                            "economy": 107,
                            "business": 268,
                        },
                        "2024-05-26": {
                            "basic_economy": 92,
                            "economy": 174,
                            "business": 259,
                        },
                        "2024-05-27": {
                            "basic_economy": 90,
                            "economy": 139,
                            "business": 237,
                        },
                        "2024-05-28": {
                            "basic_economy": 90,
                            "economy": 132,
                            "business": 219,
                        },
                        "2024-05-29": {
                            "basic_economy": 85,
                            "economy": 182,
                            "business": 293,
                        },
                        "2024-05-30": {
                            "basic_economy": 56,
                            "economy": 176,
                            "business": 425,
                        },
                    },
                    "operational_status": {
                        "2024-05-01": "landed",
                        "2024-05-02": "landed",
                        "2024-05-03": "landed",
                        "2024-05-04": "landed",
                        "2024-05-05": "landed",
                        "2024-05-06": "landed",
                        "2024-05-07": "landed",
                        "2024-05-08": "landed",
                        "2024-05-09": "landed",
                        "2024-05-10": "landed",
                        "2024-05-11": "landed",
                        "2024-05-12": "landed",
                        "2024-05-13": "landed",
                        "2024-05-14": "landed",
                        "2024-05-15": "flying",
                        "2024-05-16": "available",
                        "2024-05-17": "available",
                        "2024-05-18": "available",
                        "2024-05-19": "available",
                        "2024-05-20": "available",
                        "2024-05-21": "available",
                        "2024-05-22": "available",
                        "2024-05-23": "available",
                        "2024-05-24": "available",
                        "2024-05-25": "available",
                        "2024-05-26": "available",
                        "2024-05-27": "available",
                        "2024-05-28": "available",
                        "2024-05-29": "available",
                        "2024-05-30": "available",
                    },
                    "estimated_departure_times": {},
                    "estimated_arrival_times": {"2024-05-15": "2024-05-15T16:33:00"},
                },
                {
                    "segment_id": "c49a478d-6f5b-46e3-a0ca-79b4ef755068",
                    "type": "AIR",
                    "status": "CONFIRMED",
                    "confirmation_number": "HAT0519172",
                    "start_date": "2024-05-24 23:00:00",
                    "end_date": "2024-05-25 00:00:00",
                    "vendor": "HAT",
                    "vendor_name": "HAT Airlines",
                    "currency": "USD",
                    "total_rate": 1772,
                    "departure_airport": "LGA",
                    "arrival_airport": "PHL",
                    "flight_number": "HAT172",
                    "aircraft_type": "Boeing 737",
                    "fare_class": "J",
                    "is_direct": True,
                    "baggage": {"count": 1, "weight_kg": 23, "nonfree_count": 0},
                    "scheduled_departure_time": "23:00:00",
                    "scheduled_arrival_time": "00:00:00+1",
                    "flight_schedule_data": {
                        "2024-05-01": {
                            "actual_departure_time_est": "2024-05-01T22:32:00",
                            "actual_arrival_time_est": "2024-05-01T23:18:00",
                            "scheduled_departure_time_est": "23:00:00",
                            "scheduled_arrival_time_est": "00:00:00+1",
                        },
                        "2024-05-02": {
                            "actual_departure_time_est": "2024-05-02T22:45:00",
                            "actual_arrival_time_est": "2024-05-03T00:02:00",
                            "scheduled_departure_time_est": "23:00:00",
                            "scheduled_arrival_time_est": "00:00:00+1",
                        },
                        "2024-05-03": {
                            "actual_departure_time_est": "2024-05-03T23:26:00",
                            "actual_arrival_time_est": "2024-05-04T00:41:00",
                            "scheduled_departure_time_est": "23:00:00",
                            "scheduled_arrival_time_est": "00:00:00+1",
                        },
                        "2024-05-04": {
                            "actual_departure_time_est": "2024-05-04T23:26:00",
                            "actual_arrival_time_est": "2024-05-05T00:38:00",
                            "scheduled_departure_time_est": "23:00:00",
                            "scheduled_arrival_time_est": "00:00:00+1",
                        },
                        "2024-05-05": {
                            "actual_departure_time_est": "2024-05-05T23:11:00",
                            "actual_arrival_time_est": "2024-05-06T00:02:00",
                            "scheduled_departure_time_est": "23:00:00",
                            "scheduled_arrival_time_est": "00:00:00+1",
                        },
                        "2024-05-06": {
                            "actual_departure_time_est": "2024-05-06T22:38:00",
                            "actual_arrival_time_est": "2024-05-06T23:22:00",
                            "scheduled_departure_time_est": "23:00:00",
                            "scheduled_arrival_time_est": "00:00:00+1",
                        },
                        "2024-05-07": {
                            "actual_departure_time_est": "2024-05-07T22:32:00",
                            "actual_arrival_time_est": "2024-05-08T00:00:00",
                            "scheduled_departure_time_est": "23:00:00",
                            "scheduled_arrival_time_est": "00:00:00+1",
                        },
                        "2024-05-08": {
                            "actual_departure_time_est": "2024-05-08T23:25:00",
                            "actual_arrival_time_est": "2024-05-09T00:39:00",
                            "scheduled_departure_time_est": "23:00:00",
                            "scheduled_arrival_time_est": "00:00:00+1",
                        },
                        "2024-05-09": {
                            "actual_departure_time_est": "2024-05-09T23:05:00",
                            "actual_arrival_time_est": "2024-05-10T00:05:00",
                            "scheduled_departure_time_est": "23:00:00",
                            "scheduled_arrival_time_est": "00:00:00+1",
                        },
                        "2024-05-10": {
                            "actual_departure_time_est": "2024-05-10T22:40:00",
                            "actual_arrival_time_est": "2024-05-10T23:52:00",
                            "scheduled_departure_time_est": "23:00:00",
                            "scheduled_arrival_time_est": "00:00:00+1",
                        },
                        "2024-05-11": {
                            "actual_departure_time_est": "2024-05-11T23:02:00",
                            "actual_arrival_time_est": "2024-05-12T00:28:00",
                            "scheduled_departure_time_est": "23:00:00",
                            "scheduled_arrival_time_est": "00:00:00+1",
                        },
                        "2024-05-12": {
                            "actual_departure_time_est": "2024-05-12T23:18:00",
                            "actual_arrival_time_est": "2024-05-13T00:01:00",
                            "scheduled_departure_time_est": "23:00:00",
                            "scheduled_arrival_time_est": "00:00:00+1",
                        },
                        "2024-05-13": {
                            "actual_departure_time_est": "2024-05-13T22:42:00",
                            "actual_arrival_time_est": "2024-05-13T23:37:00",
                            "scheduled_departure_time_est": "23:00:00",
                            "scheduled_arrival_time_est": "00:00:00+1",
                        },
                        "2024-05-14": {
                            "actual_departure_time_est": "2024-05-14T22:44:00",
                            "actual_arrival_time_est": "2024-05-15T00:06:00",
                            "scheduled_departure_time_est": "23:00:00",
                            "scheduled_arrival_time_est": "00:00:00+1",
                        },
                        "2024-05-24": {
                            "actual_departure_time_est": "2024-05-24T23:00:00",
                            "actual_arrival_time_est": "2024-05-25T00:00:00",
                            "scheduled_departure_time_est": "23:00:00",
                            "scheduled_arrival_time_est": "00:00:00+1",
                        },
                    },
                    "availability_data": {
                        "2024-05-16": {
                            "basic_economy": 10,
                            "economy": 2,
                            "business": 13,
                        },
                        "2024-05-17": {
                            "basic_economy": 15,
                            "economy": 1,
                            "business": 4,
                        },
                        "2024-05-18": {
                            "basic_economy": 15,
                            "economy": 10,
                            "business": 4,
                        },
                        "2024-05-19": {"basic_economy": 5, "economy": 3, "business": 8},
                        "2024-05-20": {
                            "basic_economy": 6,
                            "economy": 8,
                            "business": 10,
                        },
                        "2024-05-21": {"basic_economy": 1, "economy": 5, "business": 8},
                        "2024-05-22": {
                            "basic_economy": 5,
                            "economy": 1,
                            "business": 20,
                        },
                        "2024-05-23": {
                            "basic_economy": 13,
                            "economy": 5,
                            "business": 0,
                        },
                        "2024-05-24": {
                            "basic_economy": 7,
                            "economy": 2,
                            "business": 15,
                        },
                        "2024-05-25": {
                            "basic_economy": 18,
                            "economy": 2,
                            "business": 13,
                        },
                        "2024-05-26": {"basic_economy": 7, "economy": 5, "business": 7},
                        "2024-05-27": {
                            "basic_economy": 5,
                            "economy": 19,
                            "business": 7,
                        },
                        "2024-05-28": {
                            "basic_economy": 19,
                            "economy": 13,
                            "business": 10,
                        },
                        "2024-05-29": {
                            "basic_economy": 2,
                            "economy": 18,
                            "business": 4,
                        },
                        "2024-05-30": {
                            "basic_economy": 13,
                            "economy": 19,
                            "business": 18,
                        },
                    },
                    "pricing_data": {
                        "2024-05-16": {
                            "basic_economy": 98,
                            "economy": 191,
                            "business": 449,
                        },
                        "2024-05-17": {
                            "basic_economy": 63,
                            "economy": 126,
                            "business": 214,
                        },
                        "2024-05-18": {
                            "basic_economy": 80,
                            "economy": 125,
                            "business": 319,
                        },
                        "2024-05-19": {
                            "basic_economy": 71,
                            "economy": 147,
                            "business": 319,
                        },
                        "2024-05-20": {
                            "basic_economy": 76,
                            "economy": 127,
                            "business": 391,
                        },
                        "2024-05-21": {
                            "basic_economy": 63,
                            "economy": 146,
                            "business": 349,
                        },
                        "2024-05-22": {
                            "basic_economy": 55,
                            "economy": 125,
                            "business": 360,
                        },
                        "2024-05-23": {
                            "basic_economy": 95,
                            "economy": 120,
                            "business": 399,
                        },
                        "2024-05-24": {
                            "basic_economy": 79,
                            "economy": 102,
                            "business": 360,
                        },
                        "2024-05-25": {
                            "basic_economy": 55,
                            "economy": 159,
                            "business": 434,
                        },
                        "2024-05-26": {
                            "basic_economy": 98,
                            "economy": 130,
                            "business": 467,
                        },
                        "2024-05-27": {
                            "basic_economy": 58,
                            "economy": 156,
                            "business": 496,
                        },
                        "2024-05-28": {
                            "basic_economy": 59,
                            "economy": 113,
                            "business": 301,
                        },
                        "2024-05-29": {
                            "basic_economy": 65,
                            "economy": 111,
                            "business": 479,
                        },
                        "2024-05-30": {
                            "basic_economy": 50,
                            "economy": 194,
                            "business": 240,
                        },
                    },
                    "operational_status": {
                        "2024-05-01": "landed",
                        "2024-05-02": "landed",
                        "2024-05-03": "landed",
                        "2024-05-04": "landed",
                        "2024-05-05": "landed",
                        "2024-05-06": "landed",
                        "2024-05-07": "landed",
                        "2024-05-08": "landed",
                        "2024-05-09": "landed",
                        "2024-05-10": "landed",
                        "2024-05-11": "landed",
                        "2024-05-12": "landed",
                        "2024-05-13": "landed",
                        "2024-05-14": "landed",
                        "2024-05-15": "on time",
                        "2024-05-16": "available",
                        "2024-05-17": "available",
                        "2024-05-18": "available",
                        "2024-05-19": "available",
                        "2024-05-20": "available",
                        "2024-05-21": "available",
                        "2024-05-22": "available",
                        "2024-05-23": "available",
                        "2024-05-24": "available",
                        "2024-05-25": "available",
                        "2024-05-26": "available",
                        "2024-05-27": "available",
                        "2024-05-28": "available",
                        "2024-05-29": "available",
                        "2024-05-30": "available",
                    },
                    "estimated_departure_times": {"2024-05-15": "2024-05-15T22:56:00"},
                    "estimated_arrival_times": {"2024-05-15": "2024-05-15T23:44:00"},
                },
                {
                    "segment_id": "3b918f8f-4fee-45cb-89b7-d800964db239",
                    "type": "AIR",
                    "status": "CONFIRMED",
                    "confirmation_number": "HAT0520197",
                    "start_date": "2024-05-20 17:00:00",
                    "end_date": "2024-05-20 19:00:00",
                    "vendor": "HAT",
                    "vendor_name": "HAT Airlines",
                    "currency": "USD",
                    "total_rate": 1074,
                    "departure_airport": "PHL",
                    "arrival_airport": "ORD",
                    "flight_number": "HAT197",
                    "aircraft_type": "Boeing 737",
                    "fare_class": "J",
                    "is_direct": True,
                    "baggage": {"count": 1, "weight_kg": 23, "nonfree_count": 0},
                    "scheduled_departure_time": "17:00:00",
                    "scheduled_arrival_time": "19:00:00",
                    "flight_schedule_data": {
                        "2024-05-01": {
                            "actual_departure_time_est": "2024-05-01T17:30:00",
                            "actual_arrival_time_est": "2024-05-01T19:11:00",
                            "scheduled_departure_time_est": "17:00:00",
                            "scheduled_arrival_time_est": "19:00:00",
                        },
                        "2024-05-02": {
                            "actual_departure_time_est": "2024-05-02T17:24:00",
                            "actual_arrival_time_est": "2024-05-02T19:01:00",
                            "scheduled_departure_time_est": "17:00:00",
                            "scheduled_arrival_time_est": "19:00:00",
                        },
                        "2024-05-03": {
                            "actual_departure_time_est": "2024-05-03T16:55:00",
                            "actual_arrival_time_est": "2024-05-03T19:13:00",
                            "scheduled_departure_time_est": "17:00:00",
                            "scheduled_arrival_time_est": "19:00:00",
                        },
                        "2024-05-04": {
                            "actual_departure_time_est": "2024-05-04T16:57:00",
                            "actual_arrival_time_est": "2024-05-04T19:05:00",
                            "scheduled_departure_time_est": "17:00:00",
                            "scheduled_arrival_time_est": "19:00:00",
                        },
                        "2024-05-05": {
                            "actual_departure_time_est": "2024-05-05T16:52:00",
                            "actual_arrival_time_est": "2024-05-05T18:41:00",
                            "scheduled_departure_time_est": "17:00:00",
                            "scheduled_arrival_time_est": "19:00:00",
                        },
                        "2024-05-06": {
                            "actual_departure_time_est": "2024-05-06T17:16:00",
                            "actual_arrival_time_est": "2024-05-06T19:22:00",
                            "scheduled_departure_time_est": "17:00:00",
                            "scheduled_arrival_time_est": "19:00:00",
                        },
                        "2024-05-07": {
                            "actual_departure_time_est": "2024-05-07T16:48:00",
                            "actual_arrival_time_est": "2024-05-07T18:20:00",
                            "scheduled_departure_time_est": "17:00:00",
                            "scheduled_arrival_time_est": "19:00:00",
                        },
                        "2024-05-08": {
                            "actual_departure_time_est": "2024-05-08T17:02:00",
                            "actual_arrival_time_est": "2024-05-08T18:32:00",
                            "scheduled_departure_time_est": "17:00:00",
                            "scheduled_arrival_time_est": "19:00:00",
                        },
                        "2024-05-09": {
                            "actual_departure_time_est": "2024-05-09T17:29:00",
                            "actual_arrival_time_est": "2024-05-09T19:38:00",
                            "scheduled_departure_time_est": "17:00:00",
                            "scheduled_arrival_time_est": "19:00:00",
                        },
                        "2024-05-10": {
                            "actual_departure_time_est": "2024-05-10T17:30:00",
                            "actual_arrival_time_est": "2024-05-10T19:09:00",
                            "scheduled_departure_time_est": "17:00:00",
                            "scheduled_arrival_time_est": "19:00:00",
                        },
                        "2024-05-11": {
                            "actual_departure_time_est": "2024-05-11T16:37:00",
                            "actual_arrival_time_est": "2024-05-11T18:36:00",
                            "scheduled_departure_time_est": "17:00:00",
                            "scheduled_arrival_time_est": "19:00:00",
                        },
                        "2024-05-12": {
                            "actual_departure_time_est": "2024-05-12T17:04:00",
                            "actual_arrival_time_est": "2024-05-12T18:47:00",
                            "scheduled_departure_time_est": "17:00:00",
                            "scheduled_arrival_time_est": "19:00:00",
                        },
                        "2024-05-13": {
                            "actual_departure_time_est": "2024-05-13T16:55:00",
                            "actual_arrival_time_est": "2024-05-13T19:18:00",
                            "scheduled_departure_time_est": "17:00:00",
                            "scheduled_arrival_time_est": "19:00:00",
                        },
                        "2024-05-14": {
                            "actual_departure_time_est": "2024-05-14T17:02:00",
                            "actual_arrival_time_est": "2024-05-14T18:48:00",
                            "scheduled_departure_time_est": "17:00:00",
                            "scheduled_arrival_time_est": "19:00:00",
                        },
                    },
                    "availability_data": {
                        "2024-05-16": {"basic_economy": 6, "economy": 5, "business": 4},
                        "2024-05-17": {
                            "basic_economy": 2,
                            "economy": 12,
                            "business": 5,
                        },
                        "2024-05-18": {
                            "basic_economy": 15,
                            "economy": 14,
                            "business": 17,
                        },
                        "2024-05-19": {
                            "basic_economy": 16,
                            "economy": 5,
                            "business": 4,
                        },
                        "2024-05-20": {
                            "basic_economy": 13,
                            "economy": 10,
                            "business": 0,
                        },
                        "2024-05-21": {"basic_economy": 2, "economy": 8, "business": 5},
                        "2024-05-22": {
                            "basic_economy": 19,
                            "economy": 13,
                            "business": 15,
                        },
                        "2024-05-23": {
                            "basic_economy": 20,
                            "economy": 2,
                            "business": 20,
                        },
                        "2024-05-24": {
                            "basic_economy": 16,
                            "economy": 1,
                            "business": 11,
                        },
                        "2024-05-25": {
                            "basic_economy": 17,
                            "economy": 9,
                            "business": 8,
                        },
                        "2024-05-26": {
                            "basic_economy": 6,
                            "economy": 14,
                            "business": 19,
                        },
                        "2024-05-27": {
                            "basic_economy": 7,
                            "economy": 18,
                            "business": 0,
                        },
                        "2024-05-28": {
                            "basic_economy": 20,
                            "economy": 5,
                            "business": 11,
                        },
                        "2024-05-29": {
                            "basic_economy": 4,
                            "economy": 5,
                            "business": 10,
                        },
                        "2024-05-30": {
                            "basic_economy": 11,
                            "economy": 14,
                            "business": 6,
                        },
                    },
                    "pricing_data": {
                        "2024-05-16": {
                            "basic_economy": 95,
                            "economy": 127,
                            "business": 321,
                        },
                        "2024-05-17": {
                            "basic_economy": 98,
                            "economy": 169,
                            "business": 254,
                        },
                        "2024-05-18": {
                            "basic_economy": 89,
                            "economy": 152,
                            "business": 494,
                        },
                        "2024-05-19": {
                            "basic_economy": 59,
                            "economy": 199,
                            "business": 381,
                        },
                        "2024-05-20": {
                            "basic_economy": 68,
                            "economy": 180,
                            "business": 378,
                        },
                        "2024-05-21": {
                            "basic_economy": 67,
                            "economy": 177,
                            "business": 316,
                        },
                        "2024-05-22": {
                            "basic_economy": 80,
                            "economy": 157,
                            "business": 217,
                        },
                        "2024-05-23": {
                            "basic_economy": 92,
                            "economy": 189,
                            "business": 266,
                        },
                        "2024-05-24": {
                            "basic_economy": 63,
                            "economy": 179,
                            "business": 255,
                        },
                        "2024-05-25": {
                            "basic_economy": 54,
                            "economy": 100,
                            "business": 200,
                        },
                        "2024-05-26": {
                            "basic_economy": 72,
                            "economy": 170,
                            "business": 404,
                        },
                        "2024-05-27": {
                            "basic_economy": 68,
                            "economy": 103,
                            "business": 304,
                        },
                        "2024-05-28": {
                            "basic_economy": 77,
                            "economy": 185,
                            "business": 238,
                        },
                        "2024-05-29": {
                            "basic_economy": 65,
                            "economy": 177,
                            "business": 443,
                        },
                        "2024-05-30": {
                            "basic_economy": 77,
                            "economy": 174,
                            "business": 276,
                        },
                    },
                    "operational_status": {
                        "2024-05-01": "landed",
                        "2024-05-02": "landed",
                        "2024-05-03": "landed",
                        "2024-05-04": "landed",
                        "2024-05-05": "landed",
                        "2024-05-06": "landed",
                        "2024-05-07": "landed",
                        "2024-05-08": "landed",
                        "2024-05-09": "landed",
                        "2024-05-10": "landed",
                        "2024-05-11": "landed",
                        "2024-05-12": "landed",
                        "2024-05-13": "landed",
                        "2024-05-14": "landed",
                        "2024-05-15": "delayed",
                        "2024-05-16": "available",
                        "2024-05-17": "available",
                        "2024-05-18": "available",
                        "2024-05-19": "available",
                        "2024-05-20": "available",
                        "2024-05-21": "available",
                        "2024-05-22": "available",
                        "2024-05-23": "available",
                        "2024-05-24": "available",
                        "2024-05-25": "available",
                        "2024-05-26": "available",
                        "2024-05-27": "available",
                        "2024-05-28": "available",
                        "2024-05-29": "available",
                        "2024-05-30": "available",
                    },
                    "estimated_departure_times": {"2024-05-15": "2024-05-15T18:28:00"},
                    "estimated_arrival_times": {"2024-05-15": "2024-05-15T20:28:00"},
                },
            ],
            "warnings": [],
            "payment_history": [
                {
                    "payment_id": "credit_card_5794036",
                    "amount": 5172,
                    "timestamp": "2024-05-07T18:16:10",
                    "type": "booking",
                }
            ],
            "created_at": "2024-05-07T18:16:10",
            "last_modified": "2024-05-07T18:16:10",
            "flight_type": "round_trip",
            "cabin": "business",
            "insurance": "no",
            "total_baggages": 1,
            "nonfree_baggages": 0,
            "origin": "ORD",
            "destination": "LGA",
        }
    },
    "locations": {},
    "notifications": {},
    "user_by_external_id": {"emp-1001": "550e8400-e29b-41d4-a716-446655441000"},
    "booking_by_locator": {"ZU8VTC": "9fd1bc79-510c-448b-ad58-e9ac31740bb1"},
    "trips_by_user": {
        "550e8400-e29b-41d4-a716-446655441000": ["550e8400-e29b-41d4-a716-446655441001"]
    },
    "bookings_by_trip": {
        "550e8400-e29b-41d4-a716-446655441001": [
            "550e8400-e29b-41d4-a716-446655441002",
            "550e8400-e29b-41d4-a716-446655441003",
            "550e8400-e29b-41d4-a716-446655441004",
            "550e8400-e29b-41d4-a716-446655441005",
        ]
    },
}


class TestSearchOneStopFlight(BaseTestCaseWithErrorHandler):
    """
    Test suite for the search_direct_flight function.
    """

    @classmethod
    def setUpClass(cls):
        """Save original DB state and set up initial test state."""
        cls.original_db_state = copy.deepcopy(DB)
        DB.clear()
        DB.update(copy.deepcopy(FLIGHT_SEARCH_INITIAL_DB_STATE))

    @classmethod
    def tearDownClass(cls):
        """Restore original DB state."""
        DB.clear()
        DB.update(cls.original_db_state)

    def setUp(self):
        """Reset DB state before each test."""
        DB.clear()
        DB.update(copy.deepcopy(FLIGHT_SEARCH_INITIAL_DB_STATE))
        self._validate_db_structure()

    def _validate_db_structure(self):
        """Validate that the DB structure conforms to ConcurAirlineDB model."""
        try:
            # Ensure all required collections exist with defaults
            DB.setdefault("locations", {})
            DB.setdefault("notifications", {})
            DB.setdefault("user_by_external_id", {})
            DB.setdefault("booking_by_locator", {})
            DB.setdefault("trips_by_user", {})
            DB.setdefault("bookings_by_trip", {})

            # Use the actual ConcurAirlineDB model for validation
            concur_db = models.ConcurAirlineDB(**DB)

        except Exception as e:
            raise AssertionError(
                f"DB structure validation failed using ConcurAirlineDB model: {str(e)}"
            )

    # Success test cases
    def test_search_one_stop_flight_success_basic(self):
        """Test successful search for direct flights JFK to LAX."""
        result = search_onestop_flight(
            departure_airport="ATL", arrival_airport="PHL", departure_date="2024-05-24"
        )

        # Should find 2 direct flights (AA and DL - DL has no is_direct field so defaults to True)
        self.assertEqual(len(result), 2)

        # flight1 should have departure_airport = ATL and arrival_airport = LGA
        # flight2 should have departure_airport = LGA and arrival_airport = PHL
        self.assertEqual(result[0]["departure_airport"], "ATL")
        self.assertEqual(result[0]["arrival_airport"], "LGA")
        self.assertEqual(result[1]["departure_airport"], "LGA")
        self.assertEqual(result[1]["arrival_airport"], "PHL")

        # the airlines should be HAT110 and HAT172
        self.assertEqual(result[0]["flight_number"], "HAT110")
        self.assertEqual(result[1]["flight_number"], "HAT172")


if __name__ == "__main__":
    unittest.main()
