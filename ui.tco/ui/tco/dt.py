import os
import warnings

import torch
from torch.utils.data import DataLoader, Dataset
from sympy import Symbol, Eq, Abs, tanh, Or, And, Not
import numpy as np
import itertools

import modulus.sym
from modulus.sym.hydra import to_absolute_path, instantiate_arch, ModulusConfig
from modulus.sym.utils.io import csv_to_dict
from modulus.sym.solver import Solver
from modulus.sym.domain import Domain
from modulus.sym.geometry.primitives_3d import Box, Channel, Plane
from modulus.sym.domain.constraint import (
    PointwiseBoundaryConstraint,
    PointwiseInteriorConstraint,
    IntegralBoundaryConstraint,
)
from modulus.sym.domain.validator import PointwiseValidator
from modulus.sym.domain.monitor import PointwiseMonitor
from modulus.sym.key import Key
from modulus.sym.node import Node
from modulus.sym.eq.pdes.navier_stokes import NavierStokes
from modulus.sym.eq.pdes.turbulence_zero_eq import ZeroEquation
from modulus.sym.eq.pdes.basic import NormalDotVec, GradNormal
from modulus.sym.eq.pdes.diffusion import Diffusion, DiffusionInterface
from modulus.sym.eq.pdes.advection_diffusion import AdvectionDiffusion
from modulus.sym.models.fully_connected import FullyConnectedArch

from HotAisleGeo import *


@modulus.sym.main(config_path=".", config_name="config")
def run(cfg: ModulusConfig) -> None:
    # Governing Equations
    # We are directly estimation NS equation no need for turbulence model as we are not interested in TKE etc. 
    # if cfg.custom.turbulent:
    #     ze = ZeroEquation(nu=0.002, dim=3, time=False, max_distance=0.5)
    #     ns = NavierStokes(nu=ze.equations["nu"], rho=1.0, dim=3, time=False)
    #     navier_stokes_nodes = ns.make_nodes() + ze.make_nodes()
    # else:
    ns = NavierStokes(nu=0.01, rho=1.0, dim=3, time=False)
    navier_stokes_nodes = ns.make_nodes()
    normal_dot_vel = NormalDotVec()

    # make network arch
    input_keys = [Key("x"), Key("y"), Key("z")]
    flow_net = FullyConnectedArch(
        input_keys=input_keys, output_keys=[Key("u"), Key("v"), Key("w"), Key("p")]
    )

    # make list of nodes to unroll graph on
    flow_nodes = (
        navier_stokes_nodes
        + normal_dot_vel.make_nodes()
        + [flow_net.make_node(name="flow_network")]
    )

    geo = ThreeFin(parameterized=cfg.custom.parameterized)

    # params for simulation
    # fluid params
    inlet_vel = 1.0

    # make flow domain
    flow_domain = Domain()

    # inlet
    # Presently two inlet will be customized to assign each to different racks
    u_profile = inlet_vel
    
    constraint_inletL = PointwiseBoundaryConstraint(
        nodes=flow_nodes,
        geometry=geo.geo,
        outvar={"u": u_profile, "v": 0, "w": 0},
        batch_size=cfg.batch_size.Inlet,
        criteria=And(Eq(x, L4), H1 <= y, y <= H2, Z2 <= z, z <= Z3),
        lambda_weighting={
            "u": 1.0,
            "v": 1.0,
            "w": 1.0,
        },  # weight zero on edges
        batch_per_epoch=5000,
    )
    flow_domain.add_constraint(constraint_inletL, "inletL")
    
    constraint_inletR = PointwiseBoundaryConstraint(
        nodes=flow_nodes,
        geometry=geo.geo,
        outvar={"u": -u_profile, "v": 0, "w": 0},
        batch_size=cfg.batch_size.Inlet,
        criteria=And(Eq(x, L5), H1 <= y, y <= H2, Z2 <= z, z <= Z3),
        lambda_weighting={
            "u": 1.0,
            "v": 1.0,
            "w": 1.0,
        },  # weight zero on edges
        batch_per_epoch=5000,
    )
    flow_domain.add_constraint(constraint_inletR, "inletR")

    # outlet
    # Presently two outlet will be customized to assign each to CRAH
    constraint_outletL = PointwiseBoundaryConstraint(
        nodes=flow_nodes,
        geometry=geo.geo,
        outvar={"p": 0},
        batch_size=cfg.batch_size.Outlet,
        criteria=geo.OutletL,
        lambda_weighting={"p": -1.0},
        batch_per_epoch=5000,
    )
    flow_domain.add_constraint(constraint_outletL, "outletL")
    
    constraint_outletR = PointwiseBoundaryConstraint(
        nodes=flow_nodes,
        geometry=geo.geo,
        outvar={"p": 0},
        batch_size=cfg.batch_size.Outlet,
        criteria=geo.OutletR,
        lambda_weighting={"p": -1.0},
        batch_per_epoch=5000,
    )
    flow_domain.add_constraint(constraint_outletR, "outletR")
    
    # no slip and no penetration BCs
    no_slip = PointwiseBoundaryConstraint(
        nodes=flow_nodes,
        geometry=geo.geo,
        outvar={"u": 0, "v": 0, "w": 0},
        batch_size=cfg.batch_size.NoSlip,
        lambda_weighting={
            "u": 1.0,
            "v": 1.0,
            "w": 1.0,
        },  # weight zero on edges
        batch_per_epoch=5000,
#         criteria=Not(And(geo.OutletL,geo.OutletR))
    )
    flow_domain.add_constraint(no_slip, "no_slip")

    # flow interior
    lr_interior = PointwiseInteriorConstraint(
        nodes=flow_nodes,
        geometry=geo.geo,
        outvar={"continuity": 0, "momentum_x": 0, "momentum_y": 0, "momentum_z": 0},
        batch_size=cfg.batch_size.InteriorLR,
        lambda_weighting={
            "continuity": Symbol("sdf"),
            "momentum_x": Symbol("sdf"),
            "momentum_y": Symbol("sdf"),
            "momentum_z": Symbol("sdf"),
        },
        compute_sdf_derivatives=True,
        batch_per_epoch=5000,
    )
    flow_domain.add_constraint(lr_interior, "lr_interior")

    # integral continuity
    def integral_criteria(invar, params):
        sdf = geo.geo.sdf(invar, params)
        return np.greater(sdf["sdf"], 0)

    integral_continuity1 = IntegralBoundaryConstraint(
        nodes=flow_nodes,
        geometry=geo.integral_plane,
        outvar={"normal_dot_vel": 1},
        batch_size=5,
        integral_batch_size=cfg.batch_size.IntegralContinuity,
        criteria=integral_criteria,
        lambda_weighting={"normal_dot_vel": 1.0},
        parameterization=geo.x_pos_range1,
        fixed_dataset=False,
        num_workers=4,
    )
    flow_domain.add_constraint(integral_continuity1, "integral_continuity1")

    integral_continuity2 = IntegralBoundaryConstraint(
        nodes=flow_nodes,
        geometry=geo.integral_plane,
        outvar={"normal_dot_vel": -1},
        batch_size=5,
        integral_batch_size=cfg.batch_size.IntegralContinuity,
        criteria=integral_criteria,
        lambda_weighting={"normal_dot_vel": 1.0},
        parameterization=geo.x_pos_range2,
        fixed_dataset=False,
        num_workers=4,
    )
    flow_domain.add_constraint(integral_continuity2, "integral_continuity2")

    # make solver
    flow_slv = Solver(cfg, flow_domain)

    # start flow solver
    flow_slv.solve()


if __name__ == "__main__":
    run()