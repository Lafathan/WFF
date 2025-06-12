from wff import logic


def test_negation():
    assert logic.negation(True) is False
    assert logic.negation(False) is True


def test_conjunction():
    assert logic.conjunction(True, True)
    assert not logic.conjunction(True, False)


def test_disjunction():
    assert logic.disjunction(False, True)
    assert not logic.disjunction(False, False)


def test_implication():
    assert logic.implication(True, False) is False
    assert logic.implication(True, True) is True
    assert logic.implication(False, True) is True


def test_biconditional():
    assert logic.biconditional(True, True) is True
    assert logic.biconditional(True, False) is False
