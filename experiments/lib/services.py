import requests
import io
import pandas as pd

# base_url = 'https://beta-engine.energytransitionmodel.com/api/v3'
base_url = 'http://localhost:3001/api/v3/'
END_YEAR = 2030

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
            'source': 'mEUrit',
            'user_values': {
                'settings_satisfy_export_with_dispatchables': 1
            }
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


    def create_interconnector(self, index, capacity, import_availability):
        data = {'scenario': {
            'user_values': {
                f'electricity_interconnector_{index}_capacity': capacity,
                f'electricity_interconnector_{index}_co2_emissions_future': 0,
                f'electricity_interconnector_{index}_import_availability': import_availability
            }
        }}
        response = requests.put(self.base_url, json=data)

        if response.ok: return

        raise ScenarioException(info='creating interconnectors')

    def update_interconnector(self, index, price_curve):
        file = price_curve['Price (Euros)'].to_csv(index=False, header=False)
        data = {'file': ('mEUrit_curve.csv', file)}
        response = requests.put(
            self.base_url + f'/custom_curves/interconnector_{index}_price',
            files=data
        )

        if response.ok: return

        raise ScenarioException(info='setting interconnectors')

class ScenarioException(BaseException):
    def __init__(self, info):
        super().__init__()
        self.message = f'Something went wrong connecting to the ETM when {info}'
