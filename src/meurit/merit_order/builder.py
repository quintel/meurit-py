"""The Builder"""


class MeritOrderBuilder:
    """Builds up a merit order with users and other participants parsed from its source"""

    def __init__(self, merit_order, source):
        self.merit_order = merit_order
        self.source = source

    def build_from_source(self):
        self._build_users()
        self._build_producers()
        self._build_flex()
        self._build_interconnectors()

    def _build_users(self):
        for user in self.source.users():
            self.merit_order.add_user(**user)

    def _build_producers(self):
        for producer in self.source.producers():
            self.merit_order.add_participant("Merit::" + producer["type"], **producer)

    def _build_flex(self):
        for flex in self.source.flex():
            print(flex)
            self.merit_order.add_participant(flex["type"], **flex)

    def _build_interconnectors(self):
        for connector in self.source.interconnectors():
            if not connector["in_service"]:
                continue

            # TODO: It's not clear what to do with the "to_region" or "scaling" attributes.
            common_attrs = {
                "marginal_costs": connector["marginal_costs"],
                "number_of_units": 1.0,
                # TODO: This should be specified via the CSV.
                "availability": [1.0] * 8760,
            }

            # Import

            import_attrs = {
                "key": connector["key"] + "_import",
                "output_capacity_per_unit": connector["p_mw"],
            }

            self.merit_order.add_participant(
                "Merit::VariableDispatchableProducer", **common_attrs, **import_attrs
            )

            # Export

            export_attrs = {
                "key": connector["key"] + "_export",
                "input_capacity_per_unit": connector["p_mw"],
                "output_capacity_per_unit": 0.0,
                "consume_from_dispatchables": True,
            }

            self.merit_order.add_participant(
                "Merit::Flex::VariableConsumer", **common_attrs, **export_attrs
            )
