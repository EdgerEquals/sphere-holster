"""DOLFINx smoke test (FEniCSx).

1. Poisson -lap(u) = f on the unit square, manufactured solution
   u = 1 + x^2 + 2y^2 (f = -6). P2 elements reproduce it exactly, so the
   L2 error must be at round-off level.
2. Poisson with u = sin(pi x) sin(pi y) on a 32x32 P1 mesh: L2 error must be
   below 2e-3 (O(h^2) discretisation error), and halve-h convergence rate ~2.
3. 1D steady heat conduction -k T'' = q on [0, L], T(0)=T(L)=0.
   Analytic peak T_max = q L^2 / (8 k). P2 is exact for this quadratic.
"""
import os
import sys

import numpy as np
import ufl
from mpi4py import MPI
from petsc4py import PETSc
from dolfinx import fem, mesh, __version__ as dolfinx_version
from dolfinx.fem.petsc import LinearProblem

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from summary import Report  # noqa: E402

rep = Report(f"FEniCSx (DOLFINx {dolfinx_version})", os.path.join(os.path.dirname(__file__), "out"))
comm = MPI.COMM_WORLD


def solve(msh, degree, u_exact_ufl, f_ufl, bc_expr, k=1.0, prefix="p"):
    V = fem.functionspace(msh, ("Lagrange", degree))
    tdim = msh.topology.dim
    msh.topology.create_connectivity(tdim - 1, tdim)
    facets = mesh.exterior_facet_indices(msh.topology)
    dofs = fem.locate_dofs_topological(V, tdim - 1, facets)
    ubc = fem.Function(V)
    ubc.interpolate(bc_expr)
    bc = fem.dirichletbc(ubc, dofs)
    u, v = ufl.TrialFunction(V), ufl.TestFunction(V)
    a = k * ufl.inner(ufl.grad(u), ufl.grad(v)) * ufl.dx
    L = f_ufl * v * ufl.dx
    problem = LinearProblem(a, L, bcs=[bc], petsc_options_prefix=prefix,
                            petsc_options={"ksp_type": "preonly", "pc_type": "lu"})
    uh = problem.solve()
    if isinstance(uh, tuple):
        uh = uh[0]
    err = fem.assemble_scalar(fem.form((uh - u_exact_ufl) ** 2 * ufl.dx))
    return uh, np.sqrt(comm.allreduce(err, op=MPI.SUM))


# 1. exact quadratic
msh = mesh.create_unit_square(comm, 8, 8)
x = ufl.SpatialCoordinate(msh)
uq = 1 + x[0] ** 2 + 2 * x[1] ** 2
_, e = solve(msh, 2, uq, fem.Constant(msh, PETSc.ScalarType(-6.0)),
             lambda X: 1 + X[0] ** 2 + 2 * X[1] ** 2, prefix="quad_")
rep.check("Poisson P2, u=1+x^2+2y^2: L2 error", 0.0, float(e), abs_tol=1e-10)

# 2. sin*sin manufactured solution, convergence
errs = []
for n in (16, 32):
    msh = mesh.create_unit_square(comm, n, n)
    x = ufl.SpatialCoordinate(msh)
    us = ufl.sin(ufl.pi * x[0]) * ufl.sin(ufl.pi * x[1])
    f = 2 * ufl.pi ** 2 * us
    _, e = solve(msh, 1, us, f, lambda X: np.sin(np.pi * X[0]) * np.sin(np.pi * X[1]), prefix=f"sin{n}_")
    errs.append(float(e))
rep.check("Poisson P1 32x32, u=sin(pi x)sin(pi y): L2 error < 2e-3", 0.0, errs[1], abs_tol=2e-3)
rate = float(np.log2(errs[0] / errs[1]))
rep.check("P1 L2 convergence rate (16->32)", 2.0, round(rate, 4), abs_tol=0.15)

# 3. 1D steady heat conduction
Lbar, kc, q = 0.01, 1.4, 5.0e6   # 10 mm fused-silica-like bar, k=1.4 W/mK, q=5 MW/m^3
msh = mesh.create_interval(comm, 20, [0.0, Lbar])
x = ufl.SpatialCoordinate(msh)
Tex = q / (2 * kc) * x[0] * (Lbar - x[0])
Th, e = solve(msh, 2, Tex, fem.Constant(msh, PETSc.ScalarType(q)), lambda X: 0 * X[0], k=kc, prefix="heat_")
tmax_local = Th.x.array.max() if Th.x.array.size else -np.inf
tmax = comm.allreduce(tmax_local, op=MPI.MAX)
rep.check("1D heat: T_max = qL^2/(8k) [K]", q * Lbar ** 2 / (8 * kc), float(tmax), rel_tol=1e-9)
rep.check("1D heat: L2 error vs analytic", 0.0, float(e), abs_tol=1e-9)
rep.finish()
