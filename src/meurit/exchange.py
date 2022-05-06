import numpy as np
import pandas as pd

class ExchangeModel:

    """make sure to validate interconnectors dataframe for
    specified format. (raise for negative powers)

    validate market prices (8760 entries)"""

    @property
    def regions(self):
        """included regions"""
        keys = ['from_region', 'to_region']
        return list(np.unique(self.interconnectors[keys]))

    @property
    def capacity_matrix(self):
        """make connection matrix for interconnectors"""
        return self.__make_property_matrix('p_mw').fillna(0)

    @property
    def scaling_matrix(self):
        return self.__make_property_matrix('scaling').fillna(0)

    @property
    def in_service_matrix(self):
        return self.__make_property_matrix('in_service').fillna(False)

    def __make_property_matrix(self, key):
        """get property matrix from interconnection dataframe"""

        # prepare dataframe headers
        keys = ['from_region', 'to_region']
        index = np.unique(self.interconnectors[keys])

        # get values and fill dataframe
        values = self.interconnectors.set_index(keys)[key].unstack('to_region')
        matrix = pd.DataFrame(data=values, index=index, columns=index)

        return matrix

    def __init__(self, interconnectors):
        """class initialization"""

        # set dataframe
        self.interconnectors = interconnectors

    def __call__(self, countries, utilization):
        """call market to exchange at highest welfare potential"""
        return self.exchange_energy(countries, utilization)

    def _lookup_coords(self, coords, frame, **kwargs):
        """lookup function to get coordinate values from dataframe"""

        # reindex frame with factorized coords
        idx, cols = pd.factorize(coords)
        values = frame.reindex(cols, axis=1)

        # lookup values
        values = values.to_numpy()
        values = values[np.arange(len(values)), idx]

        return pd.Series(values, index=frame.index, **kwargs)

    def _get_interzonal_price_deltas(self, values, from_region, to_region):
        """get price delta between two regions"""
        return values[from_region].sub(values[to_region])

    def _get_interzonal_exchange_prices(self, values, from_region, to_region):
        """get exchange price between two regions"""
        return values[[from_region, to_region]].min(axis=1)

    def get_avaialble_plants_per_zone(self, zones):
        """name of the rampable power plant during each hour
        of the year"""

        # concat curves of each country
        names = [zone.name for zone in zones]
        keys = [zone.available_plant for zone in zones]

        return pd.concat(keys, axis=1, keys=names)

    def get_production_surpluses_per_zone(self, zones):
        """remaining capacity for each ramping plant for each hour
        of the year"""

        # concat curves of each country
        names = [zone.name for zone in zones]
        surplus = [zone.available_capacity for zone in zones]

        return pd.concat(surplus, axis=1, keys=names)

    def get_exchange_prices_per_zone(self, zones):
        """unit price of the remaining capacity for each ramping plant for
        each hour of the year"""

        # concat curves of each country
        names = [zone.name for zone in zones]
        prices = [zone.price_curve for zone in zones]

        return pd.concat(prices, axis=1, keys=names)

    def get_price_deltas_per_zone(self, zones):
        """get price deltas for each interconnector"""

        # get prices
        prices = self.get_exchange_prices_per_zone(zones)

        # availability conditions
        powered = self.interconnectors.p_mw > 0
        in_service = self.interconnectors.in_service

        # subset available interconnectors
        interconns = self.interconnectors[powered & in_service]

        # make dictonairy
        frm, to = interconns.from_region, interconns.to_region
        mapping = dict(zip(interconns.index, list(zip(frm, to))))

        # evaluate price deltas for combinations
        combs, func = mapping.values(), self._get_interzonal_price_deltas
        deltas = [func(prices, frm, to) for frm, to in combs]

        return pd.concat(deltas, axis=1, keys=mapping.keys())

    def get_exchange_prices_per_interconnector(self, zones):
        """get exchange prices for each interconnector"""

        # reference interconnectors
        interconns = self.interconnectors
        prices = self.get_exchange_prices_per_zone(zones)

        # make diconairy
        frm, to = interconns.from_region, interconns.to_region
        mapping = dict(zip(interconns.index, list(zip(frm, to))))

        # evaluate price
        combs, func = mapping.values(), self._get_interzonal_exchange_prices
        prices = [func(prices, frm, to) for frm, to in combs]

        return pd.concat(prices, axis=1, keys=mapping.keys())

    def get_available_capacity_per_interconnector(self, utilization):
        """determine wheter an interconnector is available to the
        market or is already fully utilized"""

        # determine remaining capacity
        available = self.interconnectors.scaling.sub(utilization)
        capacity = self.interconnectors.p_mw.mul(available)

        return capacity

    def make_exchange_table(self, zones, utilization):
        """make table with hourly exchange information"""

        # determine price deltas and available capacity
        deltas = self.get_price_deltas_per_zone(zones)
        capacity = self.get_available_capacity_per_interconnector(utilization)

        # drop exchange for saturated hours
        deltas = deltas.mul(capacity > 0)

        # get highest exchange potential
        conns = deltas.abs().idxmax(axis=1)
        df = conns.to_frame(name='node')

        # lookup corresponding exchange prices
        deltas = self._lookup_coords(conns, deltas)

        # get region information
        to_region = conns.map(self.interconnectors.to_region)
        from_region = conns.map(self.interconnectors.from_region)

        # assign exchange positions of regions
        df['exporting_zone'] = np.where(deltas >= 0, from_region, to_region)
        df['importing_zone'] = np.where(deltas >= 0, to_region, from_region)

        # lookup and assign capacity utilization and availability
        df['utilization_percent'] = self._lookup_coords(conns, utilization)
        df['available_mw'] = self._lookup_coords(conns, capacity)

        # assign welfare potential
        df['welfare_per_unit'] = deltas.abs()

        return df

    def exchange_energy(self, zones, utilization):
        """exchange energy between markets"""

        # copy utilization
        utilization = utilization.copy(deep=True)

        # get interconnector exchange prices and make table
        exchange = self.make_exchange_table(zones, utilization)
        surplus = self.get_production_surpluses_per_zone(zones)

        # lookup production surplus at exporting country
        coords, name = exchange.exporting_zone, 'surplus_mw'
        surplus = self._lookup_coords(coords, surplus, name=name)

        # determine additional exchange volume
        volume = np.minimum(surplus, exchange.available_mw)

        # add additional utilization percentage
        capacity = exchange.node.map(self.interconnectors.p_mw)
        exchange.utilization_percent += volume.div(capacity)

        # pivot utilization percent over interconnectors
        columns, values = 'node', 'utilization_percent'
        util = exchange.pivot(columns=columns, values=values)

        # update utilization tables
        utilization.update(util)

        # get interconnector price curves
        iprices = self.get_exchange_prices_per_interconnector(zones)

        return iprices, utilization
