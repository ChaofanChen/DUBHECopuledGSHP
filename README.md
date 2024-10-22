# Coupled simulation of a DUBHE with a heat pump

This repository holds the data, python scripts for modeling and notebooks for
data preparation and evaluation of the results for the paper
"Thermal performance response and heat load redistribution mechanism of a deep
U-type borehole heat exchanger in heating systems" submitted to Applied Energy.

For the paper open source software for thermodynamic plant modeling
([Thermal Engineering Systems in Python](https://tespy.readthedocs.io): TESPy)
and for thermo-hydro-mechanical-chemical modeling of the subsurface
([OpenGeoSystems](https://www.opengeosys.org/): OGS) have been coupled.

- DUBHE: Deep U-Type Borehole Heat Exchanger
- GSHP: Ground Source Heat Pump

## Installation and usage

After downloading install the requirements within a fresh virtual environment:

```sh
python -m pip install -r requirements.txt
```

## Coupling Scheme

The two simulators have been coupled according to the figure below. The heat
demand time series controls the operation of the heat pump. Based on the heat
demand, the heat demand temperature level as well as the BHE flow rate and
outflow temperature the heat pump model calculates the BHE re-injection
temperature. Next, the DUBHE simulation is started to update the BHE outflow
temperature. Once convergence on the BHE outflow temperature has been reached,
the iteration process is started for the next time step in the heat demand time
series.

![Coupling scheme](./coupling_scheme.svg)

*Coupling scheme for OGS and TESPy*

## Literature

For the heat pump model TESPy has been used:

- Francesco Witte, Ilja Tuschy (2020). TESPy: Thermal Engineering Systems in
  Python. Journal of Open Source Software, 5(49), 2178,
  [10.21105/joss.02178](https://doi.org/10.21105/joss.02178)

For the subsurface model OGS has been used:

- Chaofan Chen, Wanlong Cai, Dmitri Naumov, Kun Tu, Hongwei Zhou,
  Yuping Zhang, Olaf Kolditz, and Haibing Shao (2021). Numerical investigation
  on the capacity and efficiency of a deep enhanced U-tube borehole heat
  exchanger system for building heating. Renewable Energy 169: 557-572. doi:
  [10.1016/j.renene.2021.01.033](https://doi.org/10.1016/j.renene.2021.01.033)

For the case study on integration of the DUBHE coupled GSHP demand data have
been used based on the following publication:

- Merlin Sebastian Triebs, Elisa Papadis, Hannes Cramer, George Tsatsaronis
  (2021). Landscape of district heating systems in Germany – Status quo and
  categorization. Energy Conversion and Management: X, 9, 100068, doi:
  [10.1016/j.ecmx.2020.100068](https://doi.org/10.1016/j.ecmx.2020.100068).

## License

Copyright (c) 2024 Francesco Witte, Chaofan Chen

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
