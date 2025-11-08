import pytest
from common_utils.email_validator_custom import validate_email_custom
from common_utils.custom_errors import InvalidEmailError

def test_valid_email():
    """Test that a valid email address passes validation."""
    email = "test.email@example.com"
    assert validate_email_custom(email) == email

def test_invalid_input_type():
    """Test that a non-string input raises an InvalidEmailError."""
    with pytest.raises(InvalidEmailError, match="Invalid input: not a string"):
        validate_email_custom(123)

def test_email_too_long():
    """Test that an email exceeding 512 characters raises an InvalidEmailError."""
    long_email = "a" * 501 + "@example.com"
    with pytest.raises(InvalidEmailError, match="Invalid email: exceeds 512 characters"):
        validate_email_custom(long_email)

def test_missing_at_symbol():
    """Test that an email without an '@' symbol raises an InvalidEmailError."""
    with pytest.raises(InvalidEmailError, match="Invalid email: missing '@' symbol"):
        validate_email_custom("test.email.example.com")

def test_multiple_at_symbols():
    """Test that an email with multiple '@' symbols raises an InvalidEmailError."""
    with pytest.raises(InvalidEmailError, match="Invalid email: more than one '@' symbol"):
        validate_email_custom("test@email@example.com")

def test_missing_local_part():
    """Test that an email with a missing local part raises an InvalidEmailError."""
    with pytest.raises(InvalidEmailError, match="Invalid email: missing local part"):
        validate_email_custom("@example.com")

def test_local_part_starts_with_dot():
    """Test that an email with a local part starting with a dot raises an InvalidEmailError."""
    with pytest.raises(InvalidEmailError, match="Invalid email: local part starts or ends with a dot"):
        validate_email_custom(".test@example.com")

def test_local_part_ends_with_dot():
    """Test that an email with a local part ending with a dot raises an InvalidEmailError."""
    with pytest.raises(InvalidEmailError, match="Invalid email: local part starts or ends with a dot"):
        validate_email_custom("test.@example.com")

def test_local_part_consecutive_dots():
    """Test that an email with consecutive dots in the local part raises an InvalidEmailError."""
    with pytest.raises(InvalidEmailError, match="Invalid email: local part has consecutive dots"):
        validate_email_custom("test..email@example.com")

def test_invalid_domain_part():
    """Test that an email with an invalid domain part raises an InvalidEmailError."""
    with pytest.raises(InvalidEmailError, match="Invalid email: domain part is invalid"):
        validate_email_custom("test@example")

def test_domain_starts_with_hyphen():
    """Test that an email with a domain starting with a hyphen raises an InvalidEmailError."""
    with pytest.raises(InvalidEmailError, match="Invalid email: domain starts or ends with a hyphen"):
        validate_email_custom("test@-example.com")

def test_domain_ends_with_hyphen():
    """Test that an email with a domain ending with a hyphen raises an InvalidEmailError."""
    with pytest.raises(InvalidEmailError, match="Invalid email: domain starts or ends with a hyphen"):
        validate_email_custom("test@example.com-")

def test_domain_consecutive_dots():
    """Test that an email with consecutive dots in the domain raises an InvalidEmailError."""
    with pytest.raises(InvalidEmailError, match="Invalid email: domain part has consecutive dots"):
        validate_email_custom("test@example..com")

def test_invalid_format():
    """Test that an email with a format not matching the regex raises an InvalidEmailError."""
    with pytest.raises(InvalidEmailError, match="Invalid email: format doesn't match standard pattern"):
        validate_email_custom("test@.com")
def test_invalid_format_with_whitespace():
    """Test that an email with a format not matching the regex raises an InvalidEmailError."""
    with pytest.raises(InvalidEmailError, match="Invalid email: format doesn't match standard pattern"):
        validate_email_custom("test@.com ")

def test_invalid_format_with_whitespace_and_at_symbol():
    """Test that an email with a format not matching the regex raises an InvalidEmailError."""
    with pytest.raises(InvalidEmailError, match="Invalid email: more than one '@' symbol"):
        validate_email_custom("test@.com @example.com")

def test_invalid_format_with_whitespace_before_symbol():
    """Test that an email with a format not matching the regex raises an InvalidEmailError."""
    with pytest.raises(InvalidEmailError, match="Invalid email: missing local part"):
        validate_email_custom(" "*500+"@example.com")

def test_invalid_format_email():
    """Test that an email with a format not matching the regex raises an InvalidEmailError."""
    with pytest.raises(InvalidEmailError, match="Invalid email: format doesn't match standard pattern"):
        validate_email_custom("test@.com")