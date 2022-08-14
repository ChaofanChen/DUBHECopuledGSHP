# -*- coding: utf-8 -*-

from tespy.components import Compressor
from tespy.components import Condenser
from tespy.components import CycleCloser
from tespy.components import HeatExchanger
from tespy.components import Sink
from tespy.components import Source
from tespy.components import Valve
from tespy.components import Pump
from tespy.connections import Connection
from tespy.connections import Bus
from tespy.networks import Network
from tespy.tools.characteristics import CharLine
from tespy.tools.characteristics import load_default_char as ldc

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tespy

# print('CoolProp ver:%s'%(CoolProp.__version__))
print('TESPy ver:%s'%(tespy.__version__))
# %% network
pamb = 1.013  # ambient pressure
Tamb = 2.8  # ambient temperature

# geothermal temperature and flow rate
Tgeo = 40
vgeo = 15

# heating load from building site
Q_b = -1.4e6

nw = Network(fluids=['water', 'R410A'], T_unit='C', p_unit='bar',
             h_unit='kJ / kg', m_unit='kg / s', v_unit='l / s')

# %% components

cc = CycleCloser('cycle closer')

# heat pump system
cd = Condenser('condenser')
va = Valve('valve')
ev = HeatExchanger('evaporator')
cp = Compressor('compressor')

# geothermal heat collector
gh_in = Source('ground heat feed flow')
gh_out = Sink('ground heat return flow')
ghp = Pump('ground heat loop pump')

# heating system
hs_feed = Sink('heating system feed flow')
hs_ret = Source('heating system return flow')
hsp = Pump('heating system pump')

# %% connections

# heat pump system
cc_cd = Connection(cc, 'out1', cd, 'in1')
cd_va = Connection(cd, 'out1', va, 'in1')
va_ev = Connection(va, 'out1', ev, 'in2')
ev_cp = Connection(ev, 'out2', cp, 'in1')
cp_cc = Connection(cp, 'out1', cc, 'in1')
nw.add_conns(cc_cd, cd_va, va_ev, ev_cp, cp_cc)

# geothermal heat collector
gh_in_ghp = Connection(gh_in, 'out1', ghp, 'in1')
ghp_ev = Connection(ghp, 'out1', ev, 'in1')
ev_gh_out = Connection(ev, 'out1', gh_out, 'in1', label='BHE_inlet')
nw.add_conns(gh_in_ghp, ghp_ev, ev_gh_out)

# heating system
hs_ret_hsp = Connection(hs_ret, 'out1', hsp, 'in1')
hsp_cd = Connection(hsp, 'out1', cd, 'in2')
cd_hs_feed = Connection(cd, 'out2', hs_feed, 'in1')
nw.add_conns(hs_ret_hsp, hsp_cd, cd_hs_feed)


# %% component parametrization

# condenser
cd.set_attr(pr1=0.99, pr2=0.99, ttd_u=8, design=['pr2', 'ttd_u'],
            offdesign=['zeta2', 'kA_char'])
# evaporator
kA_char1 = ldc('heat exchanger', 'kA_char1', 'DEFAULT', CharLine)
kA_char2 = ldc('heat exchanger', 'kA_char2', 'EVAPORATING FLUID', CharLine)
ev.set_attr(pr1=0.99, pr2=0.99, ttd_l=8,
            kA_char1=kA_char1, kA_char2=kA_char2,
            design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char'])
# compressor
cp.set_attr(eta_s=0.85, design=['eta_s'], offdesign=['eta_s_char'])
# heating system pump
hsp.set_attr(eta_s=0.75, design=['eta_s'], offdesign=['eta_s_char'])
# ground heat loop pump
ghp.set_attr(eta_s=0.75, design=['eta_s'], offdesign=['eta_s_char'])


# %% connection parametrization

# heat pump system
cc_cd.set_attr(fluid={'water': 0, 'R410A': 1})
ev_cp.set_attr(Td_bp=3)

# geothermal heat collector
gh_in_ghp.set_attr(T=Tgeo, p=1.5, fluid={'water': 1, 'R410A': 0})
ev_gh_out.set_attr(v=vgeo, p=1.5)

# heating system
hs_ret_hsp.set_attr(T=35, m=24, p=2, fluid={'water': 1, 'R410A': 0})
cd_hs_feed.set_attr(p=2)

# starting values
va_ev.set_attr(h0=275)
cc_cd.set_attr(p0=18)

# %% create busses

# characteristic function for motor efficiency
x = np.array([0, 0.2, 0.4, 0.6, 0.8, 1, 1.2])
y = np.array([0, 0.86, 0.9, 0.93, 0.95, 0.96, 0.95])

# power bus
char = CharLine(x=x, y=y)
power = Bus('power input')
power.add_comps({'comp': cp, 'char': char, 'base': 'bus'},
                {'comp': ghp, 'char': char, 'base': 'bus'},
                {'comp': hsp, 'char': char, 'base': 'bus'})

# consumer heat bus
heat_cons = Bus('heating system')
heat_cons.add_comps({'comp': cd, 'base': 'bus'}, {'comp': hsp})

# geothermal heat bus
heat_geo = Bus('geothermal heat')
heat_geo.add_comps({'comp': ev, 'char': -1, 'base': 'bus'},
                   {'comp': ghp})

nw.add_busses(power, heat_cons, heat_geo)

# %% key parameter

cd.set_attr(Q=Q_b)

# %% design calculation

path = 'R410A'
nw.solve('design', init_path=path)
# alternatively use:
# nw.solve('design', init_path=path)
print("\n##### DESIGN CALCULATION #####\n")
nw.print_results()
nw.save(path)
#print(abs(cd.Q.val) / (cp.P.val + hsp.P.val + ghp.P.val))
#print("\n##### OFF-DESIGN CALCULATION #####\n")
#gh_in_ghp.set_attr(T=35)
##cp.set_attr(igva='var')
#nw.solve('offdesign', design_path=path)
#nw.print_results()
#abs(cd.Q.val) / (cp1.P.val + cp2.P.val + erp.P.val + pu.P.val)
#print(abs(cd.Q.val) / (cp.P.val + hsp.P.val + ghp.P.val))

T_range = np.linspace(50, 18, 5)
Q_range = np.array([1.4e6, 1.225e6, 1.1e6, 1.0e6])
df_cop = pd.DataFrame(columns=Q_range)
df_reinj = pd.DataFrame(columns=Q_range)
for T in T_range:
    cop = []
    reinj = []
    gh_in_ghp.set_attr(T=T)

    for Q in Q_range:
        cd.set_attr(Q=-Q)
        if Q == Q_range[0]:
            nw.solve('offdesign', init_path=path, design_path=path)
        else:
            nw.solve('offdesign', design_path=path)

        if nw.lin_dep:
            cop += [np.nan]
            reinj += [np.nan]
        else:
            cop += [abs(cd.Q.val) / (cp.P.val + hsp.P.val + ghp.P.val)]
            reinj += [nw.get_conn('BHE_inlet').T.val]

    df_cop.loc[T] = cop
    df_reinj.loc[T] = reinj

fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
ax.plot(df_cop)
ax.set(xlabel= 'Geothermal BHE temperature (°C)', ylabel='COP (-)')

fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
ax.plot(df_reinj)
ax.set(xlabel= 'Geothermal BHE temperature (°C)', ylabel='BHE return temperature (°C)')















