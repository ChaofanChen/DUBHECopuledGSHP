# -*- coding: utf-8 -*-
from tespy.networks import Network
from tespy.components import (
    Sink, Source, Splitter, Compressor, Condenser, Pump, HeatExchangerSimple,
    Valve, Drum, HeatExchanger, CycleCloser
)
from tespy.connections import Connection, Ref
from tespy.tools.characteristics import CharLine
from tespy.tools.characteristics import load_default_char as ldc
from tespy.tools import document_model

import numpy as np
import pandas as pd

# %% network

nw = Network(
    fluids=['water', 'NH3'], T_unit='C', p_unit='bar', h_unit='kJ / kg',
    m_unit='kg / s'
)

# %% components

# sources & sinks
cc = CycleCloser('coolant cycle closer')
cc_cons = CycleCloser('consumer cycle closer')
amb = Source('ambient air')
amb_out1 = Sink('sink ambient 1')
amb_out2 = Sink('sink ambient 2')

# ambient system
sp = Splitter('splitter')
pu = Pump('pump')

# consumer system

cd = Condenser('condenser')
dhp = Pump('district heating pump')
cons = HeatExchangerSimple('consumer')

# evaporator system

ves = Valve('valve')
dr = Drum('drum')
ev = HeatExchanger('evaporator')
su = HeatExchanger('superheater')
erp = Pump('evaporator reciculation pump')

# compressor-system

cp1 = Compressor('compressor 1')
cp2 = Compressor('compressor 2')
ic = HeatExchanger('intercooler')

# %% connections

# consumer system

c_in_cd = Connection(cc, 'out1', cd, 'in1')

cb_dhp = Connection(cc_cons, 'out1', dhp, 'in1')
dhp_cd = Connection(dhp, 'out1', cd, 'in2')
cd_cons = Connection(cd, 'out2', cons, 'in1')
cons_cf = Connection(cons, 'out1', cc_cons, 'in1')

nw.add_conns(c_in_cd, cb_dhp, dhp_cd, cd_cons, cons_cf)

# connection condenser - evaporator system

cd_ves = Connection(cd, 'out1', ves, 'in1')

nw.add_conns(cd_ves)

# evaporator system

ves_dr = Connection(ves, 'out1', dr, 'in1')
dr_erp = Connection(dr, 'out1', erp, 'in1')
erp_ev = Connection(erp, 'out1', ev, 'in2')
ev_dr = Connection(ev, 'out2', dr, 'in2')
dr_su = Connection(dr, 'out2', su, 'in2')

nw.add_conns(ves_dr, dr_erp, erp_ev, ev_dr, dr_su)

amb_p = Connection(amb, 'out1', pu, 'in1')
p_sp = Connection(pu, 'out1', sp, 'in1')
sp_su = Connection(sp, 'out1', su, 'in1')
su_ev = Connection(su, 'out1', ev, 'in1')
ev_amb_out = Connection(ev, 'out1', amb_out1, 'in1')

nw.add_conns(amb_p, p_sp, sp_su, su_ev, ev_amb_out)

# connection evaporator system - compressor system

su_cp1 = Connection(su, 'out2', cp1, 'in1')

nw.add_conns(su_cp1)

# compressor-system

cp1_he = Connection(cp1, 'out1', ic, 'in1')
he_cp2 = Connection(ic, 'out1', cp2, 'in1')
cp2_c_out = Connection(cp2, 'out1', cc, 'in1')

sp_ic = Connection(sp, 'out2', ic, 'in2')
ic_out = Connection(ic, 'out2', amb_out2, 'in1')

nw.add_conns(cp1_he, he_cp2, sp_ic, ic_out, cp2_c_out)

# %% component parametrization

# condenser system

cd.set_attr(pr1=0.99, pr2=0.99, ttd_u=5, design=['pr2', 'ttd_u'],
            offdesign=['zeta2', 'kA_char'])
dhp.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])
cons.set_attr(pr=0.99, design=['pr'], offdesign=['zeta'])

# water pump

pu.set_attr(eta_s=0.75, design=['eta_s'], offdesign=['eta_s_char'])

# evaporator system

kA_char1 = ldc('heat exchanger', 'kA_char1', 'DEFAULT', CharLine)
kA_char2 = ldc('heat exchanger', 'kA_char2', 'EVAPORATING FLUID', CharLine)

ev.set_attr(pr1=0.98, pr2=0.99, ttd_l=5,
            kA_char1=kA_char1, kA_char2=kA_char2,
            design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char'])
su.set_attr(pr1=0.98, pr2=0.99, ttd_u=2, design=['pr1', 'pr2', 'ttd_u'],
            offdesign=['zeta1', 'zeta2', 'kA_char'])
erp.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])

# compressor system

cp1.set_attr(eta_s=0.85, pr=3, design=['eta_s'], offdesign=['eta_s_char'])
cp2.set_attr(eta_s=0.9, pr=3, design=['eta_s'], offdesign=['eta_s_char'])
ic.set_attr(pr1=0.99, pr2=0.98, ttd_l=3, design=['pr1', 'pr2'],
            offdesign=['zeta1', 'zeta2', 'kA_char'])

# %% connection parametrization

# condenser system

c_in_cd.set_attr(fluid={'NH3': 1, 'water': 0})
cb_dhp.set_attr(T=60, p=10, fluid={'NH3': 0, 'water': 1})
cd_cons.set_attr(T=90)

# evaporator system cold side

erp_ev.set_attr(m=Ref(ves_dr, 1.25, 0), p0=5)
su_cp1.set_attr(p0=5, state='g')

# evaporator system hot side

T_pro=40
m_pro=15

T_re=20

# pumping at constant rate in partload
amb_p.set_attr(T=T_pro, p=2, m=m_pro, fluid={'NH3': 0, 'water': 1},
               offdesign=['v'])
sp_su.set_attr(offdesign=['v'])
#ev_amb_out.set_attr(p=2, T=T_re, design=['T'])

# compressor-system

he_cp2.set_attr(Td_bp=5, p0=20, design=['Td_bp'])
#ic_out.set_attr(T=T_re, design=['T'])

# %% key paramter

cons.set_attr(Q=-1.225e6)

# %% Calculation

nw.solve('design')
nw.print_results()
nw.save('heat_pump_water')
# document_model(nw, filename='report_water_design.tex')

# offdesign test
#nw.solve('offdesign', design_path='heat_pump_water')
# document_model(nw, filename='report_water_offdesign.tex')

#T_range = [6, 12, 18, 24, 30]
#Q_range = np.array([100e3, 120e3, 140e3, 160e3, 180e3, 200e3, 220e3])
#df = pd.DataFrame(columns=Q_range / -cons.Q.val)
#
#for T in T_range:
#    amb_p.set_attr(T=T)
#    eps = []
#
#    for Q in Q_range:
#        cons.set_attr(Q=-Q)
#        nw.solve('offdesign', design_path='heat_pump_water')
#
#        if nw.lin_dep:
#            eps += [np.nan]
#        else:
#            eps += [
#                abs(cd.Q.val) / (cp1.P.val + cp2.P.val + erp.P.val + pu.P.val)
#            ]
#
#    df.loc[T] = eps
#
#df.to_csv('COP_water.csv')
