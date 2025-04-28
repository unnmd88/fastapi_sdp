import enum
from typing import (
    MutableSequence,
    Annotated, TypeVar
)

from pydantic import BaseModel, Field, ConfigDict

from sdp_lib.management_controllers.constants import AllowedControllers


class AllowedManagementEntity(enum.StrEnum):
    set_stage = 'set_stage'
    set_dark = 'set_dark'


class AllowedManagementSources(enum.StrEnum):
    man = 'man'
    central = 'central'


mutable_seq = Annotated[MutableSequence, Field(default=[])]


class CommandOptions(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    alias: Annotated[str | None, Field(default=None)]
    min_val: int
    max_val: int
    special_values: mutable_seq
    options: mutable_seq
    sources: mutable_seq
    default: AllowedManagementSources





class Stage(CommandOptions):
    alias: str = 'Фаза'


swarco_set_stage_options = Stage(
    min_val=0,
    max_val=8,
    sources=[AllowedManagementSources.man],
    default=AllowedManagementSources.central
)

potok_s_set_stage_options = Stage(
    min_val=0,
    max_val=128,
    default=AllowedManagementSources.central
)

potok_p_set_stage_options = Stage(
    min_val=0,
    max_val=128,
    default=AllowedManagementSources.central
)

peek_set_stage_options = Stage(
    min_val=0,
    max_val=128,
    sources=[AllowedManagementSources.central],
    default=AllowedManagementSources.man
)


__T_CommandOptions = TypeVar('__T_CommandOptions', bound=CommandOptions)
T_CommandOptions = dict[AllowedControllers, dict[AllowedManagementEntity, __T_CommandOptions]]


all_controllers_services = {
    AllowedControllers.SWARCO: {
        AllowedManagementEntity.set_stage: swarco_set_stage_options
    },
    AllowedControllers.POTOK_S: {
        AllowedManagementEntity.set_stage: potok_s_set_stage_options
    },
    AllowedControllers.POTOK_P: {
        AllowedManagementEntity.set_stage: potok_p_set_stage_options
    },
    AllowedControllers.PEEK: {
        AllowedManagementEntity.set_stage: peek_set_stage_options
    },
}