from meurit import merit_order

def test_merit():
    assert merit_order("to_s") == '<#Merit::Order (0 producers, 0 users, 0 flex, 0 price-sensitives)>'
