# WFF
Scripts for working with First Order Logic Well Formed Formulas

## Usage

```python

import WFF

w = WFF.WFF('(a+b)&(a+~b)+~b&c')

# Evaluate
w(a = True, b = False, c = False) # returns True
w(a = False, b = True, c = False) # returns False
w.truth_table # returns a table with all possible inputs and their evaluated values

# Format
w.format(form = 'DNF').statement # '(a)+(~b&c)'
w.format(form = 'CNF').statement # '(a+~b)&(a+c)'

# Test
w.is_tautology() # returns False
w.is_contradiction() # returns False
w.density() # returns 0.625
WFF('a').infer(w) # return True

```
