import vendor.rython as rython

merit_context = rython.RubyContext(requires=['bundler/setup', "quintel_merit"], debug=True)

merit_order = merit_context("Merit::Order.new")
must_run_producer = merit_context("Merit::MustRunProducer.new( \
    key: :agriculture_chp_engine_network_gas, marginal_costs: 81.34086561, \
    output_capacity_per_unit: 1.01369863, number_of_units: 3023.581081, availability: 0.97, \
    fixed_costs_per_unit: 116478.4738, fixed_om_costs_per_unit: 13062.47379, \
    load_profile: '../etsource/datasets/nl/curves/weather/default/agriculture_heating', \
    full_load_hours: 3980.424144)")
