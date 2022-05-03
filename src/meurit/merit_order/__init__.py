import os

from vendor import rython
from meurit.merit_order.builder import MeritOrderBuilder

merit_context = rython.RubyContext(
    requires=['bundler/setup', "quintel_merit"],
    debug=os.getenv('DEBUG_RYTHON') == 'true'
)

class MeritOrder:
    '''Sorta wraps the Ruby Merit gem'''
    def __init__(self):
        self.merit_order = merit_context("Merit::Order.new")

    def add_participant(self, participant='MustRunProducer', **kwargs):
        '''
        Adds a participant to the Merit Order (supply).

        See MO docs for all types of participants.
        '''
        self._add(merit_context(f"{participant}.new({convert_to_ruby_hash_string(kwargs)})"))

    def add_user(self, **kwargs):
        '''
        Adds a User to the Merit order (demand).

        Params:
            kwargs: Values to pass to the creation of the User in the
                    Merit gem. See Merit documentation for full info.
                    Required: key. Choose one of: total_consumption,
                    load_curve, consumption_share.
        '''
        self._add(merit_context(f"Merit::User.create({convert_to_ruby_hash_string(kwargs)})"))

    def _add(self, participant):
        '''Add a Merit::Participant to the merit order'''
        self.merit_order('add(%(new_participant)r)', new_participant=participant)

    def calculate(self):
        '''Calculates the Merit Order based on the added participants'''
        self.merit_order('calculate')

    def price_curve(self):
        '''Returns the price curve'''
        return self.merit_order('price_curve')('to_a')

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
                total_capacity = disp.respond_to?(:input_capacity_per_unit) ? disp.input_capacity_per_unit : disp.output_capacity_per_unit
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
        If none is available, returns an empty tuple.

        Only call this after calling calculate at least once
        '''
        for key, available_capacity, marginal_cost in self.dispatchables_at(hour):
            if available_capacity:
                return (key, available_capacity, marginal_cost)

        return ()

    # TODO: add method to reinject curves into interconnectors.
    def inject_curve(self, interconnector_key, curve):
        '''Inject availability curves back into the interconnector'''
        # Q: remove the old one and replace it? Or replace the curve? Or create a new
        # copy the full MeritOrder with the new curves?
        participant = self.dispatchables()("find {|d| d.key == %(key)r}", key=interconnector_key)
        return participant('availability')

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
