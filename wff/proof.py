# Proof generation for WFF logical statements
"""Utilities for deriving classical proofs between well formed formulas."""

import typing
from collections import defaultdict, deque
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

    def __str__(self) -> str:
        """Return a human readable representation of the step."""
        refs = ", ".join(str(r) for r in self.refs) if self.refs else ""
        return f"{self.formula} \t{self.rule} {refs}".rstrip()

    __repr__ = __str__


class Proof:
    """Simple forward-chaining proof generator.

    Starting from a set of premises, the algorithm repeatedly applies classical
    argument rules until the desired conclusion is discovered or no further
    progress can be made.
    """

    def __init__(self, premises: typing.List[WFF], conclusion: WFF, search_limit: int = 100) -> None:
        self.premises = [p if isinstance(p, WFF) else WFF(p) for p in premises]
        self.conclusion = conclusion if isinstance(conclusion, WFF) else WFF(conclusion)
        self.steps: typing.List[ProofStep] = []
        self._known: typing.Dict[str, int] = {}
        self._op_index: typing.DefaultDict[typing.Any, typing.List[int]] = defaultdict(list)
        self._queue_high = deque()
        self._queue_low = deque()
        self.search_limit = search_limit
        self._target_atoms = set(self.conclusion.atoms)
        self.contradiction_mode = False

    def _add_step(self, wff: WFF, rule: str, refs: typing.List[int]) -> int:
        """Register a new proof line if it hasn't been seen before."""

        key = str(wff)
        if key not in self._known:
            step = ProofStep(wff, rule, refs)
            self.steps.append(step)
            idx = len(self.steps)
            self._known[key] = idx
            op = step.formula.ast[0] if isinstance(step.formula.ast, tuple) else None
            self._op_index[op].append(idx)
            if self._target_atoms.intersection(step.formula.atoms):
                self._queue_high.append(step)
            else:
                self._queue_low.append(step)
            if self.contradiction_mode and rule != "Reductio ad Absurdum":
                if is_op(step.formula.ast, Logic.negation):
                    comp_ast = step.formula.ast[1][0]
                else:
                    comp_ast = negate_ast(step.formula.ast)
                other = self._known.get(ast_to_str(comp_ast))
                if other:
                    self._add_step(self.conclusion, "Reductio ad Absurdum", [other, idx])
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
        op = ast[0] if isinstance(ast, tuple) else None

        # Modus Ponens and Tollens depend on implications
        if op == Logic.implication:
            p, q = ast[1]
            j = self._known.get(ast_to_str(p))
            if j:
                self._add_step(WFF(ast_to_str(q)), "Modus Ponens", [idx, j])
            for j in list(self._op_index[Logic.negation]):
                oast = self.steps[j - 1].formula.ast
                if ast_equal(oast[1][0], q):
                    self._add_step(WFF(ast_to_str(negate_ast(p))), "Modus Tollens", [idx, j])

        else:
            for j in list(self._op_index[Logic.implication]):
                if j == idx:
                    continue
                oast = self.steps[j - 1].formula.ast
                p, q = oast[1]
                if ast_equal(ast, p):
                    self._add_step(WFF(ast_to_str(q)), "Modus Ponens", [j, idx])
                if op == Logic.negation and ast_equal(ast[1][0], q):
                    self._add_step(WFF(ast_to_str(negate_ast(p))), "Modus Tollens", [j, idx])

        # Disjunctive Syllogism
        if op == Logic.disjunction:
            p, q = ast[1]
            j = self._known.get(ast_to_str(negate_ast(p)))
            if j:
                self._add_step(WFF(ast_to_str(q)), "Disjunctive Syllogism", [idx, j])
            j = self._known.get(ast_to_str(negate_ast(q)))
            if j:
                self._add_step(WFF(ast_to_str(p)), "Disjunctive Syllogism", [idx, j])
        elif op == Logic.negation:
            p = ast[1][0]
            for j in list(self._op_index[Logic.disjunction]):
                oast = self.steps[j - 1].formula.ast
                a, b = oast[1]
                if ast_equal(p, a):
                    self._add_step(WFF(ast_to_str(b)), "Disjunctive Syllogism", [j, idx])
                elif ast_equal(p, b):
                    self._add_step(WFF(ast_to_str(a)), "Disjunctive Syllogism", [j, idx])

        # Conjunction Introduction
        if op != Logic.conjunction:
            for op2, indexes in list(self._op_index.items()):
                if op2 == Logic.conjunction:
                    continue
                for j in list(indexes):
                    if j == idx:
                        continue
                    oast = self.steps[j - 1].formula.ast
                    conj = (Logic.conjunction, [ast, oast])
                    self._add_step(WFF(ast_to_str(conj)), "Conjunction Introduction", [idx, j])

        # Disjunction Introduction
        for op2, indexes in list(self._op_index.items()):
            for j in list(indexes):
                if j == idx:
                    continue
                oast = self.steps[j - 1].formula.ast
                disj1 = (Logic.disjunction, [ast, oast])
                disj2 = (Logic.disjunction, [oast, ast])
                self._add_step(WFF(ast_to_str(disj1)), "Disjunction Introduction", [idx])
                self._add_step(WFF(ast_to_str(disj2)), "Disjunction Introduction", [j])

        # Biconditional Introduction
        if op == Logic.implication:
            for j in list(self._op_index[Logic.implication]):
                if j == idx:
                    continue
                oast = self.steps[j - 1].formula.ast
                p1, q1 = ast[1]
                p2, q2 = oast[1]
                if ast_equal(p1, q2) and ast_equal(q1, p2):
                    bicond = (Logic.biconditional, [p1, q1])
                    self._add_step(WFF(ast_to_str(bicond)), "Biconditional Introduction", [idx, j])


        # Conditional Introduction (heuristic)
        for op2, indexes in list(self._op_index.items()):
            for j in list(indexes):
                if j == idx:
                    continue
                other = self.steps[j - 1]
                oast = other.formula.ast
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
            for j in list(self._op_index[Logic.implication]):
                if j == idx:
                    continue
                a1 = self.steps[j - 1].formula.ast
                if ast_equal(a1[1][0], p):
                    for k in list(self._op_index[Logic.implication]):
                        if k in (idx, j):
                            continue
                        a2 = self.steps[k - 1].formula.ast
                        if ast_equal(a2[1][0], q) and ast_equal(a1[1][1], a2[1][1]):
                            self._add_step(WFF(ast_to_str(a1[1][1])), "Disjunctive Elimination", [idx, j, k])
                            return

    def _search(self) -> None:
        from_high = True
        while (self._queue_high or self._queue_low) and len(self.steps) < self.search_limit:
            if from_high and self._queue_high:
                step = self._queue_high.popleft()
            elif not from_high and self._queue_low:
                step = self._queue_low.popleft()
            elif self._queue_high:
                step = self._queue_high.popleft()
            else:
                step = self._queue_low.popleft()
            from_high = not from_high
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
        self._op_index = defaultdict(list)
        self._queue_high = deque()
        self._queue_low = deque()
        self.contradiction_mode = False

        for prem in self.premises:
            self._add_step(prem, "Assumption", [])

        self._search()
        if str(self.conclusion) in self._known:
            idx = self._known[str(self.conclusion)]
            return self.steps[:idx]

        neg_concl = WFF(f"~({self.conclusion})")
        self.contradiction_mode = True
        self._add_step(neg_concl, "Assumption", [])
        self._search()
        if str(self.conclusion) in self._known:
            idx = self._known[str(self.conclusion)]
            return self.steps[:idx]

        lines = {}
        for i, step in enumerate(self.steps, start=1):
            key = str(step.formula)
            if key.startswith("~") and key[1:] in lines:
                self._add_step(self.conclusion, "Reductio ad Absurdum", [lines[key[1:]], i])
                break
            if key not in lines:
                lines[key] = i

        return self.steps
