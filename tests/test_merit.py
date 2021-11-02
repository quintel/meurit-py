from meurit import merit_order, must_run_producer

def test_merit():
    assert merit_order("to_s") == '<#Merit::Order (0 producers, 0 users, 0 flex, 0 price-sensitives)>'

    assert '<Merit::MustRunProducer' in must_run_producer("to_s")

    merit_order('add(%(mrp)r)', mrp=must_run_producer)

    assert merit_order("to_s") == '<#Merit::Order (1 producers, 0 users, 0 flex, 0 price-sensitives)>'
