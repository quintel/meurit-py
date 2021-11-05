import vendor.rython as rython
from meurit.merit_order.builder import MeritOrderBuilder

merit_context = rython.RubyContext(requires=['bundler/setup', "quintel_merit"], debug=True)

class MeritOrder:
    '''Sorta wraps the Ruby Merit gem'''
    def __init__(self):
        self.merit_order = merit_context("Merit::Order.new")


    def add_participant(self, participant='MustRunProducer', **kwargs):
        '''
        Adds a participant to the Merit Order (supply).

        See MO docs for all types of participants.
        '''
        self._add(merit_context(f"Merit::{participant}.new({convert_to_ruby_hash_string(kwargs)})"))


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

    if isinstance(value, str) and value[0] != ':':
        return f"{key}: '{value}'"

    return f'{key}: {value}'


def load_profile(path):
    '''Returns a str version of Ruby code for creating a load profile from a path'''
    return f"Merit::LoadProfile.load('{path}')"
