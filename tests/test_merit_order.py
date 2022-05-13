'''Tests for MeritOrder'''
# pylint: disable=import-error disable=redefined-outer-name disable=missing-function-docstring disable=invalid-name

import re
import pytest
from pathlib import Path

from meurit.merit_order import MeritLockedException, MeritOrder, convert_to_ruby_hash_string, participants
from meurit.merit_order.source import Source

@pytest.fixture
def must_run_values():
    return {'key': ':agriculture_chp_engine_network_gas', 'marginal_costs': 81.34086561,
        'output_capacity_per_unit': 1.01369863, 'number_of_units': 3023.581081, 'availability': 0.97,
        'fixed_costs_per_unit': 116478.4738, 'fixed_om_costs_per_unit': 13062.47379,
        'load_profile': 'tests/fixtures/dummy_config/load_profiles/fake_curve.csv',
        'full_load_hours': 3980.424144}

def test_merit_instance():
    mo = MeritOrder()
    assert mo.merit_order("to_s") == '#<Merit::Order (0 producers, 0 users, 0 flex, 0 price-sensitives)>'

def test_add_participant(must_run_values):
    mo = MeritOrder()

    mo.add_participant(participant='Merit::MustRunProducer', **must_run_values)

    assert mo.merit_order("to_s")  == '#<Merit::Order (1 producers, 0 users, 0 flex, 0 price-sensitives)>'
    assert mo.merit_order("participants")("first")("to_s") == f'#<Merit::MustRunProducer {must_run_values["key"][1:]}>'
    assert mo.merit_order("participants")("first")("full_load_hours") == must_run_values["full_load_hours"]


def test_add_user():
    user_values = {'key': ':total_demand',
        'load_profile': 'tests/fixtures/dummy_config/load_profiles/fake_curve.csv',
        'total_consumption': 417946498897.5582}

    mo = MeritOrder()

    mo.add_user(**user_values)

    assert mo.merit_order("to_s")  == '#<Merit::Order (0 producers, 1 users, 0 flex, 0 price-sensitives)>'
    assert mo.merit_order("participants")("first")("to_s") == f'#<Merit::User::TotalConsumption {user_values["key"][1:]}>'


def test_add_interconnector_with_curve():
    attrs = {
        'key': 'interconnector',
        'marignal_costs': 0.0,
        'availability_curve': Path('tests/fixtures/dummy_config/availability_curves/fake.csv'),
    }


def test_calculate_and_price_curve(must_run_values):
    mo = MeritOrder()

    # Add demand
    user_values = {'key': ':total_demand',
        'load_profile': 'tests/fixtures/dummy_config/load_profiles/fake_curve.csv',
        'total_consumption': 417946498897.5582}
    mo.add_user(**user_values)

    # Add supply
    mo.add_participant(participant='Merit::DispatchableProducer',
        key=':my_dispatchable',
        availability=0.97,
        marginal_costs=81.34086561,
        number_of_units=3023.581081,
        output_capacity_per_unit=1.01369863,
    )

    mo.calculate()
    pc = mo.price_curve()
    assert isinstance(pc, list)
    assert len(pc) == 8760

def test_dispatchables():
    mo = MeritOrder.from_source(Source(Path('tests/fixtures/flex_config')))

    mo.calculate()

    dispatchables = mo.dispatchables_at(300)

    assert len(dispatchables) > 1
    assert len(dispatchables[0]) == 3
    assert dispatchables[0][0] == 'flex_1'
    # Available capacity
    assert dispatchables[0][1] == 2.0

    # dp = mo.dispatchables()("map { |d| d.load_curve.to_a }")

    assert len(dispatchables) > 1
    assert len(dispatchables[2]) == 3
    assert dispatchables[2][0] == 'interconnector_nl_be_import'
    # Available capacity
    assert dispatchables[2][1] == 0

def test_dispatchables_at_with_out_of_bounds_time():
    mo = MeritOrder.from_source(Source(Path('tests/fixtures/flex_config')))

    mo.calculate()
    dispatchables = mo.dispatchables_at(8770)

    # At non existing time point we act like the full capacity is available
    assert len(dispatchables) > 1
    assert len(dispatchables[0]) == 3
    assert dispatchables[0][0] == 'flex_1'
    assert dispatchables[0][1] == 2.0

def test_first_available_dispatchable():
    mo = MeritOrder.from_source(Source(Path('tests/fixtures/flex_config')))

    mo.calculate()

    disp_key, disp_av_cap, marg_costs = mo.first_available_dispatchable_at(300)

    assert disp_key == 'flex_1'
    assert disp_av_cap == 2.0
    assert marg_costs == 0.5

def test_inject_curve_into_interconnector():
    mo = MeritOrder.from_source(Source(Path('tests/fixtures/flex_config')))

    mo.calculate()

    # Test current situation
    dispatchables = mo.dispatchables_at(300)
    assert dispatchables[2][0] == 'interconnector_nl_be_import'
    assert dispatchables[2][1] == 0

    # Inject availability
    mo.inject_curve('interconnector_nl_be_import', [0.0]*8760)
    mo.calculate()

    # Test changes
    dispatchables = mo.dispatchables_at(300)
    assert dispatchables[2][0] == 'interconnector_nl_be_import'
    assert dispatchables[2][1] == 0

def test_rebuild():
    # Build and calculate once
    mo = MeritOrder.from_source(Source(Path('tests/fixtures/flex_config')))
    mo.calculate()

    # Test quickly that the cheapest interconnector is nl_be
    dispatchables = mo.dispatchables_at(300)
    assert dispatchables[2][0] == 'interconnector_nl_be_import'

    # Change the cheapest interconnectors marginal costs
    participant = mo.get_participant_from_cache('interconnector_nl_be_import')
    participant = re.sub(r'marginal_costs: (\.|[\da-zA-Z])+,', 'marginal_costs: 50.0,', participant)

    # Make sure the lock works!
    with pytest.raises(MeritLockedException):
        mo.calculate(auto_build=False)

    # Rebuild and recalulate
    mo.replace_participant_in_cache(participant)
    mo.calculate()

    # Now the cheapest interconnector should be another one in Merit
    dispatchables = mo.dispatchables_at(300)
    assert dispatchables[2][0] != 'interconnector_nl_be_import'
    assert dispatchables[2][0] == 'interconnector_nl_de_import'
