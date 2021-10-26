'''Horrible little logger and plotter'''

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class DataLogger:
    def __init__(self, iterations, countries):
        self.create_prices(iterations, countries)
        self.create_volumes(iterations, countries)
        # energy_interconnector_1_exported_electricity.input (MW)

    def create_prices(self, iterations, countries):
        iterables = [[country.name for country in countries], ['mean', 'max', 'min']]
        index = pd.MultiIndex.from_product(iterables, names=['country', 'measure'])
        self.prices = pd.DataFrame(np.zeros((iterations, 3*len(countries))), columns=index,
            index=range(iterations))


    def create_volumes(self, iterations, countries):
        # right now everybody is connected to everybody so it doesn't matter
        iterables = [[country.name for country in countries], [country.name for country in countries], ['mean', 'max', 'min']]
        index = pd.MultiIndex.from_product(iterables, names=['country', 'to', 'measure'])
        self.volumes = pd.DataFrame(np.zeros((iterations, 3*len(countries)*len(countries))),
            columns=index, index=range(iterations))


    def add_data(self, iteration, country):
        self.set_prices(iteration, country)
        self.set_volumes(iteration, country)


    def set_prices(self, iteration, country):
        prices = DataLogger.extract_price(country)
        for key, val in prices.items():
            self.prices.loc[iteration, (country.name, key)] = val

    def set_volumes(self, iteration, country):
        for index, connection in enumerate(country.interconnectors):
            # curve = country.merit_order[f'energy_interconnector_{index+1}_imported_electricity.output (MW)']
            curve = country.merit_order[f'energy_interconnector_{index+1}_exported_electricity.input (MW)']
            self.volumes.loc[iteration, (country.name, connection.to_country.name, 'mean')] = curve.mean()
            self.volumes.loc[iteration, (country.name, connection.to_country.name, 'min')] = curve.min()
            self.volumes.loc[iteration, (country.name, connection.to_country.name, 'max')] = curve.max()

    def plot(self):
        self.prices.plot(kind='bar', subplots=True, rot=0, figsize=(9, 7), layout=(3, 3),
            legend=None)
        plt.show()

        self.volumes.plot(kind='bar', subplots=True, rot=0, figsize=(9, 7), layout=(3, 9),
            legend=None)
        plt.show()


    @staticmethod
    def extract_price(country):
        return {
            'mean': country.price_curve['Price (Euros)'].mean(),
            'max': country.price_curve['Price (Euros)'].max(),
            'min': country.price_curve['Price (Euros)'].min()
        }
