import copy
from datetime import timedelta, datetime, timezone

from stripe.SimulationEngine.custom_errors import ValidationError
from ..SimulationEngine.custom_errors import InvalidRequestError, ResourceNotFoundError
from ..SimulationEngine.db import DB
from ..SimulationEngine.utils import get_fixed_timestamp
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import list_disputes, update_dispute
from ..SimulationEngine.utils import add_dispute_to_db


class TestUpdateDispute(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.charge_id_1 = "ch_001_update_dispute_test"
        self.pi_id_1 = "pi_001_update_dispute_test"

        self.dispute_id_needs_response = "dp_nr_uds_001"
        self.dispute_id_under_review = "dp_ur_uds_001"
        self.dispute_id_closed = "dp_cl_uds_001"
        self.dispute_id_won = "dp_wn_uds_001"
        self.dispute_id_lost = "dp_ls_uds_001"
        self.dispute_id_staged_evidence = "dp_stg_uds_001"

        DB['disputes'] = {
            self.dispute_id_needs_response: {
                "id": self.dispute_id_needs_response, "object": "dispute", "amount": 1000, "currency": "usd",
                "status": "warning_needs_response", "reason": "fraudulent", "charge": self.charge_id_1,
                "payment_intent": self.pi_id_1, "created": get_fixed_timestamp(0),
                "evidence": {
                    "cancellation_policy_disclosure": None,
                    "cancellation_rebuttal": None,
                    "duplicate_charge_explanation": None,
                    "uncategorized_text": None
                },
                "is_charge_refundable": False, "livemode": False, "metadata": {"order_id": "ord_uds_1"}
            },
            self.dispute_id_under_review: {
                "id": self.dispute_id_under_review, "object": "dispute", "amount": 2000, "currency": "eur",
                "status": "under_review", "reason": "product_not_received", "charge": "ch_uds_002",
                "payment_intent": None, "created": get_fixed_timestamp(10),
                "evidence": {
                    "cancellation_policy_disclosure": "Policy was shown at checkout.",
                    "cancellation_rebuttal": "Customer agreed to policy.", # Part of DB model, not updated by func
                    "duplicate_charge_explanation": None,
                    "uncategorized_text": "Initial customer statement."
                },
                "is_charge_refundable": False, "livemode": False, "metadata": {}
            },
            self.dispute_id_closed: {
                "id": self.dispute_id_closed, "object": "dispute", "amount": 500, "currency": "usd",
                "status": "closed", "reason": "credit_not_processed", "charge": "ch_uds_003",
                "payment_intent": None, "created": get_fixed_timestamp(20),
                "evidence": {
                    "cancellation_policy_disclosure": None, "cancellation_rebuttal": None,
                    "duplicate_charge_explanation": None, "uncategorized_text": "Final evidence submitted."
                },
                "is_charge_refundable": False, "livemode": False, "metadata": None
            },
            self.dispute_id_won: {
                "id": self.dispute_id_won, "object": "dispute", "amount": 1500, "currency": "gbp",
                "status": "won", "reason": "general", "charge": "ch_uds_004",
                "payment_intent": None, "created": get_fixed_timestamp(30),
                "evidence": {"uncategorized_text": "We won this dispute with this evidence."},
                "is_charge_refundable": False, "livemode": False
            },
            self.dispute_id_lost: {
                "id": self.dispute_id_lost, "object": "dispute", "amount": 2500, "currency": "usd",
                "status": "lost", "reason": "fraudulent", "charge": "ch_uds_005",
                "payment_intent": None, "created": get_fixed_timestamp(40),
                "evidence": {}, "is_charge_refundable": True, "livemode": False
            },
            self.dispute_id_staged_evidence: {
                "id": self.dispute_id_staged_evidence, "object": "dispute", "amount": 3000, "currency": "usd",
                "status": "warning_needs_response", "reason": "duplicate", "charge": "ch_uds_006",
                "payment_intent": None, "created": get_fixed_timestamp(50),
                "evidence": {
                    "cancellation_policy_disclosure": None, "cancellation_rebuttal": None,
                    "duplicate_charge_explanation": None, "uncategorized_text": None
                },
                "is_charge_refundable": False, "livemode": False
            }
        }

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_update_evidence_no_submit_needs_response(self):
        evidence_payload = {"uncategorized_text": "New evidence provided."}
        updated_dispute = update_dispute(dispute=self.dispute_id_needs_response, evidence=evidence_payload, submit=False)

        self.assertEqual(updated_dispute["id"], self.dispute_id_needs_response)
        self.assertEqual(updated_dispute["evidence"]["uncategorized_text"], "New evidence provided.")
        self.assertIsNone(updated_dispute["evidence"]["cancellation_policy_disclosure"])
        self.assertEqual(updated_dispute["status"], "warning_needs_response")

        db_dispute = DB["disputes"][self.dispute_id_needs_response]
        self.assertEqual(db_dispute["evidence"]["uncategorized_text"], "New evidence provided.")
        self.assertEqual(db_dispute["status"], "warning_needs_response")

    def test_update_evidence_with_submit_needs_response(self):
        evidence_payload = {"cancellation_policy_disclosure": "Policy clearly displayed."}
        updated_dispute = update_dispute(dispute=self.dispute_id_needs_response, evidence=evidence_payload, submit=True)

        self.assertEqual(updated_dispute["id"], self.dispute_id_needs_response)
        self.assertEqual(updated_dispute["evidence"]["cancellation_policy_disclosure"], "Policy clearly displayed.")
        self.assertEqual(updated_dispute["status"], "under_review")

        db_dispute = DB["disputes"][self.dispute_id_needs_response]
        self.assertEqual(db_dispute["evidence"]["cancellation_policy_disclosure"], "Policy clearly displayed.")
        self.assertEqual(db_dispute["status"], "under_review")

    def test_update_evidence_no_submit_under_review(self):
        original_evidence = copy.deepcopy(DB["disputes"][self.dispute_id_under_review]["evidence"])
        evidence_payload = {"duplicate_charge_explanation": "This is not a duplicate charge."}
        updated_dispute = update_dispute(dispute=self.dispute_id_under_review, evidence=evidence_payload, submit=False)

        self.assertEqual(updated_dispute["id"], self.dispute_id_under_review)
        self.assertEqual(updated_dispute["evidence"]["duplicate_charge_explanation"], "This is not a duplicate charge.")
        self.assertEqual(updated_dispute["evidence"]["uncategorized_text"], original_evidence["uncategorized_text"])
        self.assertEqual(updated_dispute["evidence"]["cancellation_policy_disclosure"], original_evidence["cancellation_policy_disclosure"])
        self.assertEqual(updated_dispute["status"], "under_review")

        db_dispute = DB["disputes"][self.dispute_id_under_review]
        self.assertEqual(db_dispute["evidence"]["duplicate_charge_explanation"], "This is not a duplicate charge.")
        self.assertEqual(db_dispute["status"], "under_review")

    def test_update_evidence_with_submit_under_review(self):
        evidence_payload = {"uncategorized_text": "Further details for review."} # Overwriting existing
        updated_dispute = update_dispute(dispute=self.dispute_id_under_review, evidence=evidence_payload, submit=True)

        self.assertEqual(updated_dispute["id"], self.dispute_id_under_review)
        self.assertEqual(updated_dispute["evidence"]["uncategorized_text"], "Further details for review.")
        self.assertIsNotNone(updated_dispute["evidence"]["cancellation_policy_disclosure"])
        self.assertEqual(updated_dispute["status"], "under_review")

        db_dispute = DB["disputes"][self.dispute_id_under_review]
        self.assertEqual(db_dispute["evidence"]["uncategorized_text"], "Further details for review.")
        self.assertEqual(db_dispute["status"], "under_review")

    def test_update_all_evidence_fields(self):
        evidence_payload = {
            "cancellation_policy_disclosure": "Full policy doc attached.",
            "duplicate_charge_explanation": "Charges are for different services.",
            "uncategorized_text": "Comprehensive summary."
        }
        updated_dispute = update_dispute(dispute=self.dispute_id_needs_response, evidence=evidence_payload, submit=True)

        self.assertEqual(updated_dispute["evidence"]["cancellation_policy_disclosure"], "Full policy doc attached.")
        self.assertEqual(updated_dispute["evidence"]["duplicate_charge_explanation"], "Charges are for different services.")
        self.assertEqual(updated_dispute["evidence"]["uncategorized_text"], "Comprehensive summary.")
        self.assertIsNone(updated_dispute["evidence"]["cancellation_rebuttal"]) # Was None, not updatable by this func
        self.assertEqual(updated_dispute["status"], "under_review")

    def test_update_evidence_with_empty_strings(self):
        evidence_payload = {"uncategorized_text": "", "cancellation_policy_disclosure": ""}
        updated_dispute = update_dispute(dispute=self.dispute_id_needs_response, evidence=evidence_payload, submit=False)
        self.assertEqual(updated_dispute["evidence"]["uncategorized_text"], "")
        self.assertEqual(updated_dispute["evidence"]["cancellation_policy_disclosure"], "")

    def test_update_evidence_sets_field_to_none(self):
        DB["disputes"][self.dispute_id_needs_response]["evidence"]["uncategorized_text"] = "Initial text"
        evidence_payload = {"uncategorized_text": None}
        updated_dispute = update_dispute(dispute=self.dispute_id_needs_response, evidence=evidence_payload, submit=False)
        self.assertIsNone(updated_dispute["evidence"]["uncategorized_text"])
        self.assertIsNone(DB["disputes"][self.dispute_id_needs_response]["evidence"]["uncategorized_text"])

    def test_stage_then_submit_evidence(self):
        staged_evidence_text = "This evidence is staged."
        evidence_payload_stage = {"uncategorized_text": staged_evidence_text}
        staged_dispute = update_dispute(dispute=self.dispute_id_staged_evidence, evidence=evidence_payload_stage, submit=False)

        self.assertEqual(staged_dispute["evidence"]["uncategorized_text"], staged_evidence_text)
        self.assertEqual(staged_dispute["status"], "warning_needs_response")

        submitted_dispute = update_dispute(dispute=self.dispute_id_staged_evidence, evidence=None, submit=True)
        self.assertEqual(submitted_dispute["evidence"]["uncategorized_text"], staged_evidence_text)
        self.assertEqual(submitted_dispute["status"], "warning_needs_response")
        self.assertEqual(DB["disputes"][self.dispute_id_staged_evidence]["status"], "warning_needs_response")

    def test_submit_with_evidence_none_and_no_staged_evidence_changes_status(self):
        updated_dispute = update_dispute(dispute=self.dispute_id_needs_response, evidence=None, submit=True)
        self.assertEqual(updated_dispute["status"], "warning_needs_response")
        self.assertEqual(DB["disputes"][self.dispute_id_needs_response]["status"], "warning_needs_response")
        # Evidence itself should remain as it was (all None for this dispute)
        self.assertIsNone(updated_dispute["evidence"]["uncategorized_text"])


    def test_update_with_empty_evidence_dict_and_submit_true_changes_status(self):
        updated_dispute = update_dispute(dispute=self.dispute_id_needs_response, evidence={}, submit=True)
        self.assertEqual(updated_dispute["status"], "warning_needs_response")
        self.assertEqual(DB["disputes"][self.dispute_id_needs_response]["status"], "warning_needs_response")
        self.assertIsNone(updated_dispute["evidence"]["uncategorized_text"])


    def test_update_with_evidence_none_and_submit_false_is_noop(self):
        original_dispute_copy = copy.deepcopy(DB["disputes"][self.dispute_id_needs_response])
        updated_dispute = update_dispute(dispute=self.dispute_id_needs_response, evidence=None, submit=False)

        self.assertEqual(updated_dispute, original_dispute_copy)
        self.assertEqual(DB["disputes"][self.dispute_id_needs_response], original_dispute_copy)

    def test_metadata_and_other_fields_unchanged(self):
        original_dispute = copy.deepcopy(DB["disputes"][self.dispute_id_needs_response])
        evidence_payload = {"uncategorized_text": "Checking other fields."}
        updated_dispute = update_dispute(dispute=self.dispute_id_needs_response, evidence=evidence_payload, submit=False)

        self.assertEqual(updated_dispute["metadata"], original_dispute["metadata"])
        self.assertEqual(updated_dispute["amount"], original_dispute["amount"])
        self.assertEqual(updated_dispute["currency"], original_dispute["currency"])
        self.assertEqual(updated_dispute["reason"], original_dispute["reason"])
        self.assertEqual(updated_dispute["charge"], original_dispute["charge"])
        self.assertEqual(updated_dispute["payment_intent"], original_dispute["payment_intent"])
        self.assertEqual(updated_dispute["created"], original_dispute["created"])
        self.assertEqual(updated_dispute["is_charge_refundable"], original_dispute["is_charge_refundable"])
        self.assertEqual(updated_dispute["livemode"], original_dispute["livemode"])
        self.assertEqual(updated_dispute["object"], "dispute")

    def test_update_dispute_submit_default_is_false(self):
        evidence_payload = {"uncategorized_text": "Testing submit default."}
        updated_dispute = update_dispute(dispute=self.dispute_id_needs_response, evidence=evidence_payload) # submit omitted

        self.assertEqual(updated_dispute["evidence"]["uncategorized_text"], "Testing submit default.")
        self.assertEqual(updated_dispute["status"], "warning_needs_response")
        self.assertEqual(DB["disputes"][self.dispute_id_needs_response]["status"], "warning_needs_response")

    def test_update_dispute_evidence_default_is_none(self):
        original_evidence = copy.deepcopy(DB["disputes"][self.dispute_id_needs_response]["evidence"])
        updated_dispute = update_dispute(dispute=self.dispute_id_needs_response, submit=True) # evidence omitted

        self.assertEqual(updated_dispute["evidence"], original_evidence)
        self.assertEqual(updated_dispute["status"], "warning_needs_response")
        self.assertEqual(DB["disputes"][self.dispute_id_needs_response]["status"], "warning_needs_response")

    # Error Scenarios - ResourceNotFoundError
    def test_update_non_existent_dispute_raises_resource_not_found_error(self):
        self.assert_error_behavior(
            func_to_call=update_dispute,
            expected_exception_type=ResourceNotFoundError,
            expected_message="Dispute with ID 'dp_non_existent_uds_001' not found.",
            dispute="dp_non_existent_uds_001",
            evidence={"uncategorized_text": "text"},
            submit=False
        )

    # Error Scenarios - InvalidRequestError
    def test_update_dispute_closed_status_raises_invalid_request_error(self):
        self.assert_error_behavior(
            func_to_call=update_dispute,
            expected_exception_type=InvalidRequestError,
            expected_message="Dispute 'dp_cl_uds_001' cannot be updated because its status is 'closed'.",
            dispute=self.dispute_id_closed,
            evidence={"uncategorized_text": "text"},
            submit=False
        )

    def test_update_dispute_won_status_raises_invalid_request_error(self):
        self.assert_error_behavior(
            func_to_call=update_dispute,
            expected_exception_type=InvalidRequestError,
            expected_message="Dispute 'dp_wn_uds_001' cannot be updated because its status is 'won'.",
            dispute=self.dispute_id_won,
            evidence={"uncategorized_text": "text"},
            submit=True
        )

    def test_update_dispute_lost_status_raises_invalid_request_error(self):
        self.assert_error_behavior(
            func_to_call=update_dispute,
            expected_exception_type=InvalidRequestError,
            expected_message="Dispute 'dp_ls_uds_001' cannot be updated because its status is 'lost'.",
            dispute=self.dispute_id_lost,
            evidence={"uncategorized_text": "text"},
            submit=False
        )

    def test_update_evidence_with_invalid_field_type_raises_invalid_request_error(self):
        self.assert_error_behavior(
            func_to_call=update_dispute,
            expected_exception_type=InvalidRequestError,
            expected_message="Invalid evidence structure: Field 'uncategorized_text': Input should be a valid string",
            dispute=self.dispute_id_needs_response,
            evidence={"uncategorized_text": 12345},
            submit=False
        )


    def test_update_dispute_with_empty_string_dispute_id_raises_resource_not_found_error(self):
        self.assert_error_behavior(
            func_to_call=update_dispute,
            expected_exception_type=ResourceNotFoundError,
            expected_message="Dispute with ID '' not found.",
            dispute="",
            evidence={"uncategorized_text": "text"},
            submit=False
        )

    # Error Scenarios - ValidationError (using ValidationError)
    def test_update_dispute_with_non_string_dispute_id_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=update_dispute,
            expected_exception_type=InvalidRequestError,
            expected_message="Dispute ID must be a string.",
            dispute=12345,
            evidence={"uncategorized_text": "text"},
            submit=False
        )

    def test_update_dispute_with_none_dispute_id_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=update_dispute,
            expected_exception_type=InvalidRequestError,
            expected_message="Dispute ID must be a string.",
            dispute=None,
            evidence={"uncategorized_text": "text"},
            submit=False
        )

    def test_update_dispute_with_non_bool_submit_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=update_dispute,
            expected_exception_type=InvalidRequestError,
            expected_message="The 'submit' parameter must be a boolean.",
            dispute=self.dispute_id_needs_response,
            evidence={"uncategorized_text": "text"},
            submit="not_a_bool"
        )

    def test_update_dispute_with_non_dict_evidence_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=update_dispute,
            expected_exception_type=InvalidRequestError,
            expected_message="Evidence, if provided, must be a dictionary.",
            dispute=self.dispute_id_needs_response,
            evidence="not_a_dict",
            submit=False
        )

