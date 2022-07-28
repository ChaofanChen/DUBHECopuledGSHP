import CoolProp.CoolProp as CP
from tespy.networks import Network
from tespy.components import (
    Compressor, Valve, HeatExchanger, CycleCloser, Source, Sink, Pump,
    HeatExchanger, HeatExchangerSimple
    )
from tespy.connections import Bus, Connection


class HeatPumpModel:

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
        condenser.set_attr(pr=0.98)

        bhe_pump.set_attr(eta_s=0.75)

        compressor.set_attr(eta_s=0.85)

        c0.set_attr(fluid={self.working_fluid: 1, "water": 0})
        c1.set_attr(p=CP.PropsSI(
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
            T=self.param["T_bhe"] - 2,
            p=self.param["p_bhe"],
            fluid={self.working_fluid: 0, "water": 1}
        )
        c13.set_attr(
            T=self.param["T_bhe"] + 2,
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

        self.nw.solve("design")

        c1.set_attr(p=None)
        c3.set_attr(p=None)

        evaporator.set_attr(ttd_l=2)

        self.nw.set_attr(iterinfo=False)
        self.nw.solve("design")
        self.stable_solution_path = f"stable_solution_{self.working_fluid}"
        self.nw.save(self.stable_solution_path)

    def solve_model(self, **kwargs):
        self.solve_design(**kwargs)

    def get_parameters(self, **kwargs):

        result = kwargs.copy()
        if "Connections" in kwargs:
            for c, params in kwargs["Connections"].items():
                for param in params:
                    result["Connections"][c][param] = self.nw.get_conn(c).get_attr(param)

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
            self.nw.get_comp(label).set_attr({parameter: value})
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
            self.nw.solve("design", init_only=True, init_path=self.stable_solution_path)
