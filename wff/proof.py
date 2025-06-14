# Proof generation for WFF logical statements
"""Utilities for deriving classical proofs between well formed formulas."""

import typing
from .core import WFF
from . import logic as Logic


def ast_equal(a, b):
    """Return ``True`` if two AST nodes are structurally equal."""

    if isinstance(a, tuple) and isinstance(b, tuple):
        return a[0] == b[0] and len(a[1]) == len(b[1]) and all(
            ast_equal(x, y) for x, y in zip(a[1], b[1])
        )
    return a == b


def ast_to_str(node):
    """Convert an AST node back into its string representation."""

    if isinstance(node, tuple):
        func, args = node
        if func == Logic.negation:
            sub = ast_to_str(args[0])
            if isinstance(args[0], tuple):
                return f"~({sub})"
            return f"~{sub}"
        if func == Logic.conjunction:
            return f"({ast_to_str(args[0])}*{ast_to_str(args[1])})"
        if func == Logic.disjunction:
            return f"({ast_to_str(args[0])}+{ast_to_str(args[1])})"
        if func == Logic.implication:
            return f"({ast_to_str(args[0])}>{ast_to_str(args[1])})"
        if func == Logic.biconditional:
            return f"({ast_to_str(args[0])}={ast_to_str(args[1])})"
    return str(node)


def negate_ast(node):
    """Return the AST for the negation of ``node``."""

    return (Logic.negation, [node])


def is_op(node, op):
    """Return ``True`` if ``node`` represents the operator ``op``."""

    return isinstance(node, tuple) and node[0] == op


class ProofStep:
    """Container object for an individual proof line."""

    def __init__(self, formula: WFF, rule: str, refs: typing.List[int]):
        self.formula = formula  # resulting formula for this line
        self.rule = rule        # textual rule applied
        self.refs = refs        # references to earlier lines


