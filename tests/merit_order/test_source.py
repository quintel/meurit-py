'''Tests for Source'''
# pylint: disable=import-error disable=redefined-outer-name disable=missing-function-docstring

from pathlib import Path
import pytest

from meurit.merit_order.source import Source, MissingSourceError, InvalidSourceError

# TEST DATA
#
# First producer:
# 'key': ':agriculture_chp_engine_network_gas',
# 'type': 'MustRunProducer',
# 'marginal_costs': 81.34086561,
# 'output_capacity_per_unit': 1.01369863,
# 'number_of_units': 3023.581081,
# 'availability': 0.97,
# 'fixed_costs_per_unit': 116478.4738,
# 'fixed_om_costs_per_unit': 13062.47379,
# 'load_profile': 'load_profiles/fake_curve.csv',
# 'full_load_hours': 3980.424144
#
# Second producer:
# 'key': ':energy_power_ultra_supercritical_crude_oil',
# 'type': 'DispatchableProducer',
# 'marginal_costs': 102.1810615,
# 'output_capacity_per_unit': 784.0,
# 'number_of_units': 0.0,
# 'availability': 0.89,
# 'fixed_costs_per_unit': 49359621.7,
# 'fixed_om_costs_per_unit': 15059622.37,
#
# First user:
# 'key': ':total_demand',
# 'load_profile': 'load_profiles/fake_curve.csv',
# 'total_consumption': 417946498897.5582


def test_producers():
    source = Source(Path('tests/fixtures/dummy_config'))
    producers = source.producers()

    producer = next(producers)

    assert producer['marginal_costs'] == 81.34086561
    assert producer['key'] == ':agriculture_chp_engine_network_gas'
    assert 'load_profile' in producer

    producer_2 = next(producers)
    assert producer_2['type'] == 'DispatchableProducer'
    assert not 'load_profile' in producer_2


def test_users():
    source = Source(Path('tests/fixtures/dummy_config'))

    users = source.users()

    user = next(users)

    assert not 'consumption_share' in user
    assert user['total_consumption'] == 417946498897.5582


def test_interconnectors():
    source = Source(Path('tests/fixtures/dummy_config'))

    interconnectors = source.interconnectors()

    interconnector = next(interconnectors)

    assert interconnector['key'] == ':interconnector_nl_be'
    assert interconnector['p_mw'] == 700

    assert interconnector['availability_curve'] == Path(
        'tests/fixtures/dummy_config/availability_curves/fake.csv'
    )


def test_flex():
    source = Source(Path('tests/fixtures/flex_config'))

    users = source.flex()

    user = next(users)

    assert user['key'] == ':flex_1'
    assert user['type'] == 'Merit::Flex::Base'


def test_source_with_invalid_path():
    invalid_path = Path('tests/fixtures/non_existing_folder')

    with pytest.raises(MissingSourceError):
        Source(invalid_path)


def test_with_invalid_csvs():
    source = Source(Path('tests/fixtures/invalid_config'))

    # Demand has an invalid load_profile
    users = source.users()

    with pytest.raises(InvalidSourceError, match=r'load_profile'):
        next(users)

    # Supply is a csv with some extra commas at the end. It should not be parsable.
    producers = source.producers()

    with pytest.raises(InvalidSourceError, match=r'could not be parsed'):
        next(producers)
