from meurit.merit_order import MeritOrder


class Country:
    def __init__(self, source):
        self.merit_order = MeritOrder()
        self.source = source

    def build_order(self):
        '''TODO: Use the builder to build a Merit order'''

