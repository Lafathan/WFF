# WFF
Scripts for working with First Order Logic Well Formed Formulas

## Usage

```python

import WFF

w = WFF.WFF('(a+b)&(a+~b)+~b&c')

# Evaluate
w(a = True, b = False, c = False) # returns True
w(a = False, b = True, c = False) # returns False
w(a = False, c = True) # returns the following truth table

# [({'b': True }, False),
#  ({'b': False}, True )]

w.truth_table # returns a table with all possible inputs and their evaluated values
w() # returns the same as above
w.statement # returns the logical statement

# Format
w.format(form = 'DNF') # '(a)+(~b&c)'
w.format(form = 'CNF') # '(a+~b)&(a+c)'

# Test
w.is_tautology() # returns False
w.is_contradiction() # returns False
w.density() # returns 0.625

# hypothesis 1: if a then b
h1 = WFF('a>b')
# hypothesis 2: a
h2 = WFF('a')
# conclusion: b
c = WFF('b')
# valid?
derivative([h1, h2]).infer(c) # return True

```
