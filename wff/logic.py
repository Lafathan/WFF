# Constants #
# =======================================================================================#

BIN_VALS = {'True': True, 'False': False}

# =======================================================================================#

# Functions #
# =======================================================================================#


def negation(p: bool) -> bool:
    return not p


def conjunction(*predicates: bool) -> bool:
    return all(predicates)


def disjunction(*predicates: bool) -> bool:
    return any(predicates)


def implication(*predicates: bool) -> bool:
    p, q = predicates[0], predicates[1]
    return disjunction(negation(p), q)


def biconditional(*predicates: bool) -> bool:
    p, q = predicates[0], predicates[1]
    return conjunction(implication(p, q), implication(q, p))

# =======================================================================================#
