# Source: The DriftNet Protocol (technical note)

DriftNet is a low-bandwidth data protocol for transmitting sensor readings from
remote marine buoys. It was developed by the Marren Lab specifically for the
Tidewatch project. DriftNet packets carry a calibration header whose values are
produced by the Kelp Calibration method; without a valid Kelp calibration, a
DriftNet packet is rejected as untrusted. DriftNet tolerates intermittent
connectivity by buffering readings locally.
