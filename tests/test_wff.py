import Wff


def test_str_and_atoms():
    w = Wff.WFF('a*b')
    assert str(w) == 'a*b'
    assert w.atoms == ['a', 'b']


def test_call_boolean():
    w = Wff.WFF('a*b')
    assert w(a=True, b=True) is True
    assert w(a=True, b=False) is False


def test_call_partial_table():
    w = Wff.WFF('a*b')
    subset = w(a=True)
    assert subset == [({'a': True, 'b': True}, True), ({'a': True, 'b': False}, False)]


def test_truth_table_and_density():
    w = Wff.WFF('a*b')
    assert len(w.truth_table) == 4
    assert w.density() == 0.25


def test_tautology_and_contradiction():
    assert Wff.WFF('a+~a').is_tautology()
    assert Wff.WFF('a*~a').is_contradiction()


def test_derivative_infer():
    h1 = Wff.WFF('a>b')
    h2 = Wff.WFF('a')
    concl = Wff.WFF('b')
    assert Wff.derivative([h1, h2]).infer(concl)


def test_format_cnf_dnf():
    w = Wff.WFF('(a+b)&(a+~b)+~b&c')
    assert w.format('DNF') == '(a)+(~b*c)'
    assert w.format('CNF') == '(a+~b)*(a+c)'
