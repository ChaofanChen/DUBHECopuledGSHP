# -*- coding: utf-8 -*-

from tespy.components import Compressor
from tespy.components import Condenser
from tespy.components import CycleCloser
from tespy.components import Drum
from tespy.components import HeatExchanger
from tespy.components import HeatExchangerSimple
from tespy.components import Pump
from tespy.components import Sink
from tespy.components import Source
from tespy.components import Valve
from tespy.connections import Connection
from tespy.connections import Ref
from tespy.networks import Network
from tespy.tools.characteristics import CharLine
from tespy.tools.characteristics import load_default_char as ldc
import numpy as np
import pandas as pd

# %% network

nw = Network(fluids=['air', 'water', 'NH3'], T_unit='C', p_unit='bar',
             h_unit='kJ / kg', m_unit='kg / s')

# %% components

# sources & sinks

cool_closer = CycleCloser('coolant cycle closer')
cons_closer = CycleCloser('consumer cycle closer')

amb_in = Source('source ambient')
amb_out = Sink('sink ambient')

ic_in = Source('source intercool')
ic_out = Sink('sink intercool')

# consumer system

cd = Condenser('condenser')
rp = Pump('recirculation pump')
cons = HeatExchangerSimple('consumer')

# evaporator system

va = Valve('valve')
dr = Drum('drum')
ev = HeatExchanger('evaporator')
su = HeatExchanger('superheater')
pu = Pump('pump evaporator')

# compressor-system

cp1 = Compressor('compressor 1')
cp2 = Compressor('compressor 2')
he = HeatExchanger('intercooler')

# %% connections

# consumer system

c_in_cd = Connection(cool_closer, 'out1', cd, 'in1')
close_rp = Connection(cons_closer, 'out1', rp, 'in1')
rp_cd = Connection(rp, 'out1', cd, 'in2')
cd_cons = Connection(cd, 'out2', cons, 'in1')
cons_close = Connection(cons, 'out1', cons_closer, 'in1')

nw.add_conns(c_in_cd, close_rp, rp_cd, cd_cons, cons_close)

# connection condenser - evaporator system

cd_va = Connection(cd, 'out1', va, 'in1')

nw.add_conns(cd_va)

# evaporator system

va_dr = Connection(va, 'out1', dr, 'in1')
dr_pu = Connection(dr, 'out1', pu, 'in1')
pu_ev = Connection(pu, 'out1', ev, 'in2')
ev_dr = Connection(ev, 'out2', dr, 'in2')
dr_su = Connection(dr, 'out2', su, 'in2')

nw.add_conns(va_dr, dr_pu, pu_ev, ev_dr, dr_su)

amb_in_su = Connection(amb_in, 'out1', su, 'in1')
su_ev = Connection(su, 'out1', ev, 'in1')
ev_amb_out = Connection(ev, 'out1', amb_out, 'in1')

nw.add_conns(amb_in_su, su_ev, ev_amb_out)

# connection evaporator system - compressor system

su_cp1 = Connection(su, 'out2', cp1, 'in1')

nw.add_conns(su_cp1)

# compressor-system

cp1_he = Connection(cp1, 'out1', he, 'in1')
he_cp2 = Connection(he, 'out1', cp2, 'in1')
cp2_close = Connection(cp2, 'out1', cool_closer, 'in1')

ic_in_he = Connection(ic_in, 'out1', he, 'in2')
he_ic_out = Connection(he, 'out2', ic_out, 'in1')

nw.add_conns(cp1_he, he_cp2, ic_in_he, he_ic_out, cp2_close)

# %% component parametrization

# condenser system

cd.set_attr(pr1=0.99, pr2=0.99, ttd_u=8, design=['pr2', 'ttd_u'],
            offdesign=['zeta2', 'kA_char'])
rp.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])
cons.set_attr(pr=0.99, design=['pr'], offdesign=['zeta'])

# evaporator system

kA_char1 = ldc('heat exchanger', 'kA_char1', 'DEFAULT', CharLine)
kA_char2 = ldc('heat exchanger', 'kA_char2', 'EVAPORATING FLUID', CharLine)

ev.set_attr(pr1=0.99, pr2=0.99, ttd_l=8,
            kA_char1=kA_char1, kA_char2=kA_char2,
            design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char'])
su.set_attr(pr1=0.99, pr2=0.99, ttd_u=2, design=['pr1', 'pr2', 'ttd_u'],
            offdesign=['zeta1', 'zeta2', 'kA_char'])
pu.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])

# compressor system

cp1.set_attr(eta_s=0.85, design=['eta_s'], offdesign=['eta_s_char'])
cp2.set_attr(eta_s=0.9, pr=3, design=['eta_s'], offdesign=['eta_s_char'])

he.set_attr(pr1=0.98, pr2=0.98, design=['pr1', 'pr2'],
            offdesign=['zeta1', 'zeta2', 'kA_char'])

# %% connection parametrization

# condenser system

c_in_cd.set_attr(fluid={'air': 0, 'water': 0, 'NH3': 1})
close_rp.set_attr(T=60, p=20, fluid={'air': 0, 'water': 1, 'NH3': 0})
cd_cons.set_attr(T=90)

# evaporator system cold side

pu_ev.set_attr(m=Ref(va_dr, 0.75, 0), p0=5)
su_cp1.set_attr(p0=5, state='g')

# evaporator system hot side
T_pro=50
m_pro=15
air_temp=10

amb_in_su.set_attr(T=T_pro, p=2, m=m_pro, fluid={'air': 0, 'water': 1, 'NH3': 0})
#ev_amb_out.set_attr(T=9)

he_cp2.set_attr(Td_bp=5, p0=20)
ic_in_he.set_attr(p=1, T=air_temp, fluid={'air': 1, 'water': 0, 'NH3': 0})
he_ic_out.set_attr(T=30, design=['T'])

# %% key paramter

cons.set_attr(Q=-1.225e6)

# %% Calculation

nw.solve('design')
nw.print_results()
# alternatively use:
#nw.solve('design', init_path='condenser_eva')
#nw.print_results()
nw.save('heat_pump')

amb_in_su.set_attr(T=40)
cons.set_attr(Q=-0.9e6)
ic_in_he.set_attr(p=1, T=air_temp)
nw.solve('offdesign', design_path='heat_pump')
nw.print_results()
#
#T_range = [25, 45, 41, 37, 34, 31, 25]
#Q_range = np.array([0.9e6, 0.9e6])
#df = pd.DataFrame(columns=Q_range / -cons.Q.val)
#
#for T in T_range:
#    amb_in_su.set_attr(T=T)
#    eps = []
#
#    for Q in Q_range:
#        cons.set_attr(Q=-Q)
#        nw.solve('offdesign', design_path='heat_pump')
#
#        if nw.lin_dep:
#            eps += [np.nan]
#        else:
#            eps += [
#                abs(cd.Q.val) / (cp1.P.val + cp2.P.val + pu.P.val)
#            ]
#
#    df.loc[T] = eps
#
##df.to_csv('COP_water.csv')
#print(df)
