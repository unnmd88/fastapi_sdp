import enum
import pprint
from collections import abc
from functools import cached_property
from typing import (
    Annotated,
    TypeVar, ClassVar, Type, TypeAlias
)


from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator

from sdp_lib.management_controllers.constants import AllowedControllers


class AllowedManagementEntity(enum.StrEnum):
    set_stage = 'set_stage'
    set_dark = 'set_dark'


class AllowedManagementSources(enum.StrEnum):
    man = 'man'
    central = 'central'


mutable_seq = Annotated[abc.MutableSequence, Field(default=[])]


# class CommandOptions(BaseModel):
#     model_config = ConfigDict(use_enum_values=True)
#
#     alias: Annotated[str | None, Field(default=None)]
#     min_val: int
#     max_val: int
#     special_values: mutable_seq
#     options: mutable_seq
#     sources: mutable_seq
#     default: AllowedManagementSources


def get_stage_range_as_set(
    min_val: int,
    max_val: int,
    collection_type: Type[abc.Collection[int | str]]
) -> abc.Collection[int | str]:
    try:
        return collection_type(num_stage for num_stage in range(min_val, max_val + 1))
    except ValueError:
        return set()


class Services(BaseModel):

    model_config = ConfigDict(use_enum_values=True, frozen=True, arbitrary_types_allowed=True)

    alias: Annotated[str, Field(default=None)]
    values_range: abc.Sequence[int | str]
    values_range_as_set: Annotated[set[int | str], Field(exclude=True, default=set())]
    options: mutable_seq
    sources: mutable_seq
    default_source: AllowedManagementSources

    @computed_field
    @cached_property
    def min_val(self) -> str | int:
        return self.values_range[0]

    @computed_field
    @cached_property
    def max_val(self) -> str | int:
        return self.values_range[-1]



class Stage(Services):

    alias: Annotated[str, Field(default='Фаза')]


T_Services: TypeAlias = Services | Stage


class CommandOptions(BaseModel):

    model_config = ConfigDict(use_enum_values=True, frozen=True, arbitrary_types_allowed=True)


    matches_services: ClassVar = {
        AllowedControllers.SWARCO: {AllowedManagementEntity.set_stage},
        AllowedControllers.POTOK_P: {AllowedManagementEntity.set_stage},
        AllowedControllers.POTOK_S: {AllowedManagementEntity.set_stage},
        AllowedControllers.PEEK: {AllowedManagementEntity.set_stage}
    }

    type_controller: AllowedControllers
    available_services: Annotated[abc.Collection[AllowedManagementEntity | str], Field(default=[])]
    services_entity: abc.MutableMapping[AllowedManagementEntity, Stage | Services]


    # def model_post_init(self, __context) -> None:
    #     self.available_services = self.matches_services[self.type_controller]







swarco_set_stage = Stage(

    values_range=get_stage_range_as_set(0, 8, list),
    values_range_as_set=get_stage_range_as_set(0, 8, set),
    default_source=AllowedManagementSources.central,
    sources=[AllowedManagementSources.central, AllowedManagementSources.man]
)

potok_s_set_stage = Stage(
    values_range=get_stage_range_as_set(0, 128, list),
    values_range_as_set=get_stage_range_as_set(0, 128, set),
    default_source=AllowedManagementSources.central
)

potok_p_set_stage = Stage(
    values_range=get_stage_range_as_set(0, 128, list),
    values_range_as_set=get_stage_range_as_set(0, 128, set),
    default_source=AllowedManagementSources.central
)

peek_set_stage = Stage(
    values_range=get_stage_range_as_set(0, 32, list),
    values_range_as_set=get_stage_range_as_set(0, 32, set),
    default_source=AllowedManagementSources.man,
    sources=[AllowedManagementSources.central, AllowedManagementSources.man]
)


swarco = CommandOptions(
    type_controller=AllowedControllers.SWARCO,
    services_entity={AllowedManagementEntity.set_stage: swarco_set_stage},
    available_services={AllowedManagementEntity.set_stage}
)

potok_s = CommandOptions(
    type_controller=AllowedControllers.POTOK_S,
    services_entity={AllowedManagementEntity.set_stage: potok_s_set_stage},
    available_services={AllowedManagementEntity.set_stage},
)


# T_CommandOptions: TypeAlias = TypeVar('T_CommandOptions', SwarcoOptions, PotokOptions)
T_CommandOptions: TypeAlias = TypeVar('T_CommandOptions', bound=CommandOptions)

# class Commands(BaseModel):
#     available_commands: abc.Collection[AllowedManagementEntity | str]
#     stage_command: Stage


# swarco_set_stage_options = Stage(
#     min_val=0,
#     max_val=8,
#     sources=[AllowedManagementSources.man],
#     default=AllowedManagementSources.central,
#     stages_range=get_stage_range_as_set(0, 8)
# )
#
# potok_s_set_stage_options = Stage(
#     min_val=0,
#     max_val=128,
#     default=AllowedManagementSources.central,
#     stages_range=get_stage_range_as_set(0, 128)
# )
#
# potok_p_set_stage_options = Stage(
#     min_val=0,
#     max_val=128,
#     default=AllowedManagementSources.central,
#     stages_range=get_stage_range_as_set(0, 128)
# )
#
# peek_set_stage_options = Stage(
#     min_val=0,
#     max_val=128,
#     sources=[AllowedManagementSources.central],
#     default=AllowedManagementSources.man,
#     stages_range=get_stage_range_as_set(0, 32)
# )
#
#
# swarco = Commands(
#     available_commands={AllowedManagementEntity.set_stage},
#     stage_command=swarco_set_stage_options
# )


__T_CommandOptions = TypeVar('__T_CommandOptions', bound=CommandOptions)
T_CommandOptions = dict[AllowedControllers, dict[AllowedManagementEntity, __T_CommandOptions]]


all_controllers_services = {
    AllowedControllers.SWARCO: swarco,
    # AllowedControllers.POTOK_S: {
    #     AllowedManagementEntity.set_stage: potok_s_set_stage_options
    # },
    # AllowedControllers.POTOK_P: {
    #     AllowedManagementEntity.set_stage: potok_p_set_stage_options
    # },
    # AllowedControllers.PEEK: {
    #     AllowedManagementEntity.set_stage: peek_set_stage_options
    # },
}

if __name__ == '__main__':
    print(swarco)
    pprint.pprint(swarco.model_dump_json())