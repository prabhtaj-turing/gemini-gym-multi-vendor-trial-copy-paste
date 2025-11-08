from .. import create_diagram
from ..SimulationEngine.custom_errors import InvalidInputError, MermaidSyntaxError
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestCreateDiagram(BaseTestCaseWithErrorHandler):
    def test_create_diagram_success(self):
        """
        Tests that a valid Mermaid diagram can be created successfully.
        """
        valid_diagram = "graph TD; A-->B;"
        result = create_diagram(valid_diagram)
        self.assertEqual(result, "Mermaid diagram created successfully.")

    def test_create_diagram_invalid_syntax_fails(self):
        """
        Tests that creating a diagram with invalid syntax fails and returns an error.
        """
        invalid_diagram = "invalid_diagram_type_that_does_not_exist\n    A --> B"
        with self.assertRaises(MermaidSyntaxError) as cm:
            create_diagram(invalid_diagram)
        self.assertIn("Invalid diagram type", str(cm.exception))

    def test_create_diagram_prohibited_styling_fails(self):
        """
        Tests that diagrams with prohibited styling (:::) fail validation.
        """
        invalid_diagram = "graph TD\n    A:::someclass --> B"
        with self.assertRaises(MermaidSyntaxError) as cm:
            create_diagram(invalid_diagram)
        self.assertIn("Custom styling with ':::' is not allowed", str(cm.exception))

    def test_create_diagram_incomplete_graph_fails(self):
        """
        Tests that incomplete graph diagrams fail validation.
        """
        invalid_diagram = "graph"  # Missing direction
        with self.assertRaises(MermaidSyntaxError) as cm:
            create_diagram(invalid_diagram)
        self.assertIn("must specify direction", str(cm.exception))

    def test_create_diagram_empty(self):
        """
        Tests that an empty string input raises InvalidInputError.
        """
        with self.assertRaises(InvalidInputError) as cm:
            create_diagram("")
        self.assertEqual(str(cm.exception), "No content provided.")

    def test_create_diagram_invalid_type(self):
        """
        Tests that a non-string input raises InvalidInputError.
        """
        with self.assertRaises(InvalidInputError) as cm:
            create_diagram(123)
        self.assertEqual(str(cm.exception), "Content must be a string.")

    def test_create_diagram_complex_success(self):
        """
        Tests a more complex but valid diagram.
        """
        # NOTE: Indentation is important for the diagram to be valid.
        complex_diagram = """
            sequenceDiagram
                participant Alice
                participant Bob
                Alice->>John: Hello John, how are you?
                loop Healthcheck
                    John->>John: Fight against hypochondria
                end
                Note right of John: Rational thoughts<br/>prevail...
                John-->>Alice: Great!
                John->>Bob: How about you?
                Bob-->>John: Jolly good!
        """
        result = create_diagram(complex_diagram)
        self.assertEqual(result, "Mermaid diagram created successfully.")
