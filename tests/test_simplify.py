from wff import simplify


def test_simplify_equality():
    assert simplify([{'a': True}, {'a': True}]) == [{'a': True}]


def test_simplify_cancellation():
    assert simplify([{'a': True}, {'a': False}]) == []


def test_simplify_adjacency():
    terms = [{'a': True, 'b': True, 'c': True}, {'a': True, 'b': False, 'c': True}]
    assert simplify(terms) == [{'a': True, 'c': True}]


def test_simplify_absorption():
    terms = [{'a': True, 'b': True, 'c': True}, {'a': True, 'b': True}]
    assert simplify(terms) == [{'a': True, 'b': True}]


def test_simplify_reduction():
    terms = [{'a': True, 'b': True}, {'a': True, 'b': False, 'c': True}]
    assert simplify(terms) == [{'a': True, 'b': True}, {'a': True, 'c': True}]
