"""
Comprehensive tests for YouTube Tool custom error classes.
Tests APIError, ExtractionError, and EnvironmentError custom exceptions.
"""

import unittest
from youtube_tool.SimulationEngine.custom_errors import APIError, ExtractionError, EnvironmentError


class TestAPIError(unittest.TestCase):
    
    def test_api_error_inheritance(self):
        """Test that APIError inherits from Exception."""
        self.assertTrue(issubclass(APIError, Exception))
        
    def test_api_error_instantiation_with_message(self):
        """Test APIError can be instantiated with a message."""
        error_message = "API request failed with status code 404"
        error = APIError(error_message)
        
        self.assertIsInstance(error, APIError)
        self.assertEqual(str(error), error_message)
        
    def test_api_error_instantiation_without_message(self):
        """Test APIError can be instantiated without a message."""
        error = APIError()
        
        self.assertIsInstance(error, APIError)
        self.assertEqual(str(error), "")
        
    def test_api_error_with_multiple_args(self):
        """Test APIError with multiple arguments."""
        error = APIError("API failed", 500, "Internal Server Error")
        
        self.assertIsInstance(error, APIError)
        # All arguments are stored in args tuple
        self.assertEqual(error.args, ("API failed", 500, "Internal Server Error"))
        
    def test_api_error_with_unicode_message(self):
        """Test APIError with unicode characters in message."""
        unicode_message = "API失败: サーバーエラー 🚫"
        error = APIError(unicode_message)
        
        self.assertEqual(str(error), unicode_message)
        
    def test_api_error_raise_and_catch(self):
        """Test raising and catching APIError."""
        error_message = "Connection timeout to YouTube API"
        
        with self.assertRaises(APIError) as context:
            raise APIError(error_message)
            
        caught_error = context.exception
        self.assertIsInstance(caught_error, APIError)
        self.assertEqual(str(caught_error), error_message)
        
    def test_api_error_in_exception_hierarchy(self):
        """Test that APIError can be caught as a generic Exception."""
        try:
            raise APIError("Test error")
        except Exception as e:
            self.assertIsInstance(e, APIError)
            self.assertIsInstance(e, Exception)
        
    def test_api_error_chaining(self):
        """Test APIError with exception chaining."""
        original_error = ValueError("Invalid parameter")
        
        try:
            try:
                raise original_error
            except ValueError as e:
                raise APIError("API call failed due to invalid input") from e
        except APIError as api_error:
            self.assertEqual(str(api_error), "API call failed due to invalid input")
            self.assertIs(api_error.__cause__, original_error)


class TestExtractionError(unittest.TestCase):
    
    def test_extraction_error_inheritance(self):
        """Test that ExtractionError inherits from Exception."""
        self.assertTrue(issubclass(ExtractionError, Exception))
        
    def test_extraction_error_instantiation_with_message(self):
        """Test ExtractionError can be instantiated with a message."""
        error_message = "Failed to extract video data from response"
        error = ExtractionError(error_message)
        
        self.assertIsInstance(error, ExtractionError)
        self.assertEqual(str(error), error_message)
        
    def test_extraction_error_instantiation_without_message(self):
        """Test ExtractionError can be instantiated without a message."""
        error = ExtractionError()
        
        self.assertIsInstance(error, ExtractionError)
        self.assertEqual(str(error), "")
        
    def test_extraction_error_with_json_context(self):
        """Test ExtractionError with JSON parsing context."""
        json_snippet = '{"candidates": [{"content": {...}}'
        error_message = f"Invalid JSON structure: {json_snippet}"
        error = ExtractionError(error_message)
        
        self.assertEqual(str(error), error_message)
        self.assertIn(json_snippet, str(error))
        
    def test_extraction_error_with_xpath_context(self):
        """Test ExtractionError with XPath/parsing context."""
        xpath = "candidates[0].content.parts[2].structuredData"
        error_message = f"Missing required field at path: {xpath}"
        error = ExtractionError(error_message)
        
        self.assertEqual(str(error), error_message)
        self.assertIn(xpath, str(error))
        
    def test_extraction_error_raise_and_catch(self):
        """Test raising and catching ExtractionError."""
        error_message = "Unable to parse YouTube response structure"
        
        with self.assertRaises(ExtractionError) as context:
            raise ExtractionError(error_message)
            
        caught_error = context.exception
        self.assertIsInstance(caught_error, ExtractionError)
        self.assertEqual(str(caught_error), error_message)
        
    def test_extraction_error_with_nested_structure_info(self):
        """Test ExtractionError with information about nested structure failures."""
        structure_info = {
            "expected_path": "candidates[0].content.parts[2].structuredData.multiStepPlanInfo",
            "actual_keys": ["candidates", "error"],
            "response_type": "error_response"
        }
        
        error_message = f"Structure mismatch: {structure_info}"
        error = ExtractionError(error_message)
        
        self.assertIn("Structure mismatch", str(error))
        self.assertIn("expected_path", str(error))


