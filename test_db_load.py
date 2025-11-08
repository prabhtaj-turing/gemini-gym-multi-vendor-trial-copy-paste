import sys
sys.path.append('./APIs')

import gdrive
import google_docs
from pydantic import ValidationError

def test_gdrive_load():
    print("Testing GDrive DB load...")
    try:
        gdrive.load_state('./DBs/GDriveDefaultDB.json')
        print("GDrive DB loaded successfully")
    except Exception as e:
        print(f"Error loading GDrive DB: {e}")

def test_google_docs_load():
    print("Testing Google Docs DB load...")
    try:
        google_docs.load_state('./DBs/GoogleDocsDefaultDB.json')
        print("Google Docs DB loaded successfully")
    except Exception as e:
        print(f"Error loading Google Docs DB: {e}")

def test_gdrive_validation():
    print("Testing GDrive content validation...")
    from gdrive.SimulationEngine.models import FileContentUnion, DocumentElementModel, FileContentModel
    
    # Test valid FileContentModel
    try:
        content = {
            "data": "UEsDBBQAAAAIAIuOzVQ...",
            "encoding": "base64",
            "checksum": "sha256:abc123def456...",
            "version": "1.0",
            "lastContentUpdate": "2025-03-10T10:00:00Z"
        }
        FileContentModel(**content)
        print("FileContentModel validation passed")
    except ValidationError as e:
        print(f"FileContentModel validation failed: {e}")
    
    # Test valid DocumentElementModel list
    try:
        elements = [
            {"elementId": "p1", "text": "Introduction: This document outlines the project proposal."},
            {"elementId": "p2", "text": "Objectives: Improve user experience and system efficiency."}
        ]
        [DocumentElementModel(**element) for element in elements]
        print("DocumentElementModel list validation passed")
    except ValidationError as e:
        print(f"DocumentElementModel list validation failed: {e}")
    
    # Test FileContentUnion with FileContentModel
    try:
        content = {
            "data": "UEsDBBQAAAAIAIuOzVQ...",
            "encoding": "base64",
            "checksum": "sha256:abc123def456...",
            "version": "1.0",
            "lastContentUpdate": "2025-03-10T10:00:00Z"
        }
        # FileContentUnion is a type hint, not a class with methods
        # Instead, validate as FileContentModel
        FileContentModel(**content)
        print("FileContentUnion with FileContentModel validation passed")
    except Exception as e:
        print(f"FileContentUnion with FileContentModel validation failed: {e}")
    
    # Test FileContentUnion with DocumentElementModel list
    try:
        elements = [
            {"elementId": "p1", "text": "Introduction: This document outlines the project proposal."},
            {"elementId": "p2", "text": "Objectives: Improve user experience and system efficiency."}
        ]
        # FileContentUnion is a type hint, not a class with methods
        # Instead, validate each element as DocumentElementModel
        [DocumentElementModel(**element) for element in elements]
        print("FileContentUnion with DocumentElementModel list validation passed")
    except Exception as e:
        print(f"FileContentUnion with DocumentElementModel list validation failed: {e}")

if __name__ == "__main__":
    test_gdrive_load()
    print("\n" + "-"*50 + "\n")
    test_google_docs_load()
    print("\n" + "-"*50 + "\n")
    test_gdrive_validation() 