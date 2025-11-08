import unittest
import json
import pytest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.models import (
    GoogleHomeDB,
    DeviceState,
    StateName,
    DeviceInfo,
    TraitName,
    DeviceType,
    MutateTraitCommand,
    CommandName,
    TogglesModes,
    ModesSetting,
)
from ..SimulationEngine.db import DB, restore_default_data


class TestDatabaseValidation(BaseTestCaseWithErrorHandler):
    """
    Validate the google_home sample database against Pydantic models,
    mirroring the airline test structure.
    """

    def test_initial_db_state_validation(self):
        """
        Validate the default Google Home DB shipped with the repo.
        """
        restore_default_data()
        snapshot = json.loads(json.dumps(DB))
        try:
            GoogleHomeDB.model_validate(snapshot)
        except Exception as e:
            self.fail(f"Default DB state validation failed: {e}")

    def test_db_module_harmony(self):
        """
        The DB module's in-memory state must conform to GoogleHomeDB after setup.
        """
        restore_default_data()
        try:
            GoogleHomeDB.model_validate(DB)
        except Exception as e:
            self.fail(f"DB module data structure validation failed after setUp: {e}")

    # Edge-case validator tests for state validation
    def test_device_state_invalid_state_name(self):
        with pytest.raises(Exception):
            DeviceState(name="unknownState", value=True)  # type: ignore[arg-type]

    def test_device_state_wrong_type_for_dict(self):
        with pytest.raises(Exception):
            DeviceState(name=StateName.CURRENT_MODES, value=[1, 2, 3])

    def test_device_state_wrong_type_for_list(self):
        with pytest.raises(Exception):
            DeviceState(name=StateName.SCHEDULES, value={})

    def test_device_info_state_not_allowed_by_traits(self):
        with pytest.raises(Exception):
            DeviceInfo(
                id="d1",
                names=["Device"],
                types=[DeviceType.LIGHT],
                traits=[TraitName.ON_OFF],
                room_name="R",
                structure="S",
                toggles_modes=[],
                device_state=[DeviceState(name=StateName.BRIGHTNESS, value=0.5)],
            )

    def test_mutate_trait_command_invalid_command_for_trait(self):
        with pytest.raises(Exception):
            MutateTraitCommand(trait=TraitName.ON_OFF, command_names=[CommandName.SET_BRIGHTNESS])

    def test_state_value_ranges_and_types(self):
        # brightness must be float and within [0,1]
        with pytest.raises(Exception):
            DeviceState(name=StateName.BRIGHTNESS, value="abc")
        with pytest.raises(Exception):
            DeviceState(name=StateName.BRIGHTNESS, value=2.0)
        DeviceState(name=StateName.BRIGHTNESS, value=0.5)

        # openPercent in [0,100]
        with pytest.raises(Exception):
            DeviceState(name=StateName.OPEN_PERCENT, value=-1)
        with pytest.raises(Exception):
            DeviceState(name=StateName.OPEN_PERCENT, value=101)
        DeviceState(name=StateName.OPEN_PERCENT, value=50.0)

        # currentVolume int [0,100]
        with pytest.raises(Exception):
            DeviceState(name=StateName.CURRENT_VOLUME, value=150)
        with pytest.raises(Exception):
            DeviceState(name=StateName.CURRENT_VOLUME, value="loud")
        DeviceState(name=StateName.CURRENT_VOLUME, value=30)

        # fanSpeed int [0,100]
        with pytest.raises(Exception):
            DeviceState(name=StateName.FAN_SPEED, value=-5)
        with pytest.raises(Exception):
            DeviceState(name=StateName.FAN_SPEED, value="fast")
        DeviceState(name=StateName.FAN_SPEED, value=66)

        # humiditySetting int [0,100]
        with pytest.raises(Exception):
            DeviceState(name=StateName.HUMIDITY_SETTING, value=101)
        DeviceState(name=StateName.HUMIDITY_SETTING, value=45)

        # dict and list types
        with pytest.raises(Exception):
            DeviceState(name=StateName.ACTIVE_TOGGLES, value=[])
        with pytest.raises(Exception):
            DeviceState(name=StateName.SCHEDULES, value={})
        DeviceState(name=StateName.ACTIVE_TOGGLES, value={})
        DeviceState(name=StateName.SCHEDULES, value=[])

    def test_device_info_current_modes_valid(self):
        modes = [
            TogglesModes(id="washCycle", names=["Wash Cycle"], settings=[
                ModesSetting(id="normal", names=["Normal"]),
                ModesSetting(id="delicate", names=["Delicate"]),
            ]),
            TogglesModes(id="rinse", names=["Rinse"], settings=[
                ModesSetting(id="quick", names=["Quick"]),
            ]),
        ]
        # Keys must match toggles_modes ids; values are not validated here
        DeviceInfo(
            id="d1",
            names=["Device"],
            types=[DeviceType.LIGHT],
            traits=[TraitName.MODES],
            room_name="R",
            structure="S",
            toggles_modes=modes,
            device_state=[DeviceState(name=StateName.CURRENT_MODES, value={"washCycle": "normal"})],
        )

    def test_device_info_current_modes_invalid_key(self):
        modes = [
            TogglesModes(id="washCycle", names=["Wash Cycle"], settings=[
                ModesSetting(id="normal", names=["Normal"]),
            ]),
        ]
        with pytest.raises(Exception):
            DeviceInfo(
                id="d1",
                names=["Device"],
                types=[DeviceType.LIGHT],
                traits=[TraitName.MODES],
                room_name="R",
                structure="S",
                toggles_modes=modes,
                device_state=[DeviceState(name=StateName.CURRENT_MODES, value={"spin": "fast"})],
            )


if __name__ == '__main__':
    unittest.main()

