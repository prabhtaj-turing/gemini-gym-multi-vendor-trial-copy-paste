import os
import json
from typing import Dict, Any

# ---------------------------------------------------------------------------------------
# In-Memory Database Structure
# ---------------------------------------------------------------------------------------
# Initialize the DB as a global variable (simulating a JSON file)
DB: Dict[str, Any] = {
    "customers": {
        "cus_20240521184759000001": {
            "id": "cus_20240521184759000001",
            "object": "customer",
            "name": "Alice Smith",
            "email": "alice.smith@example.com",
            "created": 1716337679,
            "livemode": False,
            "metadata": {"loyalty_tier": "gold"},
        },
        "cus_20240521184759000002": {
            "id": "cus_20240521184759000002",
            "object": "customer",
            "name": "Bob Johnson",
            "email": "bob.j@example.com",
            "created": 1716337690,
            "livemode": False,
            "metadata": {},
        },
        "cus_20240521184759000003": {
            "id": "cus_20240521184759000003",
            "object": "customer",
            "name": "Charlie Brown",
            "email": "charlie.b@example.com",
            "created": 1716337700,
            "livemode": False,
            "metadata": {"segment": "SMB"},
        },
    },
    "products": {
        "prod_20240521184759000004": {
            "id": "prod_20240521184759000004",
            "object": "product",
            "name": "Premium Software License",
            "description": "Annual license for our premium software suite.",
            "active": True,
            "created": 1716337710,
            "updated": 1716337710,
            "livemode": False,
            "metadata": {"version": "2.0"},
        },
        "prod_20240521184759000005": {
            "id": "prod_20240521184759000005",
            "object": "product",
            "name": "Basic Support Plan",
            "description": "Monthly support for basic inquiries.",
            "active": True,
            "created": 1716337720,
            "updated": 1716337720,
            "livemode": False,
            "metadata": {},
        },
    },
    "prices": {
        "price_20240521184759000006": {
            "id": "price_20240521184759000006",
            "object": "price",
            "active": True,
            "product": "prod_20240521184759000004",
            "unit_amount": 12000,
            "currency": "usd",
            "type": "recurring",
            "recurring": {"interval": "year", "interval_count": 1},
            "livemode": False,
            "metadata": {},
            "billing_scheme": "per_unit",
            "created": 1716337730,
        },
        "price_20240521184759000007": {
            "id": "price_20240521184759000007",
            "object": "price",
            "active": True,
            "product": "prod_20240521184759000005",
            "unit_amount": 1500,
            "currency": "usd",
            "type": "recurring",
            "recurring": {"interval": "month", "interval_count": 1},
            "livemode": False,
            "metadata": {},
            "billing_scheme": "per_unit",
            "created": 1716337740,
        },
        "price_20240521184759000008": {
            "id": "price_20240521184759000008",
            "object": "price",
            "active": True,
            "product": "prod_20240521184759000004",
            "unit_amount": 1000,
            "currency": "eur",
            "type": "one_time",
            "livemode": False,
            "metadata": {},
            "billing_scheme": "per_unit",
            "created": 1716337750,
        },
    },
    "payment_links": {
        "pl_20240521184759000009": {
            "id": "pl_20240521184759000009",
            "object": "payment_link",
            "active": True,
            "livemode": False,
            "metadata": {"campaign": "summer_sale"},
            "line_items": {
                "object": "list",
                "data": [
                    {
                        "id": "sli_20240521184759000010",
                        "price": {
                            "id": "price_20240521184759000006",
                            "product": "prod_20240521184759000004",
                        },
                        "quantity": 1,
                    }
                ],
                "has_more": False,
            },
            "after_completion": {"type": "hosted_confirmation"},
        }
    },
    "invoices": {
        "inv_20240521184759000011": {
            "id": "inv_20240521184759000011",
            "object": "invoice",
            "customer": "cus_20240521184759000001",
            "status": "draft",
            "total": 0,
            "amount_due": 0,
            "currency": "usd",
            "created": 1716337760,
            "due_date": 1718929760,
            "livemode": False,
            "metadata": {},
            "lines": {"object": "list", "data": []},
        },
        "inv_20240521184759000012": {
            "id": "inv_20240521184759000012",
            "object": "invoice",
            "customer": "cus_20240521184759000002",
            "status": "open",
            "total": 1500,
            "amount_due": 1500,
            "currency": "usd",
            "created": 1716337770,
            "due_date": 1716942570,
            "livemode": False,
            "metadata": {"project": "Q2_billing"},
            "lines": {
                "object": "list",
                "data": [
                    {
                        "id": "il_20240521184759000013",
                        "amount": 1500,
                        "description": "Monthly Basic Support Plan",
                        "price": {
                            "id": "price_20240521184759000007",
                            "product": "prod_20240521184759000005",
                        },
                        "quantity": 1,
                    }
                ],
                "has_more": False,
            },
        },
    },
    "invoice_items": {
        "ii_20240521184759000014": {
            "id": "ii_20240521184759000014",
            "object": "invoiceitem",
            "customer": "cus_20240521184759000001",
            "invoice": "inv_20240521184759000011",
            "price": {
                "id": "price_20240521184759000006",
                "product": "prod_20240521184759000004",
                "unit_amount": 12000,
                "currency": "usd",
            },
            "amount": 12000,
            "currency": "usd",
            "quantity": 1,
            "livemode": False,
            "metadata": {},
        }
    },
    "balance": {
        "object": "balance",
        "available": [
            {
                "amount": 50000,
                "currency": "usd",
                "source_types": {"card": 40000, "bank_account": 10000},
            },
            {"amount": 10000, "currency": "eur", "source_types": None},
        ],
        "pending": [
            {"amount": 10000, "currency": "usd", "source_types": {"card": 10000}}
        ],
        "livemode": False,
    },
    "refunds": {
        "re_20240521184759000015": {
            "id": "re_20240521184759000015",
            "object": "refund",
            "payment_intent": "pi_20240521184759000016",
            "amount": 500,
            "currency": "usd",
            "status": "succeeded",
            "reason": "customer_requested",
            "created": 1716337780,
            "metadata": {},
        }
    },
    "payment_intents": {
        "pi_20240521184759000016": {
            "id": "pi_20240521184759000016",
            "object": "payment_intent",
            "amount": 2500,
            "currency": "usd",
            "customer": "cus_20240521184759000001",
            "status": "succeeded",
            "created": 1716337775,
            "livemode": False,
            "metadata": {"order_id": "order_abc123"},
        },
        "pi_20240521184759000017": {
            "id": "pi_20240521184759000017",
            "object": "payment_intent",
            "amount": 5000,
            "currency": "eur",
            "customer": "cus_20240521184759000003",
            "status": "requires_payment_method",
            "created": 1716337785,
            "livemode": False,
            "metadata": {},
        },
    },
    "subscriptions": {
        "sub_20240521184759000018": {
            "id": "sub_20240521184759000018",
            "object": "subscription",
            "customer": "cus_20240521184759000001",
            "status": "active",
            "current_period_start": 1716076800,
            "current_period_end": 1747699200,
            "created": 1716076800,
            "items": {
                "object": "list",
                "data": [
                    {
                        "id": "si_20240521184759000019",
                        "object": "subscription_item",
                        "price": {
                            "id": "price_20240521184759000006",
                            "product": "prod_20240521184759000004",
                            "active": True,
                            "currency": "usd",
                            "unit_amount": 12000,
                            "type": "recurring",
                            "recurring": {"interval": "year", "interval_count": 1},
                        },
                        "quantity": 1,
                        "created": 1716076800,
                        "metadata": {},
                    }
                ],
                "has_more": False,
            },
            "livemode": False,
            "metadata": {},
            "cancel_at_period_end": False,
            "start_date": 1716076800,
        },
        "sub_20240521184759000020": {
            "id": "sub_20240521184759000020",
            "object": "subscription",
            "customer": "cus_20240521184759000002",
            "status": "trialing",
            "current_period_start": 1716337600,
            "current_period_end": 1718929600,
            "created": 1716337600,
            "items": {
                "object": "list",
                "data": [
                    {
                        "id": "si_20240521184759000021",
                        "object": "subscription_item",
                        "price": {
                            "id": "price_20240521184759000007",
                            "product": "prod_20240521184759000005",
                            "active": True,
                            "currency": "usd",
                            "unit_amount": 1500,
                            "type": "recurring",
                            "recurring": {"interval": "month", "interval_count": 1},
                        },
                        "quantity": 1,
                        "created": 1716337600,
                        "metadata": {},
                    }
                ],
                "has_more": False,
            },
            "livemode": False,
            "metadata": {},
            "cancel_at_period_end": False,
            "start_date": 1716337600,
            "trial_start": 1716337600,
            "trial_end": 1718929600,
        },
    },
    "coupons": {
        "cou_20240521184759000022": {
            "id": "cou_20240521184759000022",
            "object": "coupon",
            "name": "SUMMER20",
            "percent_off": 20,
            "currency": None,
            "duration": "once",
            "duration_in_months": None,
            "livemode": False,
            "valid": True,
            "metadata": {},
        },
        "cou_20240521184759000023": {
            "id": "cou_20240521184759000023",
            "object": "coupon",
            "name": "WELCOME10USD",
            "amount_off": 1000,
            "currency": "usd",
            "duration": "forever",
            "duration_in_months": None,
            "livemode": False,
            "valid": True,
            "metadata": {"promo_code": "NEWUSER"},
        },
    },
    "disputes": {
        "dp_20240521184759000024": {
            "id": "dp_20240521184759000024",
            "object": "dispute",
            "amount": 2500,
            "currency": "usd",
            "status": "warning_needs_response",
            "reason": "fraudulent",
            "charge": "ch_1234567890abcdef",
            "payment_intent": "pi_20240521184759000016",
            "created": 1716337790,
            "evidence": {
                "cancellation_policy_disclosure": None,
                "cancellation_rebuttal": None,
                "duplicate_charge_explanation": None,
                "uncategorized_text": "Customer claims they did not authorize this charge.",
            },
            "is_charge_refundable": False,
            "livemode": False,
            "metadata": {},
        }
    },
}


# -------------------------------------------------------------------
# Persistence Helpers
# -------------------------------------------------------------------
def save_state(filepath: str):
    """Saves the current API state to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(DB, f)


def load_state(
    filepath: str,
) -> None:
    """Loads the API state from a JSON file."""
    global DB
    try:
        with open(filepath, "r") as f:
            DB.update(json.load(f))
    except FileNotFoundError:
        pass


def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
