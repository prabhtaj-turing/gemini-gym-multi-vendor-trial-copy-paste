from dataclasses import dataclass
from typing import Callable, List, Optional, Type
from pydantic import BaseModel
from google_home.SimulationEngine.models import CommandName, TraitName, StateName


StateUpdateFn = Callable[[dict, BaseModel], None]


@dataclass
class CommandSpec:
    trait: TraitName
    op: CommandName
    values_model: Type[BaseModel]
    target_states: List[StateName]
    handler: Optional[StateUpdateFn] = None
    stateless: bool = False


