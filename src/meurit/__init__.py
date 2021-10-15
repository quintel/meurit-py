import vendor.rython as rython

merit_context = rython.RubyContext(requires=['bundler/setup', "quintel_merit"], debug=True)

merit_order = merit_context("Merit::Order.new")
