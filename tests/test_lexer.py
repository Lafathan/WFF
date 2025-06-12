import pytest
from wff import lexer
from wff import logic


def test_tokenize_simple():
    tokens = lexer.tokenize('a*b')
    assert tokens == [('a', 'Predicate'), ('*', 'Conjunction'), ('b', 'Predicate')]


def test_tokenize_multichar_predicate_and_function():
    tokens = lexer.tokenize('foo*Bar(x,y)')
    assert tokens == [
        ('foo', 'Predicate'),
        ('*', 'Conjunction'),
        ('Bar(x,y)', 'Function'),
    ]


def test_tokenize_unbalanced():
    with pytest.raises(SyntaxError):
        lexer.tokenize('(a+b')


def test_parse_conjunction():
    ast, atoms = lexer.parse('a*b')
    assert atoms == ['a', 'b']
    assert ast == (logic.conjunction, ['a', 'b'])


def test_parse_negation():
    ast, atoms = lexer.parse('~a')
    assert atoms == ['a']
    assert ast == (logic.negation, ['a'])


def test_parse_complex():
    ast, atoms = lexer.parse('(a+b)&~c')
    expected = (
        logic.conjunction,
        [
            (logic.disjunction, ['a', 'b']),
            (logic.negation, ['c'])
        ]
    )
    assert atoms == ['a', 'b', 'c']
    assert ast == expected


def test_parse_unexpected_end():
    with pytest.raises(SyntaxError):
        lexer.parse('a*')


def test_parse_extra_characters():
    with pytest.raises(SyntaxError):
        lexer.parse('(a*b)c')
