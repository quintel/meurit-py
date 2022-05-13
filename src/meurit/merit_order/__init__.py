import os

from vendor import rython
from meurit.merit_order.builder import MeritOrderBuilder
from meurit.merit_order.participants import Participants

merit_context = rython.RubyContext(
    requires=['bundler/setup', "quintel_merit"],
    debug=os.getenv('DEBUG_RYTHON') == 'true'
)

class MeritOrder(Participants):
    '''Sorta wraps the Ruby Merit gem'''
    def __init__(self):
        self.merit_order = merit_context("Merit::Order.new")
        self._lock = False

    def add_participant(self, participant='MustRunProducer', **kwargs):
        '''
        Adds a participant to the Merit Order (supply).

        See MO docs for all types of participants.
        '''
        new_instance = f"{participant}.new({convert_to_ruby_hash_string(kwargs)})"
        self._add(merit_context(new_instance))
        self.cache_participant(new_instance)

    def add_user(self, **kwargs):
        '''
        Adds a User to the Merit order (demand).

        Params:
            kwargs: Values to pass to the creation of the User in the
                    Merit gem. See Merit documentation for full info.
                    Required: key. Choose one of: total_consumption,
                    load_curve, consumption_share.
        '''
        new_instance = f"Merit::User.create({convert_to_ruby_hash_string(kwargs)})"
        self._add(merit_context(new_instance))
        self.cache_participant(new_instance)

    def _add(self, participant):
        '''Add a Merit::Participant to the merit order'''
        self.merit_order('add(%(new_participant)r)', new_participant=participant)

    def calculate(self, auto_build=True):
        '''Calculates the Merit Order based on the added participants'''
        if not self.is_locked():
            self.merit_order('calculate')
            self.lock()
        elif auto_build:
            self.rebuild()
            self.calculate()
        else:
            raise MeritLockedException('The Merit order needs to be rebuilt before calulating')

    def unlock(self):
        '''Unlocks MO'''
        self._lock = False

    def lock(self):
        '''Locks the MO'''
        self._lock = True

    def is_locked(self):
        '''Check if MO is currently locked'''
        return self._lock

    def rebuild(self):
        '''Recreates the MO and all it's participants'''
        self.merit_order = merit_context("Merit::Order.new")
        for participant in self.cached_participants():
            self._add(merit_context(participant))

        self.unlock()

    def price_curve(self):
        '''Returns the price curve'''
        return self.merit_order('price_curve')('to_a')

    # TODO: Move all dispatchables methods to seperate file
    def dispatchables_at(self, hour):
        '''
        Returns the order of dispatchables in the given hour. Can only be called after calculate.

        Returns:
            list[list[str, float, float]]: a list with all dispatchables ordered by
                                           marginal costs (key, available capacity, marginal_costs)
        '''

        ruby_map = """
        map do |disp|
            if disp.is_a?(Merit::VariableDispatchableProducer)
                total_capacity = disp.max_load_at(%(hour)r)
            else
                total_capacity = disp.available_output_capacity
            end

            [disp.key, total_capacity - disp.load_at(%(hour)r), disp.marginal_costs]
        end
        """

        return self.dispatchables()(ruby_map, hour=hour)

    def dispatchables(self):
        '''Returns RubyProxy of dispatchables. Only makes sense after calculate is called'''
        return self.merit_order('participants')('dispatchables')

    def first_available_dispatchable_at(self, hour):
        '''
        Returns the key, available capacity and marginal costs of the price setting dispatchable
        in a tuple.
        If none is available, returns the last dispatchable.

        Only call this after calling calculate at least once
        '''
        for key, available_capacity, marginal_cost in self.dispatchables_at(hour):
            dispatchable = (key, available_capacity, marginal_cost)
            if available_capacity:
                break

        return dispatchable

    def inject_curve(self, interconnector_key, curve_values, curve_type='availability'):
        '''
        Inject availability curves back into the interconnector for recalulation

        Params:
            interconnector_key(str): ...
            availability_curve(list[float]): ...
        '''
        participant = self.replace_value(
            self.get_participant_from_cache(interconnector_key),
            curve_type,
            curve_values
        )

        self.replace_participant_in_cache(participant)

    @classmethod
    def from_source(cls, source):
        '''
        Creates and builds a MeritOrder based on the supplied source

        Params:
            source(Source): The source for the MeritOrder
        '''
        mo = cls()
        MeritOrderBuilder(mo, source).build_from_source()

        return mo

class MeritLockedException(BaseException):
    '''Merit order has been locked and needs to be rebuilt before calculating'''

# Helper functions -------------------------------------------------------------

def convert_to_ruby_hash_string(dictionary):
    '''Converts a Python dict to a Ruby hash syntax in a string'''
    return ', '.join((convert_to_ruby_key_value_pair(k,v) for k,v in dictionary.items()))


def convert_to_ruby_key_value_pair(key, value):
    '''
    Converts a Python key value pair into a Ruby syntax key value pair, paying
    attention to the difference between symbol and string values.

    Returns
        str: Ruby hash key value pair as a string
    '''
    if key == 'load_profile':
        return f'{key}: {load_profile(value)}'

    if key == 'availability_curve':
        return f'availability: {curve(value)}'

    if isinstance(value, str) and value[0] != ':':
        value = f"'{value}'"
    elif value is True:
        value = 'true'
    elif value is False:
        value = 'false'

    return f'{key}: {value}'


def load_profile(path):
    '''Returns a str version of Ruby code for creating a load profile from a path'''
    return f"Merit::LoadProfile.load('{path}')"


def curve(path):
    '''Returns a str version of Ruby code for creating a curve from a path'''
    return f"Merit::Curve.load_file('{path}')"
