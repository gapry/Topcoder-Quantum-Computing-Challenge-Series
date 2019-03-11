import numpy as np
from math import sqrt
import copy

def load_graph(filename):
  lines = open(filename).readlines()
  n_node = int(lines[0].split()[0])
  n_edge = int(lines[0].split()[1])
  assert len(lines) == n_edge + 1

  edges = []
  for i in range(n_edge):
    parts = lines[i + 1].split()
    a, b, c = int(parts[0]), int(parts[1]), int(parts[2])
    assert (1 <= a) and (a <= n_node)
    assert (1 <= b) and (b <= n_node)
    a -= 1
    b -= 1
    edges.append((a, b, c))
  return n_node, edges

class BinaryQuadraticPolynomial:
  '''
  Quadratic Polynomial class
    Arguments:
      n: The number of binary variables that can be handled by this quadratic polynomial. 
         The variables are numbered from 0 to n - 1.
      Attributes:
        array: The numpy array showing this quadratic polynomial. 
               array[i][j] (i &lt;= j) is the coefficient of x_i * x_j. 
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

def build_max_cut_rule(n_node, edges):
  rule = BinaryQuadraticPolynomial(n_node)
  # TODO and and My Solution
  x, y, z = 0, 0, 0
  for k in range(len(edges[:-1])):
    i = edges[k]
    j = edges[k + 1]
    x += (i[0] - j[0])
    y += (i[1] - j[1])
    z += (i[2] - j[2])
  ans = (x**2, y**2, z**2)
  return rule.finalize()

class Solution:
  def __init__(self, energy=0, frequency=0, configuration=[]):
    self.energy = energy
    self.frequency = frequency
    self.configuration = configuration

def solveDA(rule, da_params):
  '''This is a placeholder'''
  print(rule.export_dict(), da_params)
  dummy_solution = Solution(1, 1, np.random.randint(2, size=rule._size))
  return [dummy_solution]

def find_minimum_solution(da_results):
  minimum = da_results[0].energy
  best_solution = None
  for result in da_results:
    e = result.energy
    s = result
    if minimum >= e:
      minimum = e
      best_solution = s
  return best_solution

def make_max_cut_answer(da_results):
  # This is an example.
  solution = find_minimum_solution(da_results)
  group_1 = []
  group_2 = []
  for i, bit in enumerate(solution.configuration):
    if bit == 0:
      group_1.append(i + 1)
    else:
      group_2.append(i + 1)
  return group_1, group_2

def main(n_node, edges):
  qubo = build_max_cut_rule(n_node, edges)

  # wrapper to call DA API.
  da_results = solveDA(
      qubo,
      {
          'number_iterations': 500000,
          'number_replicas': 26,  # Min: 26, Max: 128
          # Start solving using the initial bits.
          'guidance_config': {str(x): False
                              for x in range(0, qubo._size)},
          'solution_mode': 'COMPLETE'  # QUICK or COMPLETE
      })

  # Return the groups of nodes of the max-cut.
  group_1, group_2 = make_max_cut_answer(da_results)
  return (group_1, group_2)

if __name__ == '__main__':
  n_node, edges = load_graph('sample_graph.txt')
  answer = main(n_node, edges)
  print('Group 1', answer[0])
  print('Group 2', answer[1])
