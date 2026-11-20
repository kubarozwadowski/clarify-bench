# Clamp a quantity

Implement `clamp_quantity(value, minimum=1, maximum=99)` in
`project/quantities.py`. Inputs are integers. Return minimum when value is below
minimum, maximum when above maximum, and value otherwise. Bounds are inclusive.
Raise ValueError if minimum > maximum, even when value is inside either bound.
Do not change the public signature. No behavior for noninteger inputs is required.
Run the available tests.
