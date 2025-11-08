# APIs/google_chat/tests/test_utils_default_page_size.py

import pytest
import sys
import os

# Add the parent directory to the path so we can import from the APIs folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_chat.SimulationEngine.utils import default_page_size


class TestDefaultPageSize:
    """Comprehensive test suite for default_page_size function."""

    def test_none_input(self):
        """Test that None input returns default value of 100."""
        result = default_page_size(None)
        assert result == 100

    def test_zero_input(self):
        """Test that zero input returns default value of 100."""
        result = default_page_size(0)
        assert result == 100

    def test_negative_input(self):
        """Test that negative input returns default value of 100."""
        result = default_page_size(-1)
        assert result == 100
        
        result = default_page_size(-10)
        assert result == 100
        
        result = default_page_size(-999)
        assert result == 100

    def test_positive_valid_input(self):
        """Test that positive valid input returns the same value."""
        result = default_page_size(1)
        assert result == 1
        
        result = default_page_size(50)
        assert result == 50
        
        result = default_page_size(100)
        assert result == 100
        
        result = default_page_size(500)
        assert result == 500
        
        result = default_page_size(1000)
        assert result == 1000

    def test_over_maximum_input(self):
        """Test that input over maximum (1000) is capped at 1000."""
        result = default_page_size(1001)
        assert result == 1000
        
        result = default_page_size(1500)
        assert result == 1000
        
        result = default_page_size(9999)
        assert result == 1000

    def test_boundary_values(self):
        """Test boundary values around the limits."""
        # Test around zero
        result = default_page_size(0)
        assert result == 100
        
        result = default_page_size(1)
        assert result == 1
        
        # Test around maximum
        result = default_page_size(999)
        assert result == 999
        
        result = default_page_size(1000)
        assert result == 1000
        
        result = default_page_size(1001)
        assert result == 1000

    def test_type_validation_non_integer(self):
        """Test that non-integer types raise TypeError."""
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size("100")
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(100.5)
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size([100])
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size({"value": 100})

    def test_boolean_values_handled_as_integers(self):
        """Test that boolean values are handled as integers (Python behavior)."""
        # In Python, bool is a subclass of int, so True=1 and False=0
        result = default_page_size(True)
        assert result == 1
        
        result = default_page_size(False)
        assert result == 100  # False=0, which gets converted to default 100

    def test_type_validation_none_allowed(self):
        """Test that None is specifically allowed and doesn't raise TypeError."""
        # This should not raise an exception
        result = default_page_size(None)
        assert result == 100

    def test_return_type(self):
        """Test that function always returns an integer."""
        result = default_page_size(None)
        assert isinstance(result, int)
        
        result = default_page_size(50)
        assert isinstance(result, int)
        
        result = default_page_size(1500)
        assert isinstance(result, int)

    def test_return_value_range(self):
        """Test that return value is always within expected range."""
        # Test various inputs to ensure returned value is always 1-1000
        test_values = [None, -999, -1, 0, 1, 50, 100, 500, 1000, 1001, 9999]
        
        for val in test_values:
            result = default_page_size(val)
            assert 1 <= result <= 1000, f"Return value {result} for input {val} is not in range [1, 1000]"

    def test_consistent_behavior(self):
        """Test that function behavior is consistent across multiple calls."""
        # Test idempotency - same input should always give same output
        assert default_page_size(None) == default_page_size(None)
        assert default_page_size(50) == default_page_size(50)
        assert default_page_size(1500) == default_page_size(1500)

    def test_edge_case_very_large_numbers(self):
        """Test behavior with very large numbers."""
        result = default_page_size(999999)
        assert result == 1000
        
        result = default_page_size(2**31 - 1)  # Max 32-bit signed integer
        assert result == 1000

    def test_edge_case_very_small_numbers(self):
        """Test behavior with very small numbers."""
        result = default_page_size(-999999)
        assert result == 100
        
        result = default_page_size(-2**31)  # Min 32-bit signed integer
        assert result == 100

    def test_google_chat_api_compliance(self):
        """Test specific Google Chat API pagination standards."""
        # Default should be 100 when not specified
        assert default_page_size(None) == 100
        
        # Maximum should be 1000 
        assert default_page_size(2000) == 1000
        
        # Invalid values should default to 100
        assert default_page_size(0) == 100
        assert default_page_size(-1) == 100
        
        # Valid range should be preserved
        for val in [1, 10, 50, 100, 250, 500, 1000]:
            assert default_page_size(val) == val

    def test_documentation_examples(self):
        """Test all examples from function docstring."""
        # Examples from docstring
        assert default_page_size(None) == 100
        assert default_page_size(0) == 100
        assert default_page_size(50) == 50
        assert default_page_size(1500) == 1000
        assert default_page_size(-10) == 100

    # --- Additional Edge Case Tests for Better Coverage ---

    def test_edge_case_exactly_at_boundaries(self):
        """Test exact boundary values for maximum coverage."""
        # Test exactly at the boundary where behavior changes
        assert default_page_size(0) == 100      # Exactly at zero boundary
        assert default_page_size(1) == 1        # Exactly at minimum valid
        assert default_page_size(1000) == 1000  # Exactly at maximum
        assert default_page_size(1001) == 1000  # Exactly one over maximum

    def test_edge_case_floating_point_integers(self):
        """Test floating point numbers that are effectively integers."""
        # These should raise TypeError even though they represent integers
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(100.0)
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(0.0)
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(-1.0)

    def test_edge_case_complex_types(self):
        """Test complex Python types that should raise TypeError."""
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(complex(100, 0))
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(object())
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(lambda x: x)

    def test_edge_case_empty_containers(self):
        """Test empty containers that should raise TypeError."""
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size([])
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size({})
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(set())
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(tuple())

    def test_edge_case_string_representations(self):
        """Test string representations of numbers."""
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size("100")
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size("0")
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size("-1")
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size("")

    def test_edge_case_unicode_strings(self):
        """Test unicode string representations."""
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size("１００")  # Full-width unicode digits
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size("١٠٠")   # Arabic numerals

    def test_edge_case_numpy_like_objects(self):
        """Test objects that might behave like numbers but aren't integers."""
        class MockNumber:
            def __int__(self):
                return 100
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(MockNumber())

    def test_edge_case_subclass_of_int(self):
        """Test subclasses of int that should still work."""
        class MyInt(int):
            pass
        
        # These should work since they are subclasses of int
        assert default_page_size(MyInt(50)) == 50
        assert default_page_size(MyInt(1500)) == 1000
        assert default_page_size(MyInt(0)) == 100

    def test_edge_case_negative_boundary_values(self):
        """Test negative values at boundaries."""
        assert default_page_size(-1) == 100      # Exactly -1
        assert default_page_size(-999999) == 100 # Very large negative
        assert default_page_size(-2**63) == 100  # Min 64-bit integer

    def test_edge_case_positive_boundary_values(self):
        """Test positive values at boundaries."""
        assert default_page_size(1) == 1         # Minimum valid
        assert default_page_size(999) == 999     # Just below maximum
        assert default_page_size(1000) == 1000   # Exactly maximum
        assert default_page_size(1001) == 1000   # Just above maximum
        assert default_page_size(2**63 - 1) == 1000  # Max 64-bit integer

    def test_edge_case_system_limits(self):
        """Test system-specific integer limits."""
        import sys
        
        # Test maximum and minimum values for the system
        max_int = sys.maxsize
        min_int = -sys.maxsize - 1
        
        assert default_page_size(max_int) == 1000
        assert default_page_size(min_int) == 100

    def test_edge_case_boolean_edge_cases(self):
        """Test boolean edge cases more thoroughly."""
        # Test that bool values are treated as integers
        assert default_page_size(True) == 1   # True == 1
        assert default_page_size(False) == 100  # False == 0, which becomes 100

    def test_edge_case_none_vs_falsey(self):
        """Test that None is handled differently from other falsey values."""
        # None should return 100
        assert default_page_size(None) == 100
        
        # But other falsey values should raise TypeError
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size("")
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size([])

    def test_edge_case_type_checking_robustness(self):
        """Test that type checking is robust against various inputs."""
        # Test various non-integer types
        non_integer_types = [
            "string", "", "0", "100", "abc",
            3.14, 0.0, -1.5, float('inf'), float('-inf'), float('nan'),
            [], [1, 2, 3], {}, {"key": "value"}, set(), {1, 2, 3},
            tuple(), (1, 2, 3), complex(1, 2), object(), lambda x: x,
            bytes([1, 2, 3]), bytearray([1, 2, 3])
        ]
        
        for value in non_integer_types:
            with pytest.raises(TypeError, match="pageSize must be an integer"):
                default_page_size(value)

    def test_edge_case_immutable_sequences(self):
        """Test immutable sequence types."""
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size((100,))
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(tuple([100]))

    def test_edge_case_mutable_sequences(self):
        """Test mutable sequence types."""
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size([100])
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size([100, 200])

    def test_edge_case_mapping_types(self):
        """Test mapping types."""
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size({"pageSize": 100})
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size({})

    def test_edge_case_set_types(self):
        """Test set types."""
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size({100})
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(set())

    def test_edge_case_callable_objects(self):
        """Test callable objects."""
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(lambda: 100)
        
        def my_func():
            return 100
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(my_func)

    def test_edge_case_special_numbers(self):
        """Test special numeric values."""
        import math
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(math.pi)
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(math.e)
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(float('inf'))
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(float('-inf'))
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(float('nan'))

    def test_edge_case_custom_objects(self):
        """Test custom objects that might have numeric-like behavior."""
        class NumericLike:
            def __init__(self, value):
                self.value = value
            
            def __int__(self):
                return self.value
        
        with pytest.raises(TypeError, match="pageSize must be an integer"):
            default_page_size(NumericLike(100))

    def test_edge_case_inheritance_edge_cases(self):
        """Test inheritance edge cases."""
        class IntSubclass(int):
            pass
        
        # IntSubclass should work
        assert default_page_size(IntSubclass(50)) == 50
        assert default_page_size(IntSubclass(1500)) == 1000
        
        # bool is already a subclass of int, so just test with bool values
        assert default_page_size(True) == 1
        assert default_page_size(False) == 100

    def test_edge_case_performance_edge_cases(self):
        """Test performance edge cases with very large numbers."""
        # Test that function handles very large numbers efficiently
        large_numbers = [2**30, 2**31, 2**32, 2**63, 2**64 - 1]
        
        for num in large_numbers:
            result = default_page_size(num)
            assert result == 1000, f"Expected 1000 for {num}, got {result}"

    def test_edge_case_memory_edge_cases(self):
        """Test memory edge cases."""
        # Test that function doesn't have memory issues with large numbers
        result = default_page_size(2**1000)  # Extremely large number
        assert result == 1000

    def test_edge_case_error_message_consistency(self):
        """Test that error messages are consistent."""
        error_message = "pageSize must be an integer."
        
        with pytest.raises(TypeError, match=error_message):
            default_page_size("100")
        
        with pytest.raises(TypeError, match=error_message):
            default_page_size(3.14)
        
        with pytest.raises(TypeError, match=error_message):
            default_page_size([])

    def test_edge_case_function_signature_compliance(self):
        """Test that function signature matches expected behavior."""
        import inspect
        
        sig = inspect.signature(default_page_size)
        assert str(sig) == "(ps: Optional[int]) -> int"
        
        # Test that the function accepts the expected types
        assert default_page_size(None) == 100
        assert default_page_size(100) == 100 