class Proof:
    """Simple forward-chaining proof generator.

    Starting from a set of premises, the algorithm repeatedly applies classical
    argument rules until the desired conclusion is discovered or no further
    progress can be made.
    """

    def __init__(self, premises: typing.List[WFF], conclusion: WFF) -> None:
        self.premises = [p if isinstance(p, WFF) else WFF(p) for p in premises]
        self.conclusion = conclusion if isinstance(conclusion, WFF) else WFF(conclusion)
        self.steps: typing.List[ProofStep] = []
        self._known: typing.Dict[str, int] = {}
        self._queue: typing.List[ProofStep] = []

    def _add_step(self, wff: WFF, rule: str, refs: typing.List[int]) -> int:
        """Register a new proof line if it hasn't been seen before."""

        key = str(wff)
        if key not in self._known:
            step = ProofStep(wff, rule, refs)
            self.steps.append(step)
            idx = len(self.steps)
            self._known[key] = idx
            self._queue.append(step)
            return idx
        return self._known[key]

    def _apply_unary(self, idx: int, step: ProofStep) -> None:
        """Apply inference rules that use a single premise."""

        ast = step.formula.ast
        if is_op(ast, Logic.conjunction):
            # From ``p*q`` infer ``p`` and ``q``
            a, b = ast[1]
            self._add_step(WFF(ast_to_str(a)), "Conjunction Elimination", [idx])
            self._add_step(WFF(ast_to_str(b)), "Conjunction Elimination", [idx])
        if is_op(ast, Logic.negation) and isinstance(ast[1][0], tuple) and ast[1][0][0] == Logic.negation:
            # ~~p  -->  p
            inner = ast[1][0][1][0]
            self._add_step(WFF(ast_to_str(inner)), "Double Negation", [idx])

    def _apply_binary(self, idx: int, step: ProofStep) -> None:
        """Apply inference rules that depend on two premises."""

        ast = step.formula.ast
        for j, other in enumerate(self.steps, start=1):
            if j == idx:
                continue
            oast = other.formula.ast

            # Modus Ponens
            if is_op(ast, Logic.implication) and ast_equal(oast, ast[1][0]):
                self._add_step(WFF(ast_to_str(ast[1][1])), "Modus Ponens", [idx, j])
            if is_op(oast, Logic.implication) and ast_equal(ast, oast[1][0]):
                self._add_step(WFF(ast_to_str(oast[1][1])), "Modus Ponens", [j, idx])

            # Modus Tollens
            if is_op(ast, Logic.implication) and is_op(oast, Logic.negation) and ast_equal(oast[1][0], ast[1][1]):
                self._add_step(WFF(ast_to_str(negate_ast(ast[1][0]))), "Modus Tollens", [idx, j])
            if is_op(oast, Logic.implication) and is_op(ast, Logic.negation) and ast_equal(ast[1][0], oast[1][1]):
                self._add_step(WFF(ast_to_str(negate_ast(oast[1][0]))), "Modus Tollens", [j, idx])

            # Disjunctive Syllogism
            if is_op(ast, Logic.disjunction) and is_op(oast, Logic.negation):
                p, q = ast[1]
                if ast_equal(oast[1][0], p):
                    self._add_step(WFF(ast_to_str(q)), "Disjunctive Syllogism", [idx, j])
                elif ast_equal(oast[1][0], q):
                    self._add_step(WFF(ast_to_str(p)), "Disjunctive Syllogism", [idx, j])
            if is_op(oast, Logic.disjunction) and is_op(ast, Logic.negation):
                p, q = oast[1]
                if ast_equal(ast[1][0], p):
                    self._add_step(WFF(ast_to_str(q)), "Disjunctive Syllogism", [j, idx])
                elif ast_equal(ast[1][0], q):
                    self._add_step(WFF(ast_to_str(p)), "Disjunctive Syllogism", [j, idx])

            # Conjunction Introduction
            if not is_op(ast, Logic.conjunction) and not is_op(oast, Logic.conjunction):
                conj = (Logic.conjunction, [ast, oast])
                self._add_step(WFF(ast_to_str(conj)), "Conjunction Introduction", [idx, j])

            # Disjunction Introduction
            disj1 = (Logic.disjunction, [ast, oast])
            disj2 = (Logic.disjunction, [oast, ast])
            self._add_step(WFF(ast_to_str(disj1)), "Disjunction Introduction", [idx])
            self._add_step(WFF(ast_to_str(disj2)), "Disjunction Introduction", [j])

            # Biconditional Introduction
            if is_op(ast, Logic.implication) and is_op(oast, Logic.implication):
                p1, q1 = ast[1]
                p2, q2 = oast[1]
                if ast_equal(p1, q2) and ast_equal(q1, p2):
                    bicond = (Logic.biconditional, [p1, q1])
                    self._add_step(WFF(ast_to_str(bicond)), "Biconditional Introduction", [idx, j])

            # Conditional Introduction (heuristic)
            if idx in other.refs:
                impl = (Logic.implication, [ast, oast])
                self._add_step(WFF(ast_to_str(impl)), "Conditional Introduction", [idx, j])
            if j in step.refs:
                impl = (Logic.implication, [oast, ast])
                self._add_step(WFF(ast_to_str(impl)), "Conditional Introduction", [j, idx])

    def _apply_ternary(self, idx: int, step: ProofStep) -> None:
        """Apply rules that require three premises, such as disjunctive elimination."""

        ast = step.formula.ast
        if is_op(ast, Logic.disjunction):
            p, q = ast[1]
            for j, first in enumerate(self.steps, start=1):
                if j == idx:
                    continue
                a1 = first.formula.ast
                if is_op(a1, Logic.implication) and ast_equal(a1[1][0], p):
                    for k, second in enumerate(self.steps, start=1):
                        if k in (idx, j):
                            continue
                        a2 = second.formula.ast
                        if is_op(a2, Logic.implication) and ast_equal(a2[1][0], q) and ast_equal(a1[1][1], a2[1][1]):
                            self._add_step(WFF(ast_to_str(a1[1][1])), "Disjunctive Elimination", [idx, j, k])
                            return

    def _search(self) -> None:
        idx = 0
        limit = 100
        while idx < len(self._queue) and len(self.steps) < limit:
            step = self._queue[idx]
            idx += 1
            line = self._known[str(step.formula)]
            if ast_equal(step.formula.ast, self.conclusion.ast):
                return
            self._apply_unary(line, step)
            self._apply_binary(line, step)
            self._apply_ternary(line, step)
            if str(self.conclusion) in self._known:
                return

    def derive(self) -> typing.List[ProofStep]:
        self.steps = []
        self._known = {}
        self._queue = []

        for prem in self.premises:
            self._add_step(prem, "Assumption", [])

        self._search()
        if str(self.conclusion) in self._known:
            return self.steps

        neg_concl = WFF(f"~({self.conclusion})")
        self._add_step(neg_concl, "Assumption", [])
        self._search()
        if str(self.conclusion) in self._known:
            return self.steps

        lines = {}
        for i, step in enumerate(self.steps, start=1):
            key = str(step.formula)
            if key.startswith("~") and key[1:] in lines:
                self._add_step(self.conclusion, "Reductio ad Absurdum", [lines[key[1:]], i])
                break
            if key not in lines:
                lines[key] = i

        return self.steps
