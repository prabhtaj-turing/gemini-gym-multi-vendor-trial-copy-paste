# TODO: Implement mutation builder using google ADK 
# Where we can provide initial prompt and then agents will generate the mutation one by one for each API function
# At the end, we can open the session in ADK Web to provide more feedback to agents if needed
# It will take very structured prompt and then generate the mutations
# Or maybe take list of examples for input and output field renamings to guide more effectively

# For now, we will use the static changes configs to generate the mutations using static_mutation_builder.py

from .static_mutation_config_builder import StaticMutationConfigBuilder
from .static_mutation_builder import StaticMutationBuilder

__all__ = ['StaticMutationConfigBuilder', 'StaticMutationBuilder']