import CoolProp.CoolProp as CP
from tespy.networks import Network
from tespy.components import (
    Compressor, Valve, HeatExchanger, CycleCloser, Source, Sink, Pump,
    HeatExchanger, HeatExchangerSimple
)
from tespy.connections import Bus, Connection, Ref


class HeatPumpModel():

    def __init__(self, param) -> None:

        self.param = param
        self.working_fluid = self.param["working_fluid"]

        self.nw = Network(
            fluids=[self.working_fluid, "water"], p_unit="bar", T_unit="C"
        )

        # Refrigerant Cylce
        compressor = Compressor("Compressor")
        valve = Valve("Valve")
        evaporator = HeatExchanger("Evaporator")
        condenser = HeatExchangerSimple("Condenser")
        cycle_closer = CycleCloser("Cycle Closer")

        # Heat Source
        bhe_prod = Source('BHE production')
        bhe_inj = Sink('BHE injection')
        bhe_pump = Pump('BHE Circulation Pump')

        # Refrigerant Cylce
        c0 = Connection(cycle_closer, "out1", condenser, "in1", label="0")
        c1 = Connection(condenser, "out1", valve, "in1", label="1")
        c2 = Connection(valve, "out1", evaporator, "in2", label="2")
        c3 = Connection(evaporator, "out2", compressor, "in1", label="3")
        c4 = Connection(compressor, "out1", cycle_closer, "in1", label="4")

        self.nw.add_conns(c0, c1, c2, c3, c4)

        # Heat Source
        c11 = Connection(bhe_prod, "out1", evaporator, "in1", label="11")
        c12 = Connection(evaporator, "out1", bhe_pump, "in1", label="12")
        c13 = Connection(bhe_pump, "out1", bhe_inj, "in1", label="13")

        self.nw.add_conns(c11, c12, c13)

        evaporator.set_attr(pr1=0.98, pr2=1)
        condenser.set_attr(pr=1)

        bhe_pump.set_attr(eta_s=0.75, design=["eta_s"], offdesign=["eta_s_char"])

        compressor.set_attr(eta_s=0.85, design=["eta_s"], offdesign=["eta_s_char"])

        c0.set_attr(fluid={self.working_fluid: 1, "water": 0})
        c1.set_attr(x=0, p=CP.PropsSI(
            "P", "T", self.param["T_sink"] + 273.15,
            "Q", 0, self.working_fluid
        ) / 1e5
                    )
        c3.set_attr(x=1, p=CP.PropsSI(
            "P", "T", self.param["T_bhe"] + 273.15,
            "Q", 1, self.working_fluid
        ) / 1e5
                    )

        c11.set_attr(
            T=self.param["T_bhe"] + 2,
            p=self.param["p_bhe"],
            fluid={self.working_fluid: 0, "water": 1}
        )
        c13.set_attr(
            T=self.param["T_bhe"] - 2,
            p=self.param["p_bhe"]
        )

        power_bus = Bus("power input")
        power_bus.add_comps(
            {"comp": compressor, "char": 0.97, "base": "bus"},
            {"comp": bhe_pump, "char": 0.97, "base": "bus"},
        )

        heat_bus = Bus("heat output")
        heat_bus.add_comps(
            {"comp": condenser, "char": -1}
        )

        self.nw.add_busses(power_bus, heat_bus)

        condenser.set_attr(Q=self.param["Q_design"])

        self.nw.set_attr(iterinfo=False)
        self.nw.solve("design")

        c3.set_attr(p=None)
        evaporator.set_attr(ttd_l=5)

        self.nw.solve("design")

        evaporator.set_attr(design=["ttd_l"], offdesign=["kA_char"])

        condenser.set_attr()
        c1.set_attr()

        self.stable_solution_path = f"stable_solution_{self.working_fluid}"
        self.nw.save(self.stable_solution_path)

    def get_parameters(self, **kwargs):

        result = kwargs.copy()
        if "Connections" in kwargs:
            for c, params in kwargs["Connections"].items():
                result["Connections"][c] = {}
                for param in params:
                    result["Connections"][c][param] = self.nw.get_conn(c).get_attr(param).val

        return result

    def get_param(self, obj, label, parameter):
        return self.get_single_parameter(obj, label, parameter)

    def get_single_parameter(self, obj, label, parameter):
        if obj == "Components":
            return self.nw.get_comp(label).get_attr(parameter).val
        elif obj == "Connections":
            return self.nw.get_conn(label).get_attr(parameter).val

    def set_parameters(self, **kwargs):

        if "Connections" in kwargs:
            for c, params in kwargs["Connections"].items():
                self.nw.get_conn(c).set_attr(**params)

        if "Components" in kwargs:
            for c, params in kwargs["Components"].items():
                self.nw.get_comp(c).set_attr(**params)

    def set_single_parameter(self, obj, label, parameter, value):
        if obj == "Components":
            self.nw.get_comp(label).set_attr(**{parameter: value})
        elif obj == "Connections":
            self.nw.get_conn(label).set_attr(**{parameter: value})

    def solve_design(self, **kwargs):

        self.set_parameters(**kwargs)

        self.solved = False
        try:
            self.nw.solve("design")
            if all(self.nw.results['HeatExchanger']['Q'] < 0):
                self.solved = True
        except ValueError as e:
            print(e)
            self.nw.lin_dep = True
            self.nw.solve(
                "design", init_only=True,
                init_path=self.stable_solution_path
            )

    def solve_offdesign(self, **kwargs):
        self.set_parameters(**kwargs)

        self.solved = False
        try:
            self.nw.solve(
                "offdesign",
                design_path=self.design_path
            )
            if all(self.nw.results['HeatExchanger']['Q'] < 0):
                self.solved = True
        except ValueError as e:
            print(e)
            self.nw.solve(
                "offdesign", init_only=True,
                init_path=self.stable_solution_path,
                design_path=self.design_path
            )

    def get_COP_value(self):
        return self.nw.busses['heat output'].P.val / self.nw.busses['power input'].P.val


