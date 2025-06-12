import Logic


def test_negation():
    assert Logic.negation(True) is False
    assert Logic.negation(False) is True


def test_conjunction():
    assert Logic.conjunction(True, True)
    assert not Logic.conjunction(True, False)


def test_disjunction():
    assert Logic.disjunction(False, True)
    assert not Logic.disjunction(False, False)


def test_implication():
    assert Logic.implication(True, False) is False
    assert Logic.implication(True, True) is True
    assert Logic.implication(False, True) is True


def test_biconditional():
    assert Logic.biconditional(True, True) is True
    assert Logic.biconditional(True, False) is False
