import io
import time

import numpy as np
import pandas as pd
import requests



# base_url = 'https://beta-engine.energytransitionmodel.com/api/v3'
base_url = 'http://localhost:3001/api/v3/'
END_YEAR = 2030

class Country:
    def __init__(self, name):
        self.name = name
        self.interconnectors = InterconnectorCollection()
        self.scenario = Scenario.from_area_code(self.name)


    def build_interconnector_to(self, other):
        '''
        Add an interconnector to another country to the collection

        Params:
            other (Country): the country to connect to
        '''
        self.interconnectors.add(Interconnector(self, other))


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

    def calculate(self):
        '''
        Overwrites current price curve and merit order with newly downloaded data
        '''
        self.set_merit_order()
        self.set_price_curve()

    def update(self):
        for index, interconnector in enumerate(self.interconnectors):
            self.scenario.set_interconnector(index, interconnector.to_country.price_curve)

# Service object
class Scenario:
    def __init__(self, etm_id):
        self.etm_id = etm_id
        self.base_url = f'{base_url}scenarios/{etm_id}/'

    @classmethod
    def from_area_code(cls, country_area_code):
        '''
        Creates a scenario in the ETM and saves the id

        Params:
            country_area_code (str): The name of a Country, that is also a valid ETM area_code
        '''
        data = {'scenario': {
            'area_code': country_area_code,
            'end_year': str(END_YEAR),
            'source': 'mEUrit'
        }}

        response = requests.post(base_url + 'scenarios', json=data, headers={'Connection':'close'})

        if response.ok:
            return cls(response.json()['id'])

        raise ScenarioException(info=f'creating a scenario for {country_area_code}')


    def download_curve(self, curve_name):
        response = requests.get(self.base_url + f'/curves/{curve_name}')
        if response.ok:
            return pd.read_csv(io.StringIO(response.content.decode('utf-8')))

        raise ScenarioException(info=f'downloading {curve_name}')


    def download_merit_order(self):
        return self.download_curve('merit_order.csv')


    def download_electricity_price(self):
        return self.download_curve('electricity_price.csv')


    def set_interconnector(self, index, price_curve):
        file = price_curve['Price (Euros)'].to_csv(index=False, header=False)
        data = {'file': ('mEUrit_curve.csv', file)}
        response = requests.put(
            self.base_url + f'/custom_curves/interconnector_{index+1}_price',
            files=data
        )

        if response.ok: return

        raise ScenarioException(info=f'setting interconnectors')

class ScenarioException(BaseException):
     def __init__(self, info):
        self.message = f'Something went wrong connecting to the ETM when {info}'


class InterconnectorCollection:
    def __init__(self):
        self.collection = []

    def __iter__(self):
        yield from self.collection

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
    def __init__(self, from_country, to_country):
        self.from_country = from_country
        self.to_country = to_country
        self.price_curve = np.zeros(8760)
        self.volume = np.zeros(8760)

    def set_curves(self, price_curve, volume):
        self.price_curve = price_curve
        self.volume = volume


class NoInterconnectorDefined(BaseException):
    def __init__(self):
        self.message= 'No Interconnector was defined between countries'

# Let's create some interconnectors! -------------------------------------------
nl = Country('nl')
de = Country('de')
be = Country('be')


nl.build_interconnector_to(de)
nl.build_interconnector_to(be)

de.build_interconnector_to(nl)
de.build_interconnector_to(be)

be.build_interconnector_to(nl)
be.build_interconnector_to(de)

t1 = time.time()

# Let's call the ETM to calculate some price-curves and volumes for us ---------
nl.calculate()
de.calculate()
be.calculate()

print('With doing nothing nl prices are:')
print('  SUM', nl.price_curve['Price (Euros)'].sum())
print('  MAX', nl.price_curve['Price (Euros)'].max())
print('  MIN', nl.price_curve['Price (Euros)'].min())

for i in range(1,10):
    # Put each other's price curves in! --------------------------------------------
    nl.update()
    de.update()
    be.update()

    # And recalculate again! -------------------------------------------------------
    nl.calculate()
    de.calculate()
    be.calculate()

    print(f'After feeding round {i} nl prices are:')
    print('  SUM', nl.price_curve['Price (Euros)'].sum())
    print('  MAX', nl.price_curve['Price (Euros)'].max())
    print('  MIN', nl.price_curve['Price (Euros)'].min())

t2 = time.time()

print(f'It took {t2-t1} seconds!')
