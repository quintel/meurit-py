'''Neccesary models for bottom-up experiments'''

from lib.services import Scenario

class Area:
    '''Wraps a collection of  Countries so we can do all operations at once'''
    def __init__(self, *countries):
        self.countries = countries
        self.logger = None


    def calculate_all(self, iteration=0):
        for country in self.countries:
            country.calculate()
            if self.logger:
                self.logger.add_data(iteration, country)


    def enable_all_interconnectors(self):
        for country in self.countries:
            country.enable_interconnectors()


    def update_all(self):
        for country in self.countries:
            country.update()


    def attach_logger(self, logger):
        '''
        Sets the logger to log data to after calculate

        Params:
            logger(DataLogger): the logger
        '''
        self.logger = logger


class Country:
    def __init__(self, name):
        self.name = name
        self.interconnectors = InterconnectorCollection()
        self.scenario = Scenario.from_area_code(self.name)
        self.logger = None


    def build_interconnector_to(self, other, capacity):
        '''
        Add an interconnector to another country to the collection, sets the
        initial capacity to zero

        Params:
            other (Country): the country to connect to
            capacity (int): the capacity of the interconnector in MW
        '''
        self.interconnectors.add(Interconnector(self, other, capacity))
        self.scenario.set_interconnector_capacity(len(self.interconnectors), 0)


    def interconnector_to(self, country):
        '''
        Finds the interconnector to an other country

        Params:
            country (Country): the country that the connection is to

        Returns: Interconnector
        '''
        return self.interconnectors.find(country)


    def set_merit_order(self):
        self.merit_order = self.scenario.download_merit_order()


    def set_price_curve(self):
        self.price_curve = self.scenario.download_electricity_price()


    def enable_interconnectors(self):
        '''TODO: set all of them in one call'''
        for index, interconnector in enumerate(self.interconnectors):
            self.scenario.set_interconnector_capacity(index, interconnector.capacity)


    def calculate(self):
        '''
        Overwrites current price curve and merit order with newly downloaded data
        '''
        self.set_merit_order()
        self.set_price_curve()


    def update(self):
        for index, interconnector in enumerate(self.interconnectors):
            self.scenario.set_interconnector(index, interconnector.to_country.price_curve)


class InterconnectorCollection:
    def __init__(self):
        self.collection = []

    def __iter__(self):
        yield from self.collection

    def __len__(self):
        return len(self.collection)

    def add(self, interconnector):
        self.collection.append(interconnector)

    def find(self, to_country):
        for interconnector in self.collection:
            if interconnector.to_country == to_country:
                return interconnector

        raise NoInterconnectorDefined()


class Interconnector:
    # Everything is a reference, these in here are the actual countries ;) No copies. I love it.
    # It's association heaven :)) or hell??
    def __init__(self, from_country, to_country, capacity):
        self.from_country = from_country
        self.to_country = to_country
        self.capacity = capacity


class NoInterconnectorDefined(BaseException):
    def __init__(self):
        self.message= 'No Interconnector was defined between countries'

