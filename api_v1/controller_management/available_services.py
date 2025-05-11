import enum
from collections.abc import Collection
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

    stages_range: set[int] | list[int] | tuple[int]
    alias: str = 'Фаза'


def get_stage_range_as_set(min_val: int, max_val: int) -> set:
    try:
        return {num_stage for num_stage in range(min_val, max_val)}
    except ValueError:
        return set()



class Commands(BaseModel):
    available_commands: Collection[AllowedManagementEntity | str]
    stage_command: Stage


swarco_set_stage_options = Stage(
    min_val=0,
    max_val=8,
    sources=[AllowedManagementSources.man],
    default=AllowedManagementSources.central,
    stages_range=get_stage_range_as_set(0, 8)
)

potok_s_set_stage_options = Stage(
    min_val=0,
    max_val=128,
    default=AllowedManagementSources.central,
    stages_range=get_stage_range_as_set(0, 128)
)

potok_p_set_stage_options = Stage(
    min_val=0,
    max_val=128,
    default=AllowedManagementSources.central,
    stages_range=get_stage_range_as_set(0, 128)
)

peek_set_stage_options = Stage(
    min_val=0,
    max_val=128,
    sources=[AllowedManagementSources.central],
    default=AllowedManagementSources.man,
    stages_range=get_stage_range_as_set(0, 32)
)


swarco = Commands(
    available_commands={AllowedManagementEntity.set_stage},
    stage_command=swarco_set_stage_options
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