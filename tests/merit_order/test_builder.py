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
