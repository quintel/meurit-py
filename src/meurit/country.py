from meurit.merit_order import MeritOrder
from meurit.merit_order import MeritOrderBuilder


class Country:
    '''Represents one country, that is based on a single source'''

    def __init__(self, source):
        self.merit_order = MeritOrder()
        self.source = source

    def build_order(self):
        '''Use the builder to build up the Merit order'''
        MeritOrderBuilder(self.merit_order, self.source).build_from_source()


class Area:
    '''Keeps track of the area to be analysed, containing all countries'''
    def __init__(self):
        self._countries = []

    # TODO: finish this class, and add interconnection between countries
