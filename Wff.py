# Imports #
# =============================================================================#

import typing
import itertools

import Lexer
import Logic

# =============================================================================#


# Constants #
# =============================================================================#

# =============================================================================#


# Functions #
# =============================================================================#

def derivative(arguments: list) -> typing.ClassVar:
    
    return WFF('({})'.format(')&('.join([str(arg) for arg in arguments])))
    

def simplify(new_terms: list) -> list:

    def reduce(term, elements):
        for elem in elements:
            if elem in term:
                del term[elem]
                
    terms = []
    iter_count = 0

    # loop until no more simplifications are possible
    while new_terms != terms:
        
        terms = new_terms[:]
        
        # loop through term combinations looking for simplifications
        for i, term1 in enumerate(terms[:-1]):
            
            # skip it if the term is empty
            if len(term1) == 0:
                continue
                
            for j, term2 in enumerate(terms[i + 1:]):

                # skip it if the term is empty
                if len(term2) == 0:
                    continue
                
                # get all possible atoms across both terms
                keys = set().union(*term1, *term2)

                common_factors = []
                uncommon_factors = []
                unbalanced_factors = []

                # determine which bin each key belongs in
                for key in keys:
                    if key in term1 and key in term2:
                        if term1[key] == term2[key]:
                            common_factors.append(key)
                        else:
                            uncommon_factors.append(key)
                    else:
                        unbalanced_factors.append(key)

                # based on factors, determine what can be eliminated
                lc = len(common_factors)
                lu = len(uncommon_factors)
                lb = len(unbalanced_factors)

                # move on if terms begin to deviate
                # (2 uncommon factors or more is irreducible)
                if lu > 1:
                    pass
                elif len(keys) == lc:
                    # Equality: a + a ==> a + {}
                    new_terms[i+1+j].clear()
                elif lu == 1 and lb == 0:
                    if lc > 0:
                        # Adjacency: abc + a~bc ==> ac + {}
                        reduce(new_terms[i], uncommon_factors)
                    else:
                        # Cancellation: a + ~a ==> {} + {}
                        new_terms[i].clear()
                    new_terms[i+1+j].clear()
                elif lc > 0 and lu == 0 and lb > 0:
                    # Absorption: abc + ab ==> ab + {}
                    if all(x in term1 for x in unbalanced_factors):
                        new_terms[i].clear()
                    elif all(x in term2 for x in unbalanced_factors):
                        new_terms[i+1+j].clear()
                elif lu == 1 and lb > 0:
                    # Reduction: ab + a~bc ==> ab + ac
                    if all(x in term1 for x in unbalanced_factors):
                        reduce(new_terms[i], uncommon_factors)
                    elif all(x in term2 for x in unbalanced_factors):
                        reduce(new_terms[i+1+j], uncommon_factors)

        # remove the empty terms
        while {} in new_terms:
            new_terms.remove({})
            
        iter_count += 1
        if iter_count > 10:
            print('Failed to simplify. Exceeded iteration threshold.')
            break

    return new_terms

# =============================================================================#


# WFF Class #
# =============================================================================#

class WFF(object):

    def __init__(self, data: typing.Union[str, list]) -> None:
        """
        Initialize the WFF
        Generate an ast and collect the atoms
        """

        if type(data) is str:
            self.statement = data
        elif type(data) is list:
            self._truth_table = data
            self.statement = WFF(self.format()).statement

    def __setattr__(self, name: str, value: typing.Any) -> None:
        """
        Custom setattr method to prevent statement / evaluation disagreement
        """
        self.__dict__[name] = value
        if name == 'statement':
            # re-parse if a new statement is given
            self.ast, self.atoms = Lexer.parse(value)
            # wipe the truth table
            self._truth_table = None

    def __str__(self) -> str:
        return self.statement

    def __call__(self, **vals: bool) -> typing.Union[bool, list]:
        """
        Evaluates the truth value of the WFF for the given input values
        """

        # remove useless variables form the input dictionary
        vals = {k: v for k, v in vals.items() if k in self.atoms}

        # If not all atoms are contained in given values, return a sub-truth_table
        if set(vals.keys()) != set(self.atoms):
            return_list = []
            for row in self.truth_table:
                if all([v == row[0][k] for k, v in vals.items()]):
                    return_list.append(row)
            return return_list

        var_vals = vals.copy()

        # Recursively evaluate the ast, substituting atoms with given values
        def ast_eval(node) -> bool:
            if isinstance(node, tuple):
                return node[0](*[ast_eval(_node) for _node in node[1]])
            elif node in Logic.BIN_VALS:
                return Logic.BIN_VALS[node]
            else:
                return var_vals[node]

        return ast_eval(self.ast)

    @property
    def truth_table(self) -> list:
        """
        Returns the truth table if it has been generated
        otherwise generates one
        """
        if self._truth_table != None:
            return self._truth_table

        self._truth_table = []
        # loop through all combinations of True/False atomic inputs
        for vals in itertools.product(Logic.BIN_VALS.values(), repeat=len(self.atoms)):
            # assign the input values to an atomic input
            p_vals = {k: v for (k, v) in zip(self.atoms, vals)}
            # append the evaluation results with the inputs to the table
            self._truth_table.append((p_vals, self(**p_vals)))
        return self._truth_table

    def is_tautology(self) -> bool:
        """
        Return whether or not the statement is a tautology
        """
        return all((_[1] for _ in self.truth_table))

    def is_contradiction(self) -> bool:
        """
        Return whether or not the statement is a contradiction
        """
        return all((not _[1] for _ in self.truth_table))

    def density(self) -> float:
        """
        Return the fraction of possible evaluations that are True.
        """
        return sum([1 for _ in self.truth_table if _[1]]) / len(self.truth_table)

    def infer(self, wff) -> bool:
        """
        Returns whether or not the argument WFF can be inferred
        """
        return WFF('({})>({})'.format(self, wff)).is_tautology()

    def format(self, form='DNF') -> str:
        """
        Returns the WFF reformatted to the desired form
        """
        # CNF (conjunctive normal form) (a+b)&(c+d)
        # DNF (disjunctive normal form) (a&b)+(c&d)

        FORM_D = {'DNF': True, 'CNF': False}
        SYMB_D = {'DNF': ('*', ')+('), 'CNF': ('+', ')*(')}

        terms = []
        # loop through the truth table grabbing atomic value combinations
        for row in self.truth_table:
            if row[1] == FORM_D[form]:

                # copy the dictionary to the terms and swap the value if CNF
                if form == 'CNF':
                    terms.append({k: not v for k, v in row[0].items()})
                else:
                    terms.append({k: v for k, v in row[0].items()})

        # reduce the terms by simplification
        simplify(terms)

        # convert the atom/value dictionary to a statement for each term
        terms = [['~' + k if not t[k] else k for k in t] for t in terms]
        # convert the individual terms to strings
        statement_terms = [SYMB_D[form][0].join(m) for m in terms]
        # combine the individual terms into a full statement
        statement = '(' + SYMB_D[form][1].join(statement_terms) + ')'

        return statement

# =============================================================================#
