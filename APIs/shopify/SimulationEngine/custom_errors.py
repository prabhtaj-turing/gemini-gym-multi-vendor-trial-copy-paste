"""
Custom error classes for the Shopify API Simulation.

These errors are designed to be raised by the API tool implementations
to indicate specific failure conditions. They are simple type markers
inheriting from a common base error.
"""

class ShopifySimulationError(Exception):
    """
    Base class for all custom exceptions in the Shopify API simulation.
    Allows catching all simulation-specific errors with a single except block.
    """
    pass

class ShopifyApiError(ShopifySimulationError):
    """Generic error for issues encountered while interacting with the Shopify API (e.g., authentication, rate limits, server errors)."""
    pass

class NotFoundError(ShopifySimulationError):
    """Raised if a requested resource is not found."""
    pass

class InvalidInputError(ShopifySimulationError): # General input error, can be base for more specific ones
    """Raised when an input to an API tool is malformed, invalid, or missing."""
    pass

class InvalidQueryError(InvalidInputError): # More specific input error
    """Raised if the search `query` syntax is invalid or unsupported."""
    pass

class InvalidParameterError(InvalidInputError): # More specific input error
    """Raised if any of the filter parameters are invalid (e.g., malformed dates, invalid IDs)."""
    pass

class InvalidDateTimeFormatError(InvalidInputError):
    """Raised when a datetime string is not in the expected format."""
    pass

class AuthenticationError(ShopifyApiError):
    """Raised if authentication with the Shopify API fails (e.g., invalid API key, secret, or access token)."""
    pass

class PermissionError(ShopifyApiError): # General permission error, can be base for more specific ones
    """Raised if the authenticated application or user does not have the necessary permissions."""
    pass

class ResourceNotFoundError(NotFoundError): # More specific not found
    """Raised if a specific resource referenced by an ID (e.g., a product ID in `ids` or a `collection_id`) is not found on Shopify."""
    pass

class RateLimitError(ShopifyApiError):
    """Raised if the Shopify API rate limit has been exceeded by too many requests in a short period."""
    pass

class OrderProcessingError(ShopifyApiError):
    """If the order cannot be processed (e.g., cancelled, closed, reopened due to its current state or business rules)."""
    pass

class RefundError(ShopifyApiError):
    """If refund processing fails as part of an operation (e.g., invalid amount, currency mismatch, issues with the payment gateway)."""
    pass

class ShopifyInvalidInputError(InvalidInputError): # Used by Draft Order, Order Edit tools
    """If the provided data for a Shopify operation (e.g. draft_order, order edit) is invalid, incomplete, or violates business rules."""
    pass

class ShopifyPermissionError(PermissionError): # Used by Draft Order, Order Edit, Product, Customer Address tools
    """If the API credentials do not have permission for a specific Shopify action."""
    pass

class ShopifyNotFoundError(NotFoundError): # Used by Draft Order, Order Edit, Product, Customer Address tools
    """If a specific Shopify resource (e.g., draft order, product variant, calculated order) is not found."""
    pass

class ShopifyStateError(ShopifyApiError): # e.g., for draft order completion
    """Raised if a resource is not in a valid state for the requested operation (e.g., trying to complete an already completed draft order)."""
    pass

class ShopifyActionError(ShopifyApiError): # e.g., for sending an invoice
    """Raised if a specific action on a resource fails for reasons other than state or input (e.g., error sending an email)."""
    pass

class ShopifyGraphQLError(ShopifyApiError): # For GraphQL specific issues
    """Raised for errors during GraphQL API calls, potentially including user errors detailing issues with specific fields."""
    pass

class ShopifyInventoryError(ShopifyApiError):
    """Raised for inventory-related issues, such as insufficient stock or problems restocking."""
    pass

class ShopifyOrderEditCommitError(ShopifyApiError):
    """Raised if committing staged order changes from a CalculatedOrder to the actual Order fails."""
    pass

class ShopifyReturnError(ShopifyApiError): # For Return processing errors
    """Raised if a return cannot be created or processed (e.g., items not fulfillable, already returned, or order not in a state that allows returns)."""
    pass

class ShopifyExchangeError(ShopifyApiError): # For Exchange processing errors
    """Raised if an exchange cannot be created or processed (e.g., items not fulfilled, order not in valid state, or business rule violations)."""
    pass

class ShopifyPaymentError(ShopifyApiError): # For payment processing issues
    """Raised if processing a financial transaction (e.g., for a refund or new transaction) fails."""
    pass

class SchemaIntrospectionError(ShopifySimulationError):
    """
    Raised if there is an error during the (simulated) GraphQL schema
    introspection process.
    """
    pass

class AdminAPIAccessError(ShopifySimulationError):
    """
    Raised if there's an issue accessing or authenticating with the
    (simulated) Shopify Admin API.
    """
    pass

class SearchServiceError(ShopifySimulationError):
    """
    Raised if the (simulated) shopify.dev search service is unavailable
    or returns an error.
    """
    pass

class NoResultsFoundError(NotFoundError): # Can consolidate with general NotFoundError or keep separate if contextually different
    """
    Raised if a search operation yields no relevant results for the given query.
    Specifically for `search_dev_docs` if no documentation is found.
    """
    pass

class DocumentationServiceError(ShopifySimulationError):
    """
    Raised if there's a general failure in communicating with the (simulated)
    documentation service or a catastrophic error preventing any documents
    from being processed.
    """
    pass

class InvalidApiNameError(InvalidInputError): # Can consolidate
    """
    Raised if the provided 'api' argument to the `get_started` tool is not
    one of the valid API names (e.g., admin, functions, hydrogen).
    """
    pass

class InformationRetrievalError(ShopifySimulationError):
    """
    Raised if a tool fails to retrieve the necessary information.
    Specifically for `get_started` if it fails to fetch the getting started
    details for the specified API.
    """
    pass

class ValidationError(ShopifySimulationError):
    """
    Raised when input arguments to a function or API endpoint fail validation
    (e.g., incorrect type, format, value, or missing required fields).
    """
    pass
