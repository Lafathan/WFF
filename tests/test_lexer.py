import pytest
import Lexer
import Logic


def test_tokenize_simple():
    tokens = Lexer.tokenize('a*b')
    assert tokens == [('a', 'Predicate'), ('*', 'Conjunction'), ('b', 'Predicate')]


def test_tokenize_unbalanced():
    with pytest.raises(SyntaxError):
        Lexer.tokenize('(a+b')


def test_parse_conjunction():
    ast, atoms = Lexer.parse('a*b')
    assert atoms == ['a', 'b']
    assert ast == (Logic.conjunction, ['a', 'b'])


def test_parse_negation():
    ast, atoms = Lexer.parse('~a')
    assert atoms == ['a']
    assert ast == (Logic.negation, ['a'])


def test_parse_complex():
    ast, atoms = Lexer.parse('(a+b)&~c')
    expected = (
        Logic.conjunction,
        [
            (Logic.disjunction, ['a', 'b']),
            (Logic.negation, ['c'])
        ]
    )
    assert atoms == ['a', 'b', 'c']
    assert ast == expected
