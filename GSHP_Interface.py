###
# Copyright (c) 2012-2020, OpenGeoSys Community (http://www.opengeosys.org)
# Distributed under a Modified BSD License.
# See accompanying file LICENSE.txt or
# http://www.opengeosys.org/project/license
###

import sys
print(sys.version)
import os
import numpy as np
import OpenGeoSys
from heatpumpmodel import HeatPumpModel

# network status setting
def network_status(t):
    nw_status = 'on'
    # month for closed network
    timerange_nw_off_month = [-9999]  # No month for closed network
    # t-1 to avoid the calculation problem at special time point,
    # e.g. t = 2592000.
    t_trans = int((t - 1) / 86400 / 30) + 1
    t_trans_month = t_trans
    if t_trans_month > 12:
        t_trans_month = t_trans - 12 * (int(t_trans / 12))
    if t_trans_month in timerange_nw_off_month:
        nw_status = 'off'
    return nw_status

def castToList(x): #casts x to a list
    if isinstance(x, list):
        return x
    elif isinstance(x, str):
        return [x]
    try:
        return list(x)
    except TypeError:
        return [x]

# OGS setting
# Dirichlet BCs
class BC(OpenGeoSys.BHENetwork):
    def initializeDataContainer(self):
        print('info: Initialize TESPy')
        t = 0  # 'initial time'
        Tout_val = [35]  # 'Tout_val'
        Tout_node_id = [1] # 'Tout_node_id'

        self.data = {
            "working_fluid": "R410A",
            "T_bhe": Tout_val[0],
            "p_bhe": 1.5,
            "T_sink": 65,
            "Q_design": -1e6,
        }
        self.heatpump = HeatPumpModel(self.data)        
        self.heatpump.solve_design(**self.data)

        if self.heatpump.solved:
            self.heatpump.nw.print_results()
            self.heatpump.design_path = f"design_path_{self.heatpump.working_fluid}"
            self.heatpump.nw.save(self.heatpump.design_path)
            T_bhe_reinj = self.heatpump.get_param("Connections", "13", "T")
            v_bhe = self.heatpump.get_param("Connections", "13", "v")
        else:
            print("ERROR")

        print('BHE trial re-injection temperature = ',
              self.heatpump.get_param("Connections", "13", "T"))
        print('BHE trial flow rate = ',
              self.heatpump.get_param("Connections", "13", "v"))
        return (t, castToList(T_bhe_reinj), Tout_val, Tout_node_id, castToList(v_bhe))

    def tespySolver(self, t, Tin_val, Tout_val):
        # network status:
        nw_status = network_status(t)
        # if network closed:
        print('nw_status = ', nw_status)
        if nw_status == 'off':
            return (True, True, Tout_val)
        else:
            # TESPy solver
            print('BHE production temperature = ', Tout_val[0])
            
            self.heatpump.nw.get_conn("11").set_attr(T=Tout_val[0]) 
            self.heatpump.nw.get_conn("13").set_attr(T=None, v=0.01295) # v is the flow rate 
            self.heatpump.nw.get_comp("Condenser").set_attr(Q=-5.8e5)
            print('info: Calculate off-design performance')
            self.heatpump.solve_offdesign(**self.data)

            if self.heatpump.solved:
                if_success = True
                self.heatpump.nw.print_results()
                T_bhe_reinj = self.heatpump.get_param("Connections", "13", "T")
                v_bhe = self.heatpump.get_param("Connections", "13", "v")
            else:
                print("ERROR")

            # return to OGS
            print('BHE re-injection temperature = ', castToList(T_bhe_reinj))
            print('BHE flow rate = ', castToList(v_bhe))
            return (True, if_success, castToList(T_bhe_reinj), castToList(v_bhe))

if ogs_prj_directory != "":
    os.chdir(ogs_prj_directory)
# instantiate BC objects referenced in OpenGeoSys
bc_bhe = BC()
