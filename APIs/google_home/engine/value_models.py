from typing import Tuple, Optional, Literal
from pydantic import BaseModel, Field, conint, confloat, constr, model_validator


class NoValues(BaseModel):
    values: Tuple[str, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def _ensure_empty(self) -> "NoValues":
        if self.values and len([v for v in self.values if v is not None and str(v) != ""]) > 0:
            raise ValueError("This command does not accept any values.")
        return self


class SingleFloat01(BaseModel):
    values: Tuple[confloat(ge=0.0, le=1.0)]


class SinglePercent(BaseModel):
    values: Tuple[confloat(ge=0.0, le=100.0)]


class SingleLevel1to5(BaseModel):
    values: Tuple[conint(ge=1, le=5)]


class SingleDeltaMinus3to3(BaseModel):
    values: Tuple[conint(ge=-3, le=3)]

    @model_validator(mode="after")
    def _non_zero(self) -> "SingleDeltaMinus3to3":
        if self.values[0] == 0:
            raise ValueError("Ambiguous amount cannot be zero.")
        return self


class SingleFloat(BaseModel):
    values: Tuple[confloat()]


class TemperatureWithUnit(BaseModel):
    # [temperature, unit]
    values: Tuple[confloat(), Literal["C", "F", "celsius", "fahrenheit", "Celsius", "Fahrenheit"]]


class DeltaWithUnit(BaseModel):
    # [delta, unit]
    values: Tuple[confloat(), Literal["C", "F", "celsius", "fahrenheit", "Celsius", "Fahrenheit"]]


class LevelWithUnit(BaseModel):
    # [level(1..5), unit]
    values: Tuple[conint(ge=1, le=5), Literal["C", "F", "celsius", "fahrenheit", "Celsius", "Fahrenheit"]]


class ModeOnly(BaseModel):
    values: Tuple[constr(min_length=1)]


class ModeIdAndValue(BaseModel):
    # [mode_id, mode_value]
    values: Tuple[constr(min_length=1), constr(min_length=0)]


class ModeWithUnit(BaseModel):
    # [mode, unit]
    values: Tuple[constr(min_length=1), Literal["C", "F", "celsius", "fahrenheit", "Celsius", "Fahrenheit"]]


class ModeAndTemperature(BaseModel):
    # [mode, temperature]
    values: Tuple[constr(min_length=1), constr(min_length=1)]


class ModeTempWithUnit(BaseModel):
    # [mode, temperature, unit]
    values: Tuple[constr(min_length=1), constr(min_length=1), Literal["C", "F", "celsius", "fahrenheit", "Celsius", "Fahrenheit"]]


class ToggleSettingValues(BaseModel):
    # [toggle_id, true|false]
    values: Tuple[constr(min_length=1), Literal["true", "false", "True", "False"]]


class SingleSlug(BaseModel):
    values: Tuple[constr(min_length=1)]


class AppKey(BaseModel):
    values: Tuple[constr(min_length=1)]


class FanSpeedText(BaseModel):
    values: Tuple[Literal["low", "medium", "high"]]


class LightEffectOnly(BaseModel):
    values: Tuple[Literal["sleep", "wake", "colorLoop", "pulse"]]


class LightEffectWithDuration(BaseModel):
    # [effect, duration_seconds]
    values: Tuple[Literal["sleep", "wake", "colorLoop", "pulse"], conint(ge=1)]


class VolumeLevel(BaseModel):
    values: Tuple[conint(ge=0, le=100)]


class NonEmptyMessage(BaseModel):
    values: Tuple[constr(min_length=1)]


