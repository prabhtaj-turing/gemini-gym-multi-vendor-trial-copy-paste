import os
import shutil
import pytest
from types import SimpleNamespace

from common_utils.search_engine.engine import EngineManager
from gdrive.SimulationEngine.search_engine import service_adapter
from common_utils.search_engine.models import EngineDefinition
from common_utils.search_engine.strategies import WhooshSearchStrategy

# A simple dummy strategy class for testing
class DummyStrategy:
    def __init__(self, name):
        self.name = name

# Subclass EngineManager to inject custom instances mapping and required service_adapter
class DummyEngineManager(EngineManager):
    def __init__(self, engine_definitions, instances_map):
        self._instances_map = instances_map
        self._test_engine_definitions = engine_definitions
        # Pass a dummy service name. The important part is that it's a string.
        super().__init__(service_name="gdrive_test", service_adapter=service_adapter)

    def _create_instances(self):
        return self._instances_map

    def initialize_engines(self):
        self.engine_definitions = self._test_engine_definitions
        self.engines = {}
        for definition in self.engine_definitions:
            self.engines[definition.id] = self.instances[
                definition.strategy_name
            ]


def test_create_and_initialize_engines():
    instances_map = {
        's1': DummyStrategy('s1'),
        's2': DummyStrategy('s2'),
    }
    definitions = [
        EngineDefinition(id='e1', strategy_name='s1'),
        EngineDefinition(id='e2', strategy_name='s2'),
    ]
    manager = DummyEngineManager(definitions, instances_map)
    assert manager.instances == instances_map
    assert manager.engines == {'e1': instances_map['s1'], 'e2': instances_map['s2']}


def test_get_engine_and_strategy_instance():
    instances_map = {'s1': DummyStrategy('s1')}
    definitions = [EngineDefinition(id='e1', strategy_name='s1')]
    manager = DummyEngineManager(definitions, instances_map)
    # existing engine
    assert manager.get_engine('e1') is instances_map['s1']
    # non-existing engine returns None
    assert manager.get_engine('unknown') is None
    # get strategy instance
    assert manager.get_strategy_instance('s1') is instances_map['s1']


def test_override_strategy_for_engine_and_all():
    instances_map = {'s1': DummyStrategy('s1'), 's2': DummyStrategy('s2')}
    definitions = [
        EngineDefinition(id='e1', strategy_name='s1'),
        EngineDefinition(id='e2', strategy_name='s2'),
    ]
    manager = DummyEngineManager(definitions, instances_map)
    # override single engine
    returned = manager.override_strategy_for_engine('s1', 'e2')
    assert returned is instances_map['s1']
    assert manager.engines['e2'] is instances_map['s1']
    # override all engines
    result = manager.override_strategy_for_all_engines('s2')
    assert all(engine is instances_map['s2'] for engine in result.values())
    # invalid strategy raises ValueError
    with pytest.raises(ValueError):
        manager.override_strategy_for_engine('invalid', 'e1')

