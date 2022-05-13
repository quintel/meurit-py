# pylint: disable=import-error disable=redefined-outer-name disable=missing-function-docstring disable=protected-access

import re
import pytest

from meurit.merit_order.participants import Participants
from meurit.merit_order import convert_to_ruby_hash_string

def match_consumption(participant):
    pattern = r'total_consumption: (\.|[\da-zA-Z])+\)'
    return float(re.search(pattern, participant).group()[19:-1])

def test_cache_participants():
    participants = Participants()
    # Add a user
    user_values = {'key': ':total_demand',
        'load_profile': 'tests/fixtures/dummy_config/load_profiles/fake_curve.csv',
        'total_consumption': 417946498897.5582}

    participants.cache_participant(
        f"Merit::User.create({convert_to_ruby_hash_string(user_values)})"
    )

    assert len(participants.cached_participants()) == 1
    assert participants._key_for(participants.cached_participants()[0]) == 'total_demand'

def test_replace_participant():
    participants = Participants()

    user_values = {'key': ':total_demand',
        'load_profile': 'tests/fixtures/dummy_config/load_profiles/fake_curve.csv',
        'total_consumption': 1000000}

    # Add a participant
    participants.cache_participant(
       f"Merit::User.create({convert_to_ruby_hash_string(user_values)})"
    )

    # Create different participant with same key
    new_consumption = 12345
    user_values['total_consumption'] = new_consumption
    new_participant =  f"Merit::User.create({convert_to_ruby_hash_string(user_values)})"

    # Check if we set up the test correctly
    assert len(participants.cached_participants()) == 1
    assert match_consumption(participants.cached_participants()[0]) == 1000000
    assert match_consumption(new_participant) == new_consumption

    # Now replace the old with the new
    participants.replace_participant_in_cache(new_participant)
    assert len(participants.cached_participants()) == 1
    assert participants._key_for(participants.cached_participants()[0]) == 'total_demand'
    assert match_consumption(participants.cached_participants()[0]) == new_consumption

    # Create a participant with an unknown key
    user_values['key'] = ':some_other_demand'
    newer_participant =  f"Merit::User.create({convert_to_ruby_hash_string(user_values)})"

    with pytest.raises(ValueError):
        participants.replace_participant_in_cache(newer_participant)

def test_participant_key():
    participants = Participants()

    user_values = {'key': ':total_demand',
        'load_profile': 'tests/fixtures/dummy_config/load_profiles/fake_curve.csv',
        'total_consumption': 1000000}

    # Add a participant
    some_participant = f"Merit::User.create({convert_to_ruby_hash_string(user_values)})"
    participants.cache_participant(some_participant)

    key = participants._key_for(some_participant)

    assert key == 'total_demand'

def test_replace_value():
    participants = Participants()

    user_values = {'key': ':total_demand',
        'load_profile': 'tests/fixtures/dummy_config/load_profiles/fake_curve.csv',
        'total_consumption': 1000000,
        'some_other_attribute': 'one'}

    # Create a participant
    a_participant = f"Merit::User.create({convert_to_ruby_hash_string(user_values)})"

    print(a_participant)

    # Lets see if we can replace some stuff
    a_participant = participants.replace_value(a_participant, 'total_consumption', 500)
    assert '500' in a_participant
    assert '1000000' not in a_participant
    print(a_participant)
    assert a_participant == "Merit::User.create(key: :total_demand, load_profile: Merit::LoadProfile.load('tests/fixtures/dummy_config/load_profiles/fake_curve.csv'), total_consumption: 500, some_other_attribute: 'one')"

    a_participant = participants.replace_value(a_participant, 'some_other_attribute', 'two')
    assert 'two' in a_participant
    assert 'one' not in a_participant

    # Try to replace something that was not there
    with pytest.raises(KeyError):
        participants.replace_value(a_participant, 'foo', 'bar')

    # Replace the loas profile with a list of values
    a_participant = participants.replace_value(a_participant, 'load_profile', [1.0]*8760)

    assert '[1.0,' in a_participant
    assert 'Merit::LoadProfile' not in a_participant
