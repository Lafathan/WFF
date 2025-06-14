from wff import WFF, Proof


def test_simple_proof():
    prem1 = WFF('p>q')
    prem2 = WFF('~q')
    goal = WFF('~p')
    proof = Proof([prem1, prem2], goal)
    steps = proof.derive()
    assert steps[-1].formula.statement == str(goal)


def test_conjunction_introduction():
    prem1 = WFF('p')
    prem2 = WFF('q')
    goal = WFF('p*q')
    proof = Proof([prem1, prem2], goal)
    steps = proof.derive()
    assert steps[-1].formula.statement == str(goal)


def test_disjunction_introduction():
    prem1 = WFF('p')
    prem2 = WFF('q')
    goal = WFF('p+q')
    proof = Proof([prem1, prem2], goal)
    steps = proof.derive()
    assert steps[-1].formula.statement == str(goal)


def test_biconditional_introduction():
    prem1 = WFF('p>q')
    prem2 = WFF('q>p')
    goal = WFF('p=q')
    proof = Proof([prem1, prem2], goal)
    steps = proof.derive()
    assert steps[-1].formula.statement == str(goal)


def test_disjunctive_elimination():
    prem1 = WFF('p+q')
    prem2 = WFF('p>r')
    prem3 = WFF('q>r')
    goal = WFF('r')
    proof = Proof([prem1, prem2, prem3], goal)
    steps = proof.derive()
    assert steps[-1].formula.statement == str(goal)
