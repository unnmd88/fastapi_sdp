import pytest

from api_v1.controller_management import available_services


@pytest.mark.parametrize(
    'min_val, max_val, collection_type, expected',
    [
        (0, 8, list, list(i for i in range(8 + 1))),
        (0, 8, set, set(i for i in range(8 + 1))),
        (0, 8, tuple, tuple(i for i in range(8 + 1))),
        (0, 128, list, list(i for i in range(128 + 1))),
        (0, 32, set, set(i for i in range(32 + 1))),
    ]
)
def test_get_stage_range(min_val, max_val, collection_type, expected):
    assert available_services.get_stage_range(min_val, max_val, collection_type) == expected


def test_set_stage_swarco():
    swarco_stages = [i for i in range(9)]
    swarco_stages_as_set = set(swarco_stages)
    default_source = available_services.AllowedManagementSources.central
    sources = [
        available_services.AllowedManagementSources.central,
        available_services.AllowedManagementSources.man
    ]

    assert available_services.swarco_set_stage.values_range == swarco_stages
    assert available_services.swarco_set_stage.values_range_as_set == swarco_stages_as_set
    assert available_services.swarco_set_stage.default_source == default_source
    assert available_services.swarco_set_stage.sources == sources
    assert available_services.swarco_set_stage.command_name == 'Фаза'
    assert available_services.swarco_set_stage.min_val == 0
    assert available_services.swarco_set_stage.max_val == 8

def test_set_stage_potok_s():
    stages = [i for i in range(128 + 1)]
    stages_as_set = set(stages)
    default_source = available_services.AllowedManagementSources.central
    sources = [
        available_services.AllowedManagementSources.central,
    ]

    assert available_services.potok_s_set_stage.values_range == stages
    assert available_services.potok_s_set_stage.values_range_as_set == stages_as_set
    assert available_services.potok_s_set_stage.default_source == default_source
    assert available_services.potok_s_set_stage.sources == sources
    assert available_services.potok_s_set_stage.command_name == 'Фаза'
    assert available_services.potok_s_set_stage.min_val == 0
    assert available_services.potok_s_set_stage.max_val == 128

def test_set_stage_potok_p():
    stages = [i for i in range(128 + 1)]
    stages_as_set = set(stages)
    default_source = available_services.AllowedManagementSources.central
    sources = [
        available_services.AllowedManagementSources.central,
    ]

    assert available_services.potok_p_set_stage.values_range == stages
    assert available_services.potok_p_set_stage.values_range_as_set == stages_as_set
    assert available_services.potok_p_set_stage.default_source == default_source
    assert available_services.potok_p_set_stage.sources == sources
    assert available_services.potok_p_set_stage.command_name == 'Фаза'
    assert available_services.potok_p_set_stage.min_val == 0
    assert available_services.potok_p_set_stage.max_val == 128

def test_set_stage_peek():
    stages = [i for i in range(32 + 1)]
    stages_as_set = set(stages)
    default_source = available_services.AllowedManagementSources.man
    sources = [
        available_services.AllowedManagementSources.central,
        available_services.AllowedManagementSources.man,
    ]

    assert available_services.peek_set_stage.values_range == stages
    assert available_services.peek_set_stage.values_range_as_set == stages_as_set
    assert available_services.peek_set_stage.default_source == default_source
    assert available_services.peek_set_stage.sources == sources
    assert available_services.peek_set_stage.command_name == 'Фаза'
    assert available_services.peek_set_stage.min_val == 0
    assert available_services.peek_set_stage.max_val == 32