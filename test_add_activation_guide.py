
import os
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from APIs.ces_system_activation.ces_system_activation import add_activation_guide_from_pdf
from APIs.ces_system_activation.SimulationEngine import db

def test_add_activation_guide_from_pdf():
    """
    Tests that add_activation_guide_from_pdf correctly adds a new guide to the DB
    and that the content is the mock data when running in a test environment.
    """
    # 1. Create a dummy PDF for testing
    pdf_path = "/tmp/test_guide.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "This is a test PDF for the activation guide.")
    c.save()

    # 2. Get the initial state of the activation guides
    initial_guides = db.DB.get("activationGuides", {}).copy()

    # 3. Call the function to add the PDF content to the DB
    result = add_activation_guide_from_pdf(pdf_path)

    # 4. Assert that the function returns a success message
    assert result["status"] == "success"
    assert result["message"] == "Activation guide 'test_guide' added successfully."

    # 5. Get the final state of the activation guides
    final_guides = db.DB.get("activationGuides", {})

    # 6. Assert that a new guide has been added
    assert len(final_guides) == len(initial_guides) + 1
    assert "test_guide" in final_guides

    # 7. Assert that the content of the new guide is the mock data
    new_guide = final_guides["test_guide"]
    assert new_guide["title"] == "Test Guide"
    assert new_guide["appliesTo"] == "General Test"
    assert new_guide["introduction"] == "This is a test entry."

    # 8. Clean up the dummy PDF file
    os.remove(pdf_path)

    # 9. Restore the original DB state
    db.DB["activationGuides"] = initial_guides
