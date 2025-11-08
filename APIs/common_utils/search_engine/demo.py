from common_utils.print_log import print_log
# https://colab.research.google.com/drive/1yd4H7qKaEFgWTbLUs0ur3KSJnX-kFic7?usp=sharing

import os
import sys
import json

# Ensure the project root is in the Python path
pythonpath = os.environ.get("PYTHONPATH", "")
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)
if pythonpath:
    os.environ["PYTHONPATH"] = pythonpath + os.pathsep + project_root
else:
    os.environ["PYTHONPATH"] = project_root

print_log(f"Project root added to PYTHONPATH: {project_root}")

from gmail.SimulationEngine.db import DB
from gmail.Users import createUser
from gmail.Users.Messages import list as list_messages, send as send_message
from gmail.SimulationEngine.search_engine import search_engine_manager

def setup_data():
    """Set up a user with some messages directly."""
    createUser(userId="me", profile={"emailAddress": "me@example.com"})

    messages = [
            {
                "threadId": "thread-a", "labelIds": ["INBOX"], "snippet": "Exciting news about our upcoming project launch.",
                "internalDate": "1679999000000", "sender": "Alice <alice@example.com>", "recipient": "me <me@example.com>",
                "subject": "Project Phoenix Update", "body": "Full body of the project update email.",
            },
            {
                "threadId": "thread-b", "labelIds": ["INBOX", "IMPORTANT"], "snippet": "Your weekly digest is here.",
                "internalDate": "1679998000000", "sender": "Newsletter <newsletter@example.com>", "recipient": "me <me@example.com>",
                "subject": "Weekly Newsletter", "body": "This newsletter contains important information about financial markets.",
            },
            {
                "threadId": "thread-a", "labelIds": ["INBOX"], "snippet": "Re: Project Phoenix Update",
                "internalDate": "1679999100000", "sender": "Bob <bob@example.com>", "recipient": "Alice <alice@example.com>",
                "subject": "Re: Phoenix Status", "body": "Thanks for the info on the project!",
            },
            {
                "threadId": "thread-c", "labelIds": ["INBOX"], "snippet": "Logistics for the offsite meeting",
                "internalDate": "1680000000000", "sender": "carol@example.com", "recipient": "me@example.com>",
                "subject": "Logistics for the offsite", "body": "Hi team, let's coordinate logistics for our upcoming off-site event. We need to finalize the travel arrangements.",
            },
            {
                "threadId": "thread-d", "labelIds": ["INBOX", "URGENT"], "snippet": "Critical security alert",
                "internalDate": "1680001000000", "sender": "security@example.com", "recipient": "me@example.com",
                "subject": "Critical Security Alert", "body": "A critical vulnerability has been detected. We need you to take immediate action and update your security credentials.",
            },
            {
                "threadId": "thread-e", "labelIds": ["INBOX"], "snippet": "Travel Itinerary for Offsite",
                "internalDate": "1680002000000", "sender": "travel-agent@example.com", "recipient": "me@example.com",
                "subject": "Your Travel Itinerary", "body": "Here are the details for your upcoming trip. The travel arrangements are confirmed.",
            },
            {
                "threadId": "thread-f", "labelIds": ["INBOX"], "snippet": "Finalizing the travel plans",
                "internalDate": "1680003000000", "sender": "carol@example.com", "recipient": "me@example.com",
                "subject": "Finalizing Travel", "body": "Just a quick note to say that we are finalizing the travel plans for the off-site event. More details to follow.",
            },
    ]
    
    for msg_data in messages:
        msg_data["id"] = send_message(userId="me", msg=msg_data)["id"]

def print_results(title, query, expectation, results, expected_ids, indent="    "):
    """Helper function to print search results in a readable, indented format."""
    print_log(indent + "-" * 70)
    print_log(f"{indent}Strategy: {title}")
    print_log(f"{indent}Query: \"{query}\"")
    print_log(f"{indent}Expectation: {expectation}")
    
    found_messages = results.get("messages", [])
    num_results = len(found_messages)
    print_log(f"{indent}Result: Found {num_results} results.")
    
    found_ids = {msg['id'] for msg in found_messages}
    for msg in found_messages:
        subject = msg.get('subject', 'N/A')
        print_log(f"{indent}  - ID: {msg['id']}, Subject: {subject}")

    assert set(expected_ids) == found_ids, f"[{title}] Expected IDs {expected_ids}, but found {found_ids}"
    print_log(f"{indent}Assertion Passed: Found the expected message IDs.")
    print_log(indent + "-" * 70)
    print_log()

def demo_strategy_comparison():
    """Mirrors 'test_side_by_side_for_typo_query'."""
    print_log("=" * 80)
    print_log("DEMO 1: SIDE-BY-SIDE FOR TYPO QUERY")
    print_log("=" * 80)
    
    query = "'weekly news later'" 

    # Keyword search
    search_engine_manager.override_strategy_for_engine(strategy_name="keyword")
    result_keyword = list_messages(userId="me", q=query)
    print_results("Keyword Search", query, "Should not find results for a typo.", result_keyword, expected_ids=[])

    # Fuzzy search (using default settings)
    fuzzy_engine = search_engine_manager.override_strategy_for_engine(strategy_name="fuzzy")
    fuzzy_engine.config.score_cutoff = 70
    result_fuzzy = list_messages(userId="me", q=query)
    expected_ids = [msg["id"] for msg in DB["users"]["me"]["messages"].values() if msg["subject"] == "Weekly Newsletter"]
    print_results("Fuzzy Search", query, "Should find the 'Newsletter' message despite the typo.", result_fuzzy, expected_ids=expected_ids)
    
    # Semantic search (using default settings)
    semantic_engine = search_engine_manager.override_strategy_for_engine(strategy_name="semantic")
    semantic_engine.config.score_threshold = 0.90
    result_semantic = list_messages(userId="me", q=query)
    expected_ids = [msg["id"] for msg in DB["users"]["me"]["messages"].values() if msg["subject"] == "Weekly Newsletter"]
    print_results("Semantic Search", query, "Should understand the user's intent and find the 'Newsletter' message.", result_semantic, expected_ids=expected_ids)
    

