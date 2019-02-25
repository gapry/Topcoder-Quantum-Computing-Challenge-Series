import numpy as np
from math import sqrt
import copy

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

def get_variable_id(D, A, T, d, a, t):
  '''x_{a,d,t}'''
  return (d * A + a) * T + t

def get_variable_id_y(D, A, T, a, w, p):
  '''y_{a,w,p=0/1}'''
  return A * D * T + (w * A + a) * 2 + p

def get_total_variables(D, A, T):
  return D * A * T + D // 7 * A * 2

def build_total_workload_rule(D, A, T, worker_skill, daily_workload):
  rule = BinaryQuadraticPolynomial(get_total_variables(D, A, T))
  for d in range(D):
    # (sum(s_a x_{a,d,t}) - S_d)^2
    S_d = daily_workload[d]
    for t1 in range(T):
      for a1 in range(A):
        var1 = get_variable_id(D, A, T, d, a1, t1)
        s_a1 = worker_skill[a1]
        for t2 in range(T):
          for a2 in range(A):
            var2 = get_variable_id(D, A, T, d, a2, t2)
            s_a2 = worker_skill[a2]
            # s_a1 * s_a2 * x_{var1} * x_{var2}
            rule.add_coef(var1, var2, s_a1 * s_a2)
        # this is for -2 S_d s_a1 x_{var1}
        rule.add_coef(var1, var1, -2 * s_a1 * S_d)
    rule.add_constant(S_d * S_d)
  return rule.finalize()

def build_preferred_time_rule(D, A, T, reqs):
  rule = BinaryQuadraticPolynomial(get_total_variables(D, A, T))
  for d in range(D):
    for t in range(T):
      for a in range(A):
        var = get_variable_id(D, A, T, d, a, t)
        # this is for (1 - reqs[a][d][t]) * x_{var}
        rule.add_coef(var, var, 1 - reqs[a][d][t])
  return rule.finalize()

def build_sleep_rule(D, A, T):
  rule = BinaryQuadraticPolynomial(get_total_variables(D, A, T))
  # TODO
  return rule.finalize()

def build_workonce_rule(D, A, T):
  rule = BinaryQuadraticPolynomial(get_total_variables(D, A, T))
  for d in range(D):
    for a in range(A):
      # sum(x_{a, d, t}) * (sum(x_{a, d, t}) - 1)
      for t1 in range(T):
        var1 = get_variable_id(D, A, T, d, a, t1)
        for t2 in range(T):
          var2 = get_variable_id(D, A, T, d, a, t2)
          rule.add_coef(var1, var2, 1)
        # this is for -x_{var1}
        rule.add_coef(var1, var1, -1)
  return rule.finalize()

def build_holiday_rule(D, A, T):
  # within each week, every worker works at most 5 days.
  rule = BinaryQuadraticPolynomial(get_total_variables(D, A, T))
  for a in range(A):
    for w in range(D // 7):
      y0 = get_variable_id_y(D, A, T, a, w, 0)
      y1 = get_variable_id_y(D, A, T, a, w, 1)
      coef_y0 = 2
      coef_y1 = 5
      # (sum(x_{a, d, t}) + 2y0 + 5y1 - 4) * (sum(x_{a, d, t} + 2y0 + 5y1 - 5))
      for d1 in range(w * 7, w * 7 + 7):
        for t1 in range(T):
          var1 = get_variable_id(D, A, T, d1, a, t1)
          for d2 in range(w * 7, w * 7 + 7):
            for t2 in range(T):
              var2 = get_variable_id(D, A, T, d2, a, t2)
              rule.add_coef(var1, var2, 1)
          rule.add_coef(var1, y0, 2 * coef_y0)
          rule.add_coef(var1, y1, 2 * coef_y1)
          # this is for (-4 + -5) x_{var1}
          rule.add_coef(var1, var1, -9)

      rule.add_coef(y0, y0, coef_y0 * coef_y0)
      rule.add_coef(y0, y1, coef_y0 * coef_y1)
      rule.add_coef(y1, y0, coef_y1 * coef_y0)
      rule.add_coef(y1, y1, coef_y1 * coef_y1)

      # this is for (-4 + -5) y0
      rule.add_coef(y0, y0, (-4 + -5) * coef_y0)
      # this is for (-4 + -5) y1
      rule.add_coef(y1, y1, (-4 + -5) * coef_y1)
      rule.add_constant(4 * 5)

  for a in range(A):
    for w in range(D // 7):
      y1 = get_variable_id_y(D, A, T, a, w, 1)
      # this is for -y1
      rule.add_coef(y1, y1, -1)
  return rule.finalize()

def build_scheduling_rule(D, A, T, worker_skill, daily_workload, reqs, W):
  rule = BinaryQuadraticPolynomial(get_total_variables(D, A, T))
  total_workload_rule = build_total_workload_rule(D, A, T, worker_skill,
                                                  daily_workload)
  preferred_time_rule = build_preferred_time_rule(D, A, T, reqs)
  preferred_time_rule.multiply_constant(W)
  workonce_rule = build_workonce_rule(D, A, T)
  workonce_rule.multiply_constant(W)
  sleep_rule = build_sleep_rule(D, A, T)
  sleep_rule.multiply_constant(W)
  holiday_rule = build_holiday_rule(D, A, T)
  holiday_rule.multiply_constant(W)

  rule.add_poly(total_workload_rule)
  rule.add_poly(preferred_time_rule)
  rule.add_poly(workonce_rule)
  rule.add_poly(sleep_rule)
  rule.add_poly(holiday_rule)

  return rule.finalize()

def solveDA(rule):
  '''This is a placeholder'''
  print(rule.export_dict())

def main(D, A, T, worker_skill, daily_workload, reqs, W):
  qubo = build_scheduling_rule(D, A, T, worker_skill, daily_workload, reqs, W)
  return solveDA(
      qubo), qubo  # wrapper to call DA API and return results and QUBO.

def generate_test_case(D, A, T, seed):
  '''There are D days, A workers, T time slots per day, and the random seed is seed'''
  assert D % 7 == 0, '[Error] D must be a multiple of 7 days'
  np.random.seed(seed)
  worker_skill = np.random.randint(5, 15, size=A)
  # print 'worker_skill:', worker_skill
  daily_workload = np.random.randint(15, 20, size=D)
  daily_workload = 10 * daily_workload
  # print 'daily_workload:', daily_workload
  reqs = np.random.randint(2, size=(A, D, T))
  W = np.max(daily_workload) // 2
  # print 'W:', W
  return worker_skill, daily_workload, reqs, W

if __name__ == "__main__":
  D = 7
  A = 25
  T = 4
  W = 95
  seed = 1
  worker_skill, daily_workload, reqs, W = generate_test_case(D, A, T, seed)
  main(D, A, T, worker_skill, daily_workload, reqs, W)
