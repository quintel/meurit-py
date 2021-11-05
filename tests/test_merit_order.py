'''Tests for MeritOrder'''
# pylint: disable=import-error disable=redefined-outer-name disable=missing-function-docstring disable=invalid-name

import pytest

from meurit.merit_order import MeritOrder

@pytest.fixture
def must_run_values():
    return {'key': ':agriculture_chp_engine_network_gas', 'marginal_costs': 81.34086561,
        'output_capacity_per_unit': 1.01369863, 'number_of_units': 3023.581081, 'availability': 0.97,
        'fixed_costs_per_unit': 116478.4738, 'fixed_om_costs_per_unit': 13062.47379,
        'load_profile': 'tests/fixtures/dummy_config/load_profiles/fake_curve.csv',
        'full_load_hours': 3980.424144}


def test_merit_instance():
    mo = MeritOrder()
    assert mo.merit_order("to_s") == '<#Merit::Order (0 producers, 0 users, 0 flex, 0 price-sensitives)>'

def test_add_participant(must_run_values):
    mo = MeritOrder()

    mo.add_participant(participant='MustRunProducer', **must_run_values)

    assert mo.merit_order("to_s")  == '<#Merit::Order (1 producers, 0 users, 0 flex, 0 price-sensitives)>'
    assert mo.merit_order("participants")("first")("to_s") == f'#<Merit::MustRunProducer {must_run_values["key"][1:]}>'
    assert mo.merit_order("participants")("first")("full_load_hours") == must_run_values["full_load_hours"]


def test_add_user():
    user_values = {'key': ':total_demand',
        'load_profile': 'tests/fixtures/dummy_config/load_profiles/fake_curve.csv',
        'total_consumption': 417946498897.5582}

    mo = MeritOrder()

    mo.add_user(**user_values)

    assert mo.merit_order("to_s")  == '<#Merit::Order (0 producers, 1 users, 0 flex, 0 price-sensitives)>'
    assert mo.merit_order("participants")("first")("to_s") == f'#<Merit::User::TotalConsumption {user_values["key"][1:]}>'


def test_calculate_and_price_curve(must_run_values):
    mo = MeritOrder()

    # Add demand
    user_values = {'key': ':total_demand',
        'load_profile': 'tests/fixtures/dummy_config/load_profiles/fake_curve.csv',
        'total_consumption': 417946498897.5582}
    mo.add_user(**user_values)

    # Add supply
    mo.add_participant(participant='MustRunProducer', **must_run_values)

    mo.calculate()
    pc = mo.price_curve()
    assert isinstance(pc, list)
    assert len(pc) == 8760