def demo_semantic_query():
    """Mirrors 'test_side_by_side_for_semantic_query'."""
    print_log("=" * 80)
    print_log("DEMO 2: SIDE-BY-SIDE FOR SEMANTIC QUERY")
    print_log("=" * 80)
    
    query = "'urgent warning'"

    # Keyword search
    search_engine_manager.override_strategy_for_engine(strategy_name="keyword")
    result_keyword = list_messages(userId="me", q=query)
    print_results("Keyword Search", query, "Should not find semantically related terms.", result_keyword, expected_ids=[])

    # Fuzzy search
    fuzzy_engine = search_engine_manager.override_strategy_for_engine(strategy_name="fuzzy")
    fuzzy_engine.config.score_cutoff = 70
    result_fuzzy = list_messages(userId="me", q=query)
    print_results(f"Fuzzy Search (Cutoff: {fuzzy_engine.config.score_cutoff})", query, "Should not find semantically related terms.", result_fuzzy, expected_ids=[])

    # Semantic search
    semantic_engine = search_engine_manager.override_strategy_for_engine(strategy_name="semantic")
    semantic_engine.config.score_threshold = 0.85
    result_semantic = list_messages(userId="me", q=query)
    expected_ids = [msg["id"] for msg in DB["users"]["me"]["messages"].values() if msg["subject"] == "Critical Security Alert"]
    print_results( f"Semantic Search (Threshold: {semantic_engine.config.score_threshold})", query, "Should find the 'Critical Security Alert' message.", result_semantic, expected_ids=expected_ids)
    

def demo_fuzzy_cutoff():
    """Mirrors 'test_fuzzy_search_cutoff_impact'."""
    print_log("=" * 80)
    print_log("DEMO 3: FUZZY SEARCH CUTOFF IMPACT")
    print_log("=" * 80)

    query = "'travel arangements'" # Typo

    # Lenient (lower) cutoff
    fuzzy_engine_lenient = search_engine_manager.override_strategy_for_engine(strategy_name="fuzzy")
    fuzzy_engine_lenient.config.score_cutoff = 70
    result_lenient = list_messages(userId="me", q=query)
    expected_ids = [msg["id"] for msg in DB["users"]["me"]["messages"].values() if msg["subject"] in ["Logistics for the offsite", "Your Travel Itinerary", "Finalizing Travel"]]
    print_results( f"Fuzzy Search (Lenient Cutoff: {fuzzy_engine_lenient.config.score_cutoff})", query, "A lenient cutoff should find multiple loosely related messages.", result_lenient, expected_ids=expected_ids)

    # Strict (higher) cutoff
    fuzzy_engine_strict = search_engine_manager.override_strategy_for_engine(strategy_name="fuzzy")
    fuzzy_engine_strict.config.score_cutoff = 90
    result_strict = list_messages(userId="me", q=query)
    print_results( f"Fuzzy Search (Strict Cutoff: {fuzzy_engine_strict.config.score_cutoff})", query, "A strict cutoff should find no results for this typo.", result_strict, expected_ids=[])

def demo_semantic_threshold():
    """Mirrors 'test_semantic_search_threshold_impact'."""
    print_log("=" * 80)
    print_log("DEMO 4: SEMANTIC SEARCH THRESHOLD IMPACT")
    print_log("=" * 80)
    
    query = "'travel planning for the offsite'"

    # Lenient (lower) threshold
    semantic_engine_lenient = search_engine_manager.override_strategy_for_engine(strategy_name="semantic")
    semantic_engine_lenient.config.score_threshold = 0.8
    result_lenient = list_messages(userId="me", q=query)
    expected_ids = [msg["id"] for msg in DB["users"]["me"]["messages"].values() if msg["subject"] in ["Logistics for the offsite", "Finalizing Travel", "Your Travel Itinerary"]]
    print_results(f"Semantic Search (Lenient Threshold: {semantic_engine_lenient.config.score_threshold})", query, "A lenient threshold should find multiple conceptually related messages.", result_lenient, expected_ids=expected_ids)

    # Strict (higher) threshold
    semantic_engine_strict = search_engine_manager.override_strategy_for_engine(strategy_name="semantic")
    semantic_engine_strict.config.score_threshold = 0.95
    result_strict = list_messages(userId="me", q=query)
    print_results(f"Semantic Search (Strict Threshold: {semantic_engine_strict.config.score_threshold})", query, "A strict threshold requires a very strong conceptual match, finding no results.", result_strict, expected_ids=[])

if __name__ == "__main__":
    setup_data()
    demo_strategy_comparison()
    demo_semantic_query()
    demo_fuzzy_cutoff()
    demo_semantic_threshold()
