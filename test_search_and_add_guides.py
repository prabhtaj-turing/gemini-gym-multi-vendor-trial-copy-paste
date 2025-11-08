
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from APIs.ces_system_activation.ces_system_activation import add_activation_guide_from_pdf, search_activation_guides
from APIs.ces_system_activation.SimulationEngine import db
import json

def test_search_existing_guides():
    """
    Tests that search_activation_guides can find and return existing data from the DB.
    """
    # Query for an existing guide
    query = "modem setup"
    result = search_activation_guides(query)

    # Assert that the result contains the expected guide
    assert result is not None
    assert "answer" in result
    answer = json.loads(result["answer"])
    assert isinstance(answer, list)
    assert len(answer) > 0
    guide = json.loads(answer[0])
    assert guide["title"] == "Self-Installation Guide for Your NetMaster XG6 Modem"

def test_search_after_adding_pdf():
    """
    Tests that search_activation_guides can find a new guide after it has been added from a PDF.
    """
    # 1. Store the initial state of the activation guides
    initial_guides = db.DB.get("activationGuides", {}).copy()

    # 2. Create a dummy PDF with unique content
    pdf_path = "/tmp/custom_guide.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "This is a custom guide about activating a new widget.")
    c.save()

    # 3. Add the new guide from the PDF
    add_activation_guide_from_pdf(pdf_path)

    # 4. Search for the newly added guide
    query = "custom guide widget"
    result = search_activation_guides(query)

    # 5. Assert that the search result contains the new guide
    assert result is not None
    assert "answer" in result
    assert "I have no information" not in result["answer"]
    answer = json.loads(result["answer"])
    assert isinstance(answer, list)
    assert len(answer) > 0
    guide = json.loads(answer[0])
    assert guide["title"] == "Custom Guide"
    assert "custom guide" in guide["introduction"].lower()


    # 6. Clean up the dummy PDF file
    os.remove(pdf_path)

    # 7. Restore the original DB state
    db.DB["activationGuides"] = initial_guides
