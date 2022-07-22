# -*- coding: utf-8 -*-

from tespy.components import Compressor
from tespy.components import Condenser
from tespy.components import CycleCloser
from tespy.components import HeatExchanger
from tespy.components import HeatExchangerSimple
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

# %% network
pamb = 1.013  # ambient pressure
Tamb = 2.8  # ambient temperature

# mean geothermal temperature (mean value of ground feed and return flow)
Tgeo = 50

nw = Network(fluids=['water', 'NH3'], T_unit='C', p_unit='bar',
             h_unit='J / kg', m_unit='kg / s')

# %% components

cc = CycleCloser('cycle closer')
cons_closer = CycleCloser('consumer cycle closer')

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
hsp = Pump('heating system pump')
cons = HeatExchangerSimple('consumer')

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
ev_gh_out = Connection(ev, 'out1', gh_out, 'in1')
nw.add_conns(gh_in_ghp, ghp_ev, ev_gh_out)

# heating system
closer_hsp = Connection(cons_closer, 'out1', hsp, 'in1')
hsp_cd = Connection(hsp, 'out1', cd, 'in2')
cd_hscons = Connection(cd, 'out2', cons, 'in1')
hscons_closer = Connection(cons, 'out1', cons_closer, 'in1')
nw.add_conns(closer_hsp, hsp_cd, cd_hscons, hscons_closer)

# %% component parametrization

# condenser
cd.set_attr(pr1=0.99, pr2=0.99, ttd_u=8, design=['pr2', 'ttd_u'],
            offdesign=['zeta2', 'kA_char'])
cons.set_attr(pr=0.99, design=['pr'], offdesign=['zeta'])
# evaporator
kA_char1 = ldc('heat exchanger', 'kA_char1', 'DEFAULT', CharLine)
kA_char2 = ldc('heat exchanger', 'kA_char2', 'EVAPORATING FLUID', CharLine)
ev.set_attr(pr1=0.99, pr2=0.99, ttd_l=8,
            kA_char1=kA_char1, kA_char2=kA_char2,
            design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char'])
# compressor
cp.set_attr(eta_s=0.85, pr=3, design=['eta_s'], offdesign=['eta_s_char'])
# heating system pump
hsp.set_attr(eta_s=0.75, design=['eta_s'], offdesign=['eta_s_char'])
# ground heat loop pump
ghp.set_attr(eta_s=0.75, pr=20, design=['eta_s'], offdesign=['eta_s_char'])


# %% connection parametrization

# heat pump system
cc_cd.set_attr(fluid={'water': 0, 'NH3': 1})
ev_cp.set_attr(Td_bp=2)

# geothermal heat collector
gh_in_ghp.set_attr(T=Tgeo, m=15, p=1.5, fluid={'water': 1, 'NH3': 0})
#ev_gh_out.set_attr(p=1.5)

# heating system
closer_hsp.set_attr(T=60, state='l', fluid={'water': 1, 'NH3': 0})
cd_hscons.set_attr(T=65)
cons.set_attr(Q=-1.225e6)

# starting values
#ev_cp.set_attr(p0=5)
#cc_cd.set_attr(p0=18)

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

# geothermal heat bus
heat_geo = Bus('geothermal heat')
heat_geo.add_comps({'comp': ghp, 'base': 'bus'},
                   {'comp': ev})


nw.add_busses(power, heat_geo)


# %% key parameter
#
#cd.set_attr(Q=-4e3)

# %% design calculation

path = 'NH3'
nw.solve('design')
# alternatively use:
# nw.solve('design', init_path = path)
print("\n##### DESIGN CALCULATION #####\n")
nw.print_results()
nw.save(path)
