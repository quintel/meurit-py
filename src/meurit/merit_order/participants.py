'''Participants 'caching' for MeritOrder'''
import re

class Participants():
    '''Cache the strigified objects needed to build up a Ruby Merit instance'''

    def cached_participants(self):
        '''
        List of stringified Merit::Participant instances, ready to be fed to a
        merit_context
        '''
        return self._participants

    def cache_participant(self, participant):
        '''Add one user to the list'''
        try:
            self._participants.append(participant)
        except AttributeError:
            self._participants = [participant]

    def replace_participant_in_cache(self, new_participant):
        '''
        Replaces the old partcipant with a new one, based on their keys.
        Raises a ValueError if no participant is found to replace

        Params:
            new_participant(str): Stringified Merit:Participant
        '''
        key = self._key_for(new_participant)

        for index, participant in enumerate(self._participants):
            if self._key_for(participant) == key:
                self._participants[index] = new_participant
                break
        else:
            raise ValueError(f'Could not replace the participant with key {key}')

    def get_participant_from_cache(self, key):
        '''
        Returns a participant from the cache based on its key. Returns None if not found
        '''
        for participant in self._participants:
            if self._key_for(participant) == key:
                return participant
        return None

    def replace_value(self, participant, key, new_value):
        '''
        Replace the value that is currently under the key in the participant with a new value

        Params:
            participant(str):       Stringified version of a Merit::Participant
            key(str):               The key to replace the value of
            new_value(str|float):   The value to replace the old with
        '''
        merit_type, attributes = participant.split('(', 1)
        attributes = attributes.split(', ')
        # Remove the last bracket
        attributes[-1] = attributes[-1][:-1]

        for index, attribute in enumerate(attributes):
            if attribute.startswith(key):
                attributes[index] = f'{key}: {new_value}'
                break
        else:
            raise KeyError('Key was not found in the participant')

        return f'{merit_type}({", ".join(attributes)})'

    # Private

    def _key_for(self, participant):
        '''Returns the participants key'''
        pattern = r'key: :(_|[\da-zA-Z])+,'
        return re.search(pattern, participant).group()[6:-1]
