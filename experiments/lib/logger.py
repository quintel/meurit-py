'''Horrible little logger and plotter'''

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class DataLogger:
    def __init__(self, iterations, countries):
        self.create_prices(iterations, countries)
        self.create_volumes(iterations, countries)
        self.country_len = len(countries)
        # energy_interconnector_1_exported_electricity.input (MW)


    def create_prices(self, iterations, countries):
        iterables = [[country.name for country in countries], ['mean', 'max', 'min']]
        index = pd.MultiIndex.from_product(iterables, names=['country', 'measure'])
        self.prices = pd.DataFrame(np.zeros((iterations, 3*len(countries))), columns=index,
            index=range(iterations))


    def create_volumes(self, iterations, countries):
        # we dont know the connections yet, so we have a placeholder!
        iterables = [[country.name for country in countries], ['placeholder'], ['export-mean', 'export-max', 'export-min']]
        index = pd.MultiIndex.from_product(iterables, names=['country', 'to', 'measure'])
        self.volumes = pd.DataFrame(np.zeros((iterations, 3*len(countries))),
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
            import_curve = country.merit_order[f'energy_interconnector_{index+1}_imported_electricity.output (MW)']
            export_curve = country.merit_order[f'energy_interconnector_{index+1}_exported_electricity.input (MW)']
            self.volumes.loc[iteration, (country.name, connection.to_country.name, 'export-mean')] = export_curve.mean()
            self.volumes.loc[iteration, (country.name, connection.to_country.name, 'export-min')] = export_curve.min()
            self.volumes.loc[iteration, (country.name, connection.to_country.name, 'export-max')] = export_curve.max()
            self.volumes.loc[iteration, (connection.to_country.name, country.name, 'import-mean')] = import_curve.mean()
            self.volumes.loc[iteration, (connection.to_country.name, country.name, 'import-min')] = import_curve.min()
            self.volumes.loc[iteration, (connection.to_country.name, country.name, 'import-max')] = import_curve.max()


    def plot(self):
        self.plot_prices()
        self.plot_volumes()


    def plot_prices(self):
        fig, axes = plt.subplots(nrows=1, ncols=self.country_len)

        counter = 0
        for country, df in self.prices.groupby(level='country', axis=1):
            axes[counter].title.set_text(f'Mean price in {country} (euro)')
            err = [
                (df[(country, 'mean')] - df[(country, 'min')]).values,
                (df[(country,'max')] - df[(country,'mean')]).values
            ]

            df[(country, 'mean')].plot(kind='bar', rot=0, legend=None,
                yerr=err, ax=axes[counter], capsize=5)
            counter += 1

        plt.show()


    def plot_volumes(self):
        fig, axes = plt.subplots(nrows=self.country_len, ncols=self.country_len-1)

        self.volumes.drop('placeholder', axis=1, level=1, inplace=True)

        coun = 0
        for country, df in self.volumes.groupby(level='country', axis=1):
            sub = 0
            for to, df_to in df.groupby(level='to', axis=1):
                axes[coun,sub].title.set_text(f'{country} & {to}')

                export_err = [
                    (df_to[(country, to, 'export-mean')] - df_to[(country, to, 'export-min')]).values,
                    (df_to[(country, to, 'export-max')] - df_to[(country, to, 'export-mean')]).values
                ]
                import_err = [
                    (df_to[(country, to, 'import-mean')] - df_to[(country, to, 'import-min')]).values,
                    (df_to[(country, to, 'import-max')] - df_to[(country, to, 'import-mean')]).values
                ]


                df_to[[(country, to, 'export-mean'),(country, to, 'import-mean')]].plot(
                    kind='bar',
                    ax=axes[coun,sub],
                    yerr=[export_err, import_err],
                    rot=0, capsize=3,
                    legend=None
                )
                axes[coun,sub].legend([f'{country} export to {to}', f'{to} import from {country}'])
                sub += 1
            coun += 1

        plt.show()


    @staticmethod
    def extract_price(country):
        return {
            'mean': country.price_curve['Price (Euros)'].mean(),
            'max': country.price_curve['Price (Euros)'].max(),
            'min': country.price_curve['Price (Euros)'].min()
        }