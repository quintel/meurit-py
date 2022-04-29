# pylint: disable=import-error disable=redefined-outer-name disable=missing-function-docstring

from pathlib import Path
from math import floor

import pytest

from meurit.merit_order import MeritOrder
from meurit.merit_order.builder import MeritOrderBuilder
from meurit.merit_order.source import Source

def test_build_users_from_source():
    mo = MeritOrder()
    source = Source(Path('tests/fixtures/dummy_config'))
    MeritOrderBuilder(mo, source).build_from_source()

    assert mo.merit_order("participants")("users")("length") == 1
    assert mo.merit_order("participants")("users")("first")("key") == 'total_demand'
    assert floor(mo.merit_order("participants")("users")("first")("production")) == 417946498897

def test_build_producers_from_source():
    mo = MeritOrder()
    source = Source(Path('tests/fixtures/dummy_config'))
    MeritOrderBuilder(mo, source).build_from_source()

    # One dispatchable plant and five import interconnectors.
    assert mo.merit_order("participants")("dispatchables")("length") == 6

    assert mo.merit_order("participants")("must_runs")("length") == 1

def test_build_interconnectors_from_source():
    mo = MeritOrder()
    source = Source(Path('tests/fixtures/dummy_config'))
    MeritOrderBuilder(mo, source).build_from_source()

    # Five export interconnectors.
    assert mo.merit_order("participants")("flex")("length") == 5

    connector = mo.merit_order("participants")("flex")("first")
    assert connector("key") == 'interconnector_nl_be_export'
    assert connector("unused_input_capacity_at(0)") == 700
    assert connector("cost_strategy")("sortable_cost") == 10.0

def test_build_flex_from_source():
    mo = MeritOrder()
    source = Source(Path('tests/fixtures/flex_config'))
    MeritOrderBuilder(mo, source).build_from_source()

    # Five export interconnectors plus two flex.
    assert mo.merit_order("participants")("flex")("length") == 7

    connector = mo.merit_order("participants")("flex")("at(0)")
    assert connector("key") == 'flex_1'
    assert connector("available_input_capacity") == 1.0
    assert connector("available_output_capacity") == 2.0
    assert connector("cost_strategy")("sortable_cost") == 0.5

    connector = mo.merit_order("participants")("flex")("at(1)")
    assert connector("key") == 'storage_1'
    assert connector("available_input_capacity") == 100.0
    assert connector("available_output_capacity") == 200.0
    assert connector("cost_strategy")("sortable_cost") == 1.0
