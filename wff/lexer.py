# Imports #
# =======================================================================================#

import re
from . import logic as Logic

# =======================================================================================#


# Constants #
# =======================================================================================#

_BOOL_PATTERN = "|".join(map(re.escape, Logic.BIN_VALS.keys()))

TOKEN_REGEX = r"""^
    (?P<Conjunction>[*&∧])|
    (?P<Disjunction>[+∨])|
    (?P<Implication>[→>])|
    (?P<Biconditional>[↔=])|
    (?P<Negation>[¬~])|
    (?P<Quantifier>[∀Ǝ][a-zA-Z_][a-zA-Z0-9_]*)|
    (?P<LP>\()|
    (?P<RP>\))|
    (?P<Function>[A-Z][A-Za-z0-9_]*\([^()]*\))|
    (?P<Predicate>[a-z][a-zA-Z0-9_]*)|
    (?P<Boolean>({bools}))
    """.format(bools=_BOOL_PATTERN)

FORMS = re.compile(TOKEN_REGEX, re.VERBOSE)

# =======================================================================================#


# Functions #
# =======================================================================================#

def tokenize(statement):
    """
    Breaks up the given logical statement into individual tokens for parsing
    """
    tokens = []
    # remove whitespace from the statement
    partial = statement.replace(' ', '')
    while len(partial) > 0:
        # compare to regex
        m = re.match(FORMS, partial)
        # if there is a match
        if m:
            # add the token and the match type to the token list
            tokens.append((m.group(0), m.lastgroup))
            # reduce the statement by the length of the token
            partial = partial[m.end():]
        else:
            # if there is no match, raise an error
            error_string = 'Expected a token but found {}'.format(partial)
            raise SyntaxError(error_string)
    # check for balanced parenthesis
    lp = len([_ for _ in tokens if _[1] == 'LP'])
    rp = len([_ for _ in tokens if _[1] == 'RP'])
    if lp != rp:
        raise SyntaxError('Unbalanced parenthesis error')
    return tokens


def parse(statement):
    ast, atoms = Parser(statement).parse()
    return ast, atoms

# =======================================================================================#


# Classes #
# =======================================================================================#

class Parser:
    """
    This class parses a list of tokens

    Inputs:
    statement (string) : a wff that is to be parsed

    Outputs:
    ast (tuple)  : A nested tuple of functions and their arguments
    atoms (list) : A list of strings representing the atomic formula
    """

    # expr : term [+∨→>] expr | term
    # term : fact [&∧↔=] term | fact
    # fact : [¬~] fact | (expr) | atom
    # atom : True | False | PREDICATE | FUNCTION

    # the following two dictionaries are used to map regex matches to functions
    TERM_DICT = {
        'Conjunction': Logic.conjunction,
        'Biconditional': Logic.biconditional
    }
    EXPR_DICT = {
        'Disjunction': Logic.disjunction,
        'Implication': Logic.implication
    }

    def __init__(self, statement):
        self.tokens = tokenize(statement)  # initialize the parser
        self.index = -1  # start at the beginning
        self.next_token()  # grab the first token
        self.atoms = []  # prepare to collect atoms

    def parse(self):
        ast = self.expr()
        if self.current_token is not None:
            raise SyntaxError(
                'Unexpected token {} at {}'.format(self.current_token[0], self.index)
            )
        return ast, self.atoms  # return the ast and the atoms

    def next_token(self):
        self.index += 1  # increment the current token index
        if self.index < len(self.tokens):
            self.current_token = self.tokens[self.index]
        else:
            self.current_token = None

    def atom(self):
        # grab the current token
        tok = self.current_token
        if tok is None:
            raise SyntaxError('Unexpected end of input')
        # check whether it is a predicate or function
        if tok[1] == 'Predicate' or tok[1] == 'Function':
            # if it is a new atom
            if tok[0] not in self.atoms:
                # add it to the list
                self.atoms.append(tok[0])
        # if the atom is a boolean, it will be evaluated at runtime
        _atom = tok[0]
        # increment the token
        self.next_token()
        # return the atom
        return _atom

    def fact(self):
        # grab the current token
        tok = self.current_token
        if tok is None:
            raise SyntaxError('Unexpected end of input')
        # check whether it is an open parenthesis
        if tok[1] == 'LP':
            # grab the expression in the parenthesis
            self.next_token()
            _expression = self.expr()
            # if the parenthesis is properly closed
            if self.current_token[1] == 'RP':
                self.next_token()
                # return the expression as a whole
                return _expression
            raise SyntaxError('Parenthesis error at {}'.format(self.index))
        # if the parenthesis is a closure
        elif tok[1] == 'RP':
            # There should be no free floating right parenthesis
            raise SyntaxError('Parenthesis error at {}'.format(self.index))
        # if the factor is a negation
        elif tok[1] == 'Negation':
            # increment the token
            self.next_token()
            # return negation function with its argument
            return Logic.negation, [self.fact()]
        # if it is not a factor, then it must be an atom
        else:
            return self.atom()

    def term(self):
        # grab the current token
        tok = self.current_token
        if tok is None:
            raise SyntaxError('Unexpected end of input')
        # grab the left hand side of the term
        _term = self.fact()
        # grab the new current token
        tok = self.current_token
        # check the operator between the left and right hand side
        if tok is not None and tok[1] in self.TERM_DICT.keys():
            # increment the token
            self.next_token()
            # return the operator and the left and right hand sides of the term
            return self.TERM_DICT[tok[1]], [_term, self.term()]
        else:
            return _term

    def expr(self):
        # code follows same logic as the term() function
        tok = self.current_token
        if tok is None:
            raise SyntaxError('Unexpected end of input')
        _expr = self.term()
        tok = self.current_token
        if tok is not None and tok[1] in self.EXPR_DICT.keys():
            self.next_token()
            return self.EXPR_DICT[tok[1]], [_expr, self.expr()]
        else:
            return _expr

# =======================================================================================#