class TestListDisputes(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB['disputes'] = {} # Disputes are stored by ID, mapping dispute_id to dispute_data
        self.dispute_counter = 0 # Reset for each test to ensure predictable IDs/timestamps

    

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_list_disputes_empty_db(self):
        result = list_disputes()
        self.assertEqual(result['object'], "list")
        self.assertEqual(len(result['data']), 0)
        self.assertFalse(result['has_more'])

    def test_list_disputes_default_limit_and_pagination(self):
        # Create 15 disputes with varying creation times
        # Timestamps are constructed such that higher 'i' is newer
        for i in range(15):
            add_dispute_to_db( 
                charge_id=f"ch_default_{i}",
                created_timestamp=int((datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=i)).timestamp())
            )

        result = list_disputes() # Default limit is 10
        self.assertEqual(result['object'], "list")
        self.assertEqual(len(result['data']), 10)
        self.assertTrue(result['has_more'])

        # Verify structure of a dispute item from the list
        if result['data']:
            item = result['data'][0]
            self.assertIsInstance(item['id'], str)
            self.assertEqual(item["object"], "dispute")
            self.assertIsInstance(item['amount'], int)
            self.assertIsInstance(item['currency'], str)
            self.assertIsInstance(item['status'], str)
            self.assertIsInstance(item['reason'], str)
            self.assertIsInstance(item['charge'], str)
            # payment_intent can be str or None
            self.assertTrue(isinstance(item['payment_intent'], str) or item['payment_intent'] is None)
            self.assertIsInstance(item['created'], int)
            self.assertIsInstance(item['is_charge_refundable'], bool)
            self.assertIsInstance(item['livemode'], bool)
            # metadata can be dict or None
            self.assertTrue(isinstance(item['metadata'], dict) or item['metadata'] is None)

            # Check if newest item is first (dispute with i=14)
            self.assertEqual(result['data'][0]['charge'], "ch_default_14")
            self.assertEqual(result['data'][9]['charge'], "ch_default_5")


    def test_list_disputes_sorting_by_created_descending(self):
        ts_base = int(datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp())
        d1 = add_dispute_to_db( charge_id="ch_sort_1", custom_id="dp_sort_1", created_timestamp=ts_base - 200) # Oldest
        d2 = add_dispute_to_db( charge_id="ch_sort_2", custom_id="dp_sort_2", created_timestamp=ts_base - 100) # Middle
        d3 = add_dispute_to_db( charge_id="ch_sort_3", custom_id="dp_sort_3", created_timestamp=ts_base)       # Newest

        result = list_disputes(limit=3)
        self.assertEqual(len(result['data']), 3)
        self.assertEqual(result['data'][0]['id'], d3['id'])
        self.assertEqual(result['data'][1]['id'], d2['id'])
        self.assertEqual(result['data'][2]['id'], d1['id'])
        self.assertFalse(result['has_more'])

    def test_list_disputes_custom_limit_less_than_total(self):
        for i in range(5):
            add_dispute_to_db( charge_id=f"ch_limit_less_{i}")

        result = list_disputes(limit=3)
        self.assertEqual(len(result['data']), 3)
        self.assertTrue(result['has_more'])

    def test_list_disputes_custom_limit_equal_to_total(self):
        for i in range(5):
            add_dispute_to_db( charge_id=f"ch_limit_equal_{i}")

        result = list_disputes(limit=5)
        self.assertEqual(len(result['data']), 5)
        self.assertFalse(result['has_more'])

    def test_list_disputes_custom_limit_greater_than_total(self):
        for i in range(3):
            add_dispute_to_db( charge_id=f"ch_limit_greater_{i}")

        result = list_disputes(limit=5)
        self.assertEqual(len(result['data']), 3)
        self.assertFalse(result['has_more'])

    def test_list_disputes_limit_one(self):
        add_dispute_to_db(charge_id="ch_limit_one_1", created_timestamp=100)
        add_dispute_to_db(charge_id="ch_limit_one_2", created_timestamp=200) # Newest

        result = list_disputes(limit=1)
        self.assertEqual(len(result['data']), 1)
        self.assertTrue(result['has_more'])
        self.assertEqual(result['data'][0]['charge'], "ch_limit_one_2")


    def test_list_disputes_limit_max_100_less_than_total(self):
        for i in range(105):
            add_dispute_to_db( charge_id=f"ch_limit_100_less_{i}")

        result = list_disputes(limit=100)
        self.assertEqual(len(result['data']), 100)
        self.assertTrue(result['has_more'])

    def test_list_disputes_limit_max_100_equal_to_total(self):
        for i in range(100):
            add_dispute_to_db( charge_id=f"ch_limit_100_equal_{i}")

        result = list_disputes(limit=100)
        self.assertEqual(len(result['data']), 100)
        self.assertFalse(result['has_more'])

    def test_list_disputes_filter_by_charge_id_found(self):
        target_charge_id = "ch_filter_target"
        add_dispute_to_db( charge_id=target_charge_id, custom_id="dp_match_1", created_timestamp=100)
        add_dispute_to_db( charge_id="ch_other_1", custom_id="dp_no_match_1", created_timestamp=150)
        add_dispute_to_db( charge_id=target_charge_id, custom_id="dp_match_2", created_timestamp=200) # Newest matching

        result = list_disputes(charge=target_charge_id)
        self.assertEqual(len(result['data']), 2)
        self.assertTrue(all(d['charge'] == target_charge_id for d in result['data']))
        self.assertEqual(result['data'][0]['id'], "dp_match_2") # Check sorting
        self.assertEqual(result['data'][1]['id'], "dp_match_1")
        self.assertFalse(result['has_more'])

    def test_list_disputes_filter_by_charge_id_not_found(self):
        add_dispute_to_db( charge_id="ch_some_charge")
        result = list_disputes(charge="ch_non_existent")
        self.assertEqual(len(result['data']), 0)
        self.assertFalse(result['has_more'])

    def test_list_disputes_filter_by_payment_intent_id_found(self):
        target_pi_id = "pi_filter_target"
        add_dispute_to_db( charge_id="ch_pi_1", payment_intent_id=target_pi_id, custom_id="dp_pi_match_1", created_timestamp=100)
        add_dispute_to_db( charge_id="ch_pi_2", payment_intent_id="pi_other", custom_id="dp_pi_no_match_1", created_timestamp=150)
        add_dispute_to_db( charge_id="ch_pi_3", payment_intent_id=target_pi_id, custom_id="dp_pi_match_2", created_timestamp=200) # Newest matching
        add_dispute_to_db( charge_id="ch_pi_4", payment_intent_id=None, custom_id="dp_pi_no_match_2", created_timestamp=250)

        result = list_disputes(payment_intent=target_pi_id)
        self.assertEqual(len(result['data']), 2)
        self.assertTrue(all(d['payment_intent'] == target_pi_id for d in result['data']))
        self.assertEqual(result['data'][0]['id'], "dp_pi_match_2") # Check sorting
        self.assertEqual(result['data'][1]['id'], "dp_pi_match_1")
        self.assertFalse(result['has_more'])

    def test_list_disputes_filter_by_payment_intent_id_not_found(self):
        add_dispute_to_db( charge_id="ch_pi_some", payment_intent_id="pi_existing")
        result = list_disputes(payment_intent="pi_non_existent")
        self.assertEqual(len(result['data']), 0)
        self.assertFalse(result['has_more'])

    def test_list_disputes_filter_by_charge_and_payment_intent_found(self):
        target_charge = "ch_both_target"
        target_pi = "pi_both_target"
        add_dispute_to_db( charge_id=target_charge, payment_intent_id=target_pi, custom_id="dp_both_match", created_timestamp=100)
        add_dispute_to_db( charge_id=target_charge, payment_intent_id="pi_other", custom_id="dp_charge_only", created_timestamp=200)
        add_dispute_to_db( charge_id="ch_other", payment_intent_id=target_pi, custom_id="dp_pi_only", created_timestamp=300)

        result = list_disputes(charge=target_charge, payment_intent=target_pi)
        self.assertEqual(len(result['data']), 1)
        self.assertEqual(result['data'][0]['id'], "dp_both_match")
        self.assertFalse(result['has_more'])

    def test_list_disputes_filter_by_charge_and_payment_intent_no_match(self):
        target_charge = "ch_multi_filter_target_c"
        target_pi = "pi_multi_filter_target_pi"
        add_dispute_to_db( charge_id=target_charge, payment_intent_id="pi_other_1")
        add_dispute_to_db( charge_id="ch_other_2", payment_intent_id=target_pi)
        add_dispute_to_db( charge_id="ch_other_3", payment_intent_id="pi_other_3")

        result = list_disputes(charge=target_charge, payment_intent=target_pi)
        self.assertEqual(len(result['data']), 0)
        self.assertFalse(result['has_more'])

    def test_list_disputes_filter_by_charge_id_with_limit_and_pagination(self):
        # This test requires careful setup of created_timestamps to verify sorting within filtered results
        DB['disputes'].clear()
        self.dispute_counter = 0 # Reset counter for this specific setup

        target_charge_id = "ch_filter_pagination"
        base_ts = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create 15 disputes matching the charge, with distinct timestamps
        # disputes_data will store them in creation order (oldest to newest by timestamp)
        disputes_data = []
        for i in range(15):
            ts = int((base_ts + timedelta(minutes=i)).timestamp()) # timestamps[0] is oldest, timestamps[14] is newest
            dispute = add_dispute_to_db( 
                charge_id=target_charge_id,
                custom_id=f"dp_id_{i}",
                created_timestamp=ts
            )
            disputes_data.append(dispute)

        # Add one non-matching dispute to ensure filter works
        add_dispute_to_db( charge_id="ch_other_page_2", custom_id="dp_no_match_page_2", created_timestamp=int((base_ts - timedelta(minutes=1)).timestamp()))

        result = list_disputes(charge=target_charge_id, limit=5)
        self.assertEqual(len(result['data']), 5)
        self.assertTrue(all(d['charge'] == target_charge_id for d in result['data']))
        self.assertTrue(result['has_more'])

        # Expected IDs: newest 5 of the matching disputes
        # disputes_data[14] is newest, disputes_data[10] is 5th newest
        expected_ids = [disputes_data[i]['id'] for i in range(14, 9, -1)] # ids for 14, 13, 12, 11, 10
        returned_ids = [d['id'] for d in result['data']]
        self.assertEqual(returned_ids, expected_ids)

    def test_list_disputes_with_metadata(self):
        meta = {"order_id": "12345", "user_ref": "abc"}
        add_dispute_to_db( charge_id="ch_meta", metadata=meta, custom_id="dp_meta_1", created_timestamp=200)
        add_dispute_to_db( charge_id="ch_no_meta", metadata=None, custom_id="dp_meta_2", created_timestamp=100)

        result = list_disputes(limit=2)

        # Results are sorted by created desc, so dp_meta_1 should be first
        self.assertEqual(result['data'][0]['id'], "dp_meta_1")
        self.assertEqual(result['data'][0]['metadata'], meta)

        self.assertEqual(result['data'][1]['id'], "dp_meta_2")
        self.assertIsNone(result['data'][1]['metadata'])


    def test_list_disputes_payment_intent_can_be_null_in_data(self):
        add_dispute_to_db( charge_id="ch_pi_null_1", payment_intent_id=None, custom_id="dp_pi_is_null", created_timestamp=200)
        add_dispute_to_db( charge_id="ch_pi_null_2", payment_intent_id="pi_is_not_null", custom_id="dp_pi_is_not_null", created_timestamp=100)

        result = list_disputes(limit=2)

        # Results are sorted by created desc
        self.assertEqual(result['data'][0]['id'], "dp_pi_is_null")
        self.assertIsNone(result['data'][0]['payment_intent'])

        self.assertEqual(result['data'][1]['id'], "dp_pi_is_not_null")
        self.assertEqual(result['data'][1]['payment_intent'], "pi_is_not_null")

    # --- Error Handling Tests ---
    def test_list_disputes_invalid_limit_zero(self):
        self.assert_error_behavior(
            func_to_call=list_disputes,
            expected_exception_type=ValidationError,
            expected_message="Limit must be an integer between 1 and 100.",
            limit=0
        )

    def test_list_disputes_invalid_limit_negative(self):
        self.assert_error_behavior(
            func_to_call=list_disputes,
            expected_exception_type=ValidationError,
            expected_message="Limit must be an integer between 1 and 100.",
            limit=-5
        )

    def test_list_disputes_invalid_limit_too_high(self):
        self.assert_error_behavior(
            func_to_call=list_disputes,
            expected_exception_type=ValidationError,
            expected_message="Limit must be an integer between 1 and 100.",
            limit=101
        )

    def test_list_disputes_invalid_limit_type_string(self):
        self.assert_error_behavior(
            func_to_call=list_disputes,
            expected_exception_type=ValidationError,
            expected_message="Limit must be an integer between 1 and 100.",
            limit="not_an_int"
        )

    def test_list_disputes_invalid_charge_type(self):
        self.assert_error_behavior(
            func_to_call=list_disputes,
            expected_exception_type=ValidationError,
            expected_message="Charge must be a string value",
            charge=12345 # Not a string
        )

    def test_list_disputes_invalid_payment_intent_type(self):
        self.assert_error_behavior(
            func_to_call=list_disputes,
            expected_exception_type=ValidationError,
            expected_message="Payment intent must be a string value",
            payment_intent=12345 # Not a string
        )

    def test_add_dispute_with_custom_id(self):
        # Test adding dispute with custom ID
        dispute = add_dispute_to_db(
            charge_id="ch_123",
            custom_id="dp_custom_123"
        )
        self.assertEqual(dispute["id"], "dp_custom_123")
        self.assertEqual(DB['disputes']["dp_custom_123"], dispute)

    def test_add_dispute_without_custom_id(self):
        # Test adding dispute without custom ID
        dispute = add_dispute_to_db(charge_id="ch_123")
        self.assertEqual(dispute["id"], "0")
        self.assertEqual(DB['disputes']["0"], dispute)

    def test_add_multiple_disputes(self):
        # Test adding multiple disputes
        dispute1 = add_dispute_to_db(charge_id="ch_1")
        dispute2 = add_dispute_to_db(charge_id="ch_2")
        dispute3 = add_dispute_to_db(charge_id="ch_3")

        self.assertEqual(dispute1["id"], "0")
        self.assertEqual(dispute2["id"], "1")
        self.assertEqual(dispute3["id"], "2")

    def test_add_dispute_with_all_parameters(self):
        # Test adding dispute with all parameters
        dispute = add_dispute_to_db(
            charge_id="ch_123",
            payment_intent_id="pi_123",
            amount=2000,
            currency="eur",
            status="under_review",
            reason="fraudulent",
            created_timestamp=1234567890,
            metadata={"order_id": "ord_123"},
            is_charge_refundable=True,
            livemode=True
        )

        self.assertEqual(dispute["charge"], "ch_123")
        self.assertEqual(dispute["payment_intent"], "pi_123")
        self.assertEqual(dispute["amount"], 2000)
        self.assertEqual(dispute["currency"], "eur")
        self.assertEqual(dispute["status"], "under_review")
        self.assertEqual(dispute["reason"], "fraudulent")
        self.assertEqual(dispute["created"], 1234567890)
        self.assertEqual(dispute["metadata"], {"order_id": "ord_123"})
        self.assertEqual(dispute["is_charge_refundable"], True)
        self.assertEqual(dispute["livemode"], True)

    def test_add_dispute_with_default_timestamp(self):
        # Test adding dispute with default timestamp
        dispute = add_dispute_to_db(charge_id="ch_123")
        self.assertIsNotNone(dispute["created"])
        self.assertIsInstance(dispute["created"], int)

    def test_add_dispute_with_custom_timestamp(self):
        # Test adding dispute with custom timestamp
        custom_timestamp = 1234567890
        dispute = add_dispute_to_db(
            charge_id="ch_123",
            created_timestamp=custom_timestamp
        )
        self.assertEqual(dispute["created"], custom_timestamp)