## outside of iteration

data = {
    "working_fluid": "R410A",
    "T_bhe": 35,
    "p_bhe": 1.5,
    "T_sink": 65,
    "Q_design": -1e6,
}
a = HeatPumpModel(data)

a.solve_design(**data)
a.design_path = f"design_path_{a.working_fluid}"
a.nw.save(a.design_path)
a.nw.print_results()
#
# demand_data = pd.DataFrame(columns=["heat_demand"])
# demand_data.loc[0] = ...
# demand_data.loc[1] = ...

####
a.nw.get_conn("13").set_attr(T=None)
a.nw.get_conn("11").set_attr(T=21.06, v=0.01295)
# a.nw.get_conn("11").set_attr(v=0.01)
a.nw.get_comp("Condenser").set_attr(Q=-10e5)
a.solve_offdesign()

T_bhe_previous = a.get_param("Connections", "11", "T")
Q_previous = a.get_param("Components", "Condenser", "Q")

import numpy as np

T_list = [45, 15, 30, 25, 35, 40, 15, 35, 25]
Q_list = np.array([2.5, 4, 7.5, 8, 4, 10, 9.2, 10.5, 3]) * -1e5

COP_List = []
carnot_COP = []

for T, Q in zip(T_list, Q_list):

    num = int(abs(T - T_bhe_previous) // 5) + 1
    T_range = np.linspace(T, T_bhe_previous, num, endpoint=False)[::-1]
    num = int(abs(Q - Q_previous) // 2.5e5) + 1
    Q_range = np.linspace(Q, Q_previous, num, endpoint=False)[::-1]

    for T_step in T_range:
        a.nw.get_conn("11").set_attr(T=T_step)
        a.solve_offdesign()
    for Q_step in Q_range:
        a.nw.get_comp("Condenser").set_attr(Q=Q_step)
        a.solve_offdesign()

    if a.solved:
        return_params = a.get_param("Connections", "13", "T")
        print("T_return:", return_params)
        cop = a.get_COP_value()
        print('COP', cop)
        COP_List += [cop]
        carnot_COP += [(data["T_sink"] + 273.15) / (data["T_sink"] - a.get_param("Connections", "2", "T"))]
    else:
        print("ERROR")

import matplotlib.pyplot as plt


fig, ax = plt.subplots(1, 2)

ax[0].scatter(T_list, COP_List)
ax[0].scatter(T_list, carnot_COP)
ax[1].scatter(Q_list, COP_List)

ax[0].set_ylabel("COP")
ax[0].set_xlabel("BHE outlet temperature")
ax[1].set_xlabel("Heat demand")

plt.show()