class TestEnvironmentError(unittest.TestCase):
    
    def test_environment_error_inheritance(self):
        """Test that EnvironmentError inherits from Exception."""
        self.assertTrue(issubclass(EnvironmentError, Exception))
        
    def test_environment_error_instantiation_with_message(self):
        """Test EnvironmentError can be instantiated with a message."""
        error_message = "GOOGLE_API_KEY environment variable not set"
        error = EnvironmentError(error_message)
        
        self.assertIsInstance(error, EnvironmentError)
        self.assertEqual(str(error), error_message)
        
    def test_environment_error_instantiation_without_message(self):
        """Test EnvironmentError can be instantiated without a message."""
        error = EnvironmentError()
        
        self.assertIsInstance(error, EnvironmentError)
        self.assertEqual(str(error), "")
        
    def test_environment_error_api_key_missing(self):
        """Test EnvironmentError for missing API key scenarios."""
        error_message = "Google API Key not found. Please create a .env file in the project root with GOOGLE_API_KEY or GEMINI_API_KEY, or set it as an environment variable."
        error = EnvironmentError(error_message)
        
        self.assertEqual(str(error), error_message)
        self.assertIn("GOOGLE_API_KEY", str(error))
        self.assertIn("GEMINI_API_KEY", str(error))
        
    def test_environment_error_live_api_url_missing(self):
        """Test EnvironmentError for missing LIVE_API_URL scenarios."""
        error_message = "Live API URL not found. Please create a .env file in the project root with LIVE_API_URL, or set it as an environment variable."
        error = EnvironmentError(error_message)
        
        self.assertEqual(str(error), error_message)
        self.assertIn("LIVE_API_URL", str(error))
        
    def test_environment_error_raise_and_catch(self):
        """Test raising and catching EnvironmentError."""
        error_message = "Required environment configuration is missing"
        
        with self.assertRaises(EnvironmentError) as context:
            raise EnvironmentError(error_message)
            
        caught_error = context.exception
        self.assertIsInstance(caught_error, EnvironmentError)
        self.assertEqual(str(caught_error), error_message)
        
    def test_environment_error_with_configuration_hints(self):
        """Test EnvironmentError with helpful configuration information."""
        error_message = """Environment setup incomplete:
        1. Set GOOGLE_API_KEY in .env file
        2. Set LIVE_API_URL in .env file
        3. Ensure .env file is in project root
        Example: GOOGLE_API_KEY=your_key_here"""
        
        error = EnvironmentError(error_message)
        
        self.assertIn("Environment setup incomplete", str(error))
        self.assertIn("Example:", str(error))


