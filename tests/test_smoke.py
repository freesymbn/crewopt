"""Smoke test: the LP/MIP toolchain (Pyomo + HiGHS) is installed and solves a tiny model.

Model:  min x + 2y   s.t.  x + y >= 1,  x, y in {0, 1}
Optimal: x = 1, y = 0, objective = 1
"""

import pyomo.environ as pyo


def test_pyomo_highs_solves_tiny_mip():
    m = pyo.ConcreteModel()
    m.x = pyo.Var(domain=pyo.Binary)
    m.y = pyo.Var(domain=pyo.Binary)
    m.obj = pyo.Objective(expr=m.x + 2 * m.y, sense=pyo.minimize)
    m.cover = pyo.Constraint(expr=m.x + m.y >= 1)

    result = pyo.SolverFactory("appsi_highs").solve(m)

    assert result.solver.termination_condition == pyo.TerminationCondition.optimal
    assert pyo.value(m.obj) == 1
    assert pyo.value(m.x) == 1
    assert pyo.value(m.y) == 0
