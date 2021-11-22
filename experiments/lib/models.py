'''Neccesary models for bottom-up experiments'''
import pandas as pd

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
    def __init__(self, name, create_scenario=True):
        self.name = name
        self.interconnectors = InterconnectorCollection()
        # This is ugly but we need it for the subclass
        self.scenario = Scenario.from_area_code(self.name) if create_scenario else None
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
        # Disable the interconnector in the ETM
        self.scenario.set_interconnector_capacity(len(self.interconnectors), 0)

        # if not other.interconnector_to(self):
        #     other.build_interconnector_to(self, capacity)

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
            self.scenario.set_interconnector_capacity(index+1, interconnector.capacity)


    def calculate(self):
        '''
        Overwrites current price curve and merit order with newly downloaded data
        '''
        self.set_merit_order()
        self.set_price_curve()


    def update(self):
        for index, interconnector in enumerate(self.interconnectors):
            self.scenario.set_interconnector(index+1, interconnector.to_country.price_curve)


class InactiveCountry(Country):
    def __init__(self, name, price_curve):
        '''Has a price_curve instead of a scenario! The curve should be 8670 long'''
        super().__init__(name, create_scenario=False)
        self.price_curve = price_curve
        self.validate_curve()
        self.merit_order = None


    def validate_curve(self):
        if not self.price_curve['Price (Euros)'].size == 8760:
            print(f'Price curve for {self.name} should be 8760 long.')

        # No negative prices please
        self.price_curve[self.price_curve < 0] = 0


    def build_interconnector_to(self, other, capacity):
        '''
        Add an interconnector to another country to the collection.

        Params:
            other (Country): the country to connect to
            capacity (int): the capacity of the interconnector in MW
        '''
        self.interconnectors.add(Interconnector(self, other, capacity))

        # if not other.interconnector_to(self):
        #     other.build_interconnector_to(self, capacity)


    def update(self):
        pass


    def calculate(self):
        pass

    def enable_interconnectors(self):
        pass

    @classmethod
    def from_price_curve_file(cls, name, price_curve_file):
        # READ AS FLOAT
        price_curve = pd.read_csv(price_curve_file, header=None, dtype='float64')
        price_curve.columns = ['Price (Euros)']
        return cls(name, price_curve)


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

        return None


class Interconnector:
    # Everything is a reference, these in here are the actual countries ;) No copies. I love it.
    # It's association heaven :)) or hell??
    def __init__(self, from_country, to_country, capacity):
        self.from_country = from_country
        self.to_country = to_country
        self.capacity = capacity


# class NoInterconnectorDefined(BaseException):
#     def __init__(self):
#         self.message= 'No Interconnector was defined between countries'

