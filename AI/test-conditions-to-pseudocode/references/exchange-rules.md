# Exchange Rules

Use the following pseudocode vocabulary:

- `FV[...]`: apply voltage, for example `FV[VIN=10V,OUT=12V]`
- `FI[...]`: apply current, for example `FI[VIN=20mA,OUT=-500mA]`
- `Float[...]`: float pins or nodes
- `RampV[...]`: sweep voltage, for example `RampV[VIN,1V,2V,20mV]`
- `RampI[...]`: sweep current, for example `RampI[VIN,1mA,20mA,1mA]`
- `MV[...]`: measure voltage
- `MI[...]`: measure current
- `MT[...]`: measure time between events
- `Connect[...]`: connect external components, for example `Connect[VIN-10R-GND,OUT-10uF-GND]`
- `Display[...]`: derive or emit a result expression
- `Delay[...]`: wait for a time interval
- `WR[...]`: write registers

Interpretation notes:

- Convert natural-language setup conditions into `FV`, `FI`, `Float`, `RampV`, `RampI`, and `Connect`.
- Convert natural-language measurement actions into `MV`, `MI`, `MT`, and `Display`.
- Prefer concise pseudocode sequences separated by commas.
- Keep unknown or ambiguous text in a `Display[...]` note only when no deterministic conversion is possible.
