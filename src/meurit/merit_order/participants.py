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

    # Private

    def _key_for(self, participant):
        '''Returns the participants key'''
        pattern = r'key: :(_|[\da-zA-Z])+,'
        return re.search(pattern, participant).group()[6:-1]
