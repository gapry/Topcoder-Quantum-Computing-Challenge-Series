import json
import numpy as np
from math import sqrt
import copy

hint_hardest = [(0, 0, 7), (1, 2, 6), (1, 3, 4), (1, 8, 8), (2, 1, 2), (2, 6,
                                                                        0),
                (2, 7, 7), (3, 1, 5), (3, 5, 0), (3, 7, 4), (4, 2, 8), (4, 4,
                                                                        3),
                (5, 3, 6), (5, 4, 4), (6, 2, 1), (6, 4, 6), (6, 8, 3), (7, 5,
                                                                        2),
                (7, 6, 5), (7, 7, 0), (8, 6, 7)]

class BinaryQuadraticPolynomial:
  '''
  Quadratic Polynomial class
  Arguments:
    n: The number of binary variables that can be handled by this quadratic polynomial. 
       The variables are numbered from 0 to n - 1.
  Attributes:
    array: The numpy array showing this quadratic polynomial. 
           array[i][j] (i <= j) is the coefficient of x_i * x_j. 
           Since all variables are binary, x_i and x_i * x_i are the same variable.
    constant: The constant value of this quadratic polynomial.
  '''

  def __init__(self, n=1024):
    self.array = np.zeros((n, n), dtype=int)
    self.constant = 0
    self._size = n

  def export_dict(self):
    '''Convert this quadratic polynomial to a dictionary. This is will be called in the DA Solver.'''
    cells = np.where(self.array != 0)
    ts = [{
        "coefficient": float(self.array[i][j]),
        "polynomials": [int(i), int(j)]
    } for i, j in zip(cells[0], cells[1])]
    if self.constant != 0:
      ts.append({"coefficient": float(self.constant), "polynomials": []})
    return {'binary_polynomial': {'terms': ts}}

  def add_coef(self, i, j, c):
    if i > j:  # make sure it is an upper triangle matrix.
      t = i
      i = j
      j = t
    assert i >= 0, '[Error] Index out of boundary!'
    assert j < self._size, '[Error] Index out of boundary!'
    self.array[i][j] += c

  def add_constant(self, c):
    self.constant += c

  def add_poly(self, other_quad_poly):
    assert self._size == other_quad_poly._size, '[Error] Array sizes are different!'
    self.array += other_quad_poly.array
    self.constant += other_quad_poly.constant

  def multiply_constant(self, c):
    self.array *= c
    self.constant *= c

  def finalize(self):
    return copy.deepcopy(self)

def get_variable_id(N, i, j, k):
  return (i * N + j) * N + k

def build_cell_rule(N):
  rule = BinaryQuadraticPolynomial(N * N * N)
  for i in range(N):
    for j in range(N):
      for k1 in range(N):
        var1 = get_variable_id(N, i, j, k1)
        for k2 in range(N):
          var2 = get_variable_id(N, i, j, k2)
          rule.add_coef(var1, var2, 1)
        rule.add_coef(var1, var1, -2)  # this is -2 * x_{var1}
      rule.add_constant(1)
  return rule.finalize()

def build_row_rule(N):
  rule = BinaryQuadraticPolynomial(N * N * N)
  for k in range(N):
    for i in range(N):
      for j1 in range(N):
        var1 = get_variable_id(N, i, j1, k)
        for j2 in range(N):
          var2 = get_variable_id(N, i, j2, k)
          rule.add_coef(var1, var2, 1)
        rule.add_coef(var1, var1, -2)  # this is -2 * x_{var1}
      rule.add_constant(1)
  return rule.finalize()

def build_column_rule(N):
  rule = BinaryQuadraticPolynomial(N * N * N)
  for k in range(N):
    for j in range(N):
      for i1 in range(N):
        var1 = get_variable_id(N, i1, j, k)
        for i2 in range(N):
          var2 = get_variable_id(N, i2, j, k)
          rule.add_coef(var1, var2, 1)
        rule.add_coef(var1, var1, -2)  # this is -2 * x_{var1}
      rule.add_constant(1)
  return rule.finalize()

def build_subgrid_rule(N):
  rule = BinaryQuadraticPolynomial(N * N * N)
  sqrtN = int(sqrt(N))
  for grid_i in range(sqrtN):
    for grid_j in range(sqrtN):
      for k in range(N):
        # there can be only one k in the same subgrid.
        for i1 in range(grid_i * 3, grid_i * 3 + 3):
          for j1 in range(grid_j * 3, grid_j * 3 + 3):
            var1 = get_variable_id(N, i1, j1, k)
            for i2 in range(grid_i * 3, grid_i * 3 + 3):
              for j2 in range(grid_j * 3, grid_j * 3 + 3):
                var2 = get_variable_id(N, i2, j2, k)
                rule.add_coef(var1, var2, 1)
            rule.add_coef(var1, var1, -2)  # this is -2 * x_{var1}
        rule.add_constant(1)
  return rule.finalize()

def build_hint_rule(N, hint):
  rule = BinaryQuadraticPolynomial(N * N * N)
  for (j, i, k) in hint:
    var = get_variable_id(N, i, j, k)
    rule.add_coef(var, var, -1)  # this is -1 * x_{var}
    rule.add_constant(1)
  return rule.finalize()

def build_sudoku_rule(N, A):
  cell_rule = build_cell_rule(N)
  row_rule = build_row_rule(N)
  column_rule = build_column_rule(N)
  subgrid_rule = build_subgrid_rule(N)

  cell_rule.multiply_constant(A)
  row_rule.multiply_constant(A)
  column_rule.multiply_constant(A)
  subgrid_rule.multiply_constant(A)

  soduku_rule = BinaryQuadraticPolynomial(N * N * N)
  soduku_rule.add_poly(cell_rule)
  soduku_rule.add_poly(row_rule)
  soduku_rule.add_poly(column_rule)
  soduku_rule.add_poly(subgrid_rule)

  return soduku_rule.finalize()

def build_puzzle_rule(N, A, hint):
  soduku_rule = build_sudoku_rule(N, A)
  # print(soduku_rule.export_dict())
  puzzle_rule = build_hint_rule(N, hint)
  puzzle_rule.multiply_constant(2 * A)
  puzzle_rule.add_poly(soduku_rule)
  # print(puzzle_rule.export_dict())
  return puzzle_rule.finalize()

def solveDA(rule):
  '''This is a placeholder'''
  print(json.dumps(rule.export_dict()))

def main(N, hint, A=1):
  puzzle_rule = build_puzzle_rule(N, A, hint)
  print(puzzle_rule)
  return solveDA(puzzle_rule)  # wrapper to call DA API and return results.

if __name__ == "__main__":
  main(9, hint_hardest, 1)