class TestErrorClassDistinction(unittest.TestCase):
    
    def test_all_errors_are_distinct_classes(self):
        """Test that all custom error classes are distinct."""
        api_error = APIError("API error")
        extraction_error = ExtractionError("Extraction error")
        env_error = EnvironmentError("Environment error")
        
        # Check they are different types
        self.assertNotEqual(type(api_error), type(extraction_error))
        self.assertNotEqual(type(api_error), type(env_error))
        self.assertNotEqual(type(extraction_error), type(env_error))
        
        # But all inherit from Exception
        self.assertIsInstance(api_error, Exception)
        self.assertIsInstance(extraction_error, Exception)
        self.assertIsInstance(env_error, Exception)
        
    def test_error_catching_specificity(self):
        """Test that errors can be caught specifically or generically."""
        errors_to_test = [
            (APIError("API test"), APIError),
            (ExtractionError("Extraction test"), ExtractionError),
            (EnvironmentError("Environment test"), EnvironmentError),
        ]
        
        for error_instance, error_class in errors_to_test:
            # Test specific catching
            try:
                raise error_instance
            except error_class as e:
                self.assertIsInstance(e, error_class)
            except Exception:
                self.fail(f"Should have caught {error_class.__name__} specifically")
                
            # Test generic catching
            try:
                raise error_instance
            except Exception as e:
                self.assertIsInstance(e, error_class)
                self.assertIsInstance(e, Exception)
                
    def test_error_subclass_relationships(self):
        """Test that custom errors don't inherit from each other."""
        # APIError should not be a subclass of the others
        self.assertFalse(issubclass(APIError, ExtractionError))
        self.assertFalse(issubclass(APIError, EnvironmentError))
        
        # ExtractionError should not be a subclass of the others
        self.assertFalse(issubclass(ExtractionError, APIError))
        self.assertFalse(issubclass(ExtractionError, EnvironmentError))
        
        # EnvironmentError should not be a subclass of the others
        self.assertFalse(issubclass(EnvironmentError, APIError))
        self.assertFalse(issubclass(EnvironmentError, ExtractionError))
        
        # But all should be subclasses of Exception
        self.assertTrue(issubclass(APIError, Exception))
        self.assertTrue(issubclass(ExtractionError, Exception))
        self.assertTrue(issubclass(EnvironmentError, Exception))


class TestErrorUsageScenarios(unittest.TestCase):
    
    def test_api_error_scenarios(self):
        """Test realistic APIError usage scenarios."""
        scenarios = [
            "HTTP 500: Internal server error from YouTube API",
            "Request timeout after 30 seconds",
            "Rate limit exceeded: 100 requests per minute",
            "Authentication failed: Invalid API key",
            "Quota exceeded for the current billing period"
        ]
        
        for scenario in scenarios:
            error = APIError(scenario)
            self.assertIsInstance(error, APIError)
            self.assertEqual(str(error), scenario)
            
    def test_extraction_error_scenarios(self):
        """Test realistic ExtractionError usage scenarios."""
        scenarios = [
            "Missing 'candidates' field in API response",
            "Invalid JSON format in response body",
            "Empty execution trace in structured data",
            "Unexpected response structure from Gemini API",
            "Failed to parse video metadata from response"
        ]
        
        for scenario in scenarios:
            error = ExtractionError(scenario)
            self.assertIsInstance(error, ExtractionError)
            self.assertEqual(str(error), scenario)
            
    def test_environment_error_scenarios(self):
        """Test realistic EnvironmentError usage scenarios."""
        scenarios = [
            "GOOGLE_API_KEY not found in environment variables",
            "LIVE_API_URL is not configured",
            ".env file not found in project root",
            "Invalid API key format detected",
            "Environment variable GEMINI_API_KEY is empty"
        ]
        
        for scenario in scenarios:
            error = EnvironmentError(scenario)
            self.assertIsInstance(error, EnvironmentError)
            self.assertEqual(str(error), scenario)
            
    def test_error_context_preservation(self):
        """Test that error context is preserved through the call stack."""
        def level_3():
            raise EnvironmentError("Original environment error")
            
        def level_2():
            try:
                level_3()
            except EnvironmentError as e:
                raise ExtractionError(f"Extraction failed due to: {e}") from e
                
        def level_1():
            try:
                level_2()
            except ExtractionError as e:
                raise APIError(f"API call failed: {e}") from e
                
        try:
            level_1()
        except APIError as final_error:
            # Check the error chain
            self.assertIsInstance(final_error, APIError)
            self.assertIn("API call failed", str(final_error))
            
            # Check the cause chain
            extraction_cause = final_error.__cause__
            self.assertIsInstance(extraction_cause, ExtractionError)
            self.assertIn("Extraction failed due to", str(extraction_cause))
            
            env_cause = extraction_cause.__cause__
            self.assertIsInstance(env_cause, EnvironmentError)
            self.assertIn("Original environment error", str(env_cause))


if __name__ == '__main__':
    unittest.main()
