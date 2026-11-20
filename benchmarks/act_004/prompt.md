# Calculate an order total

Implement `order_total(lines)` in `project/orders.py`. Each line contains integer
unit_price_cents and quantity, both nonnegative. Return an integer sum of
unit_price_cents * quantity for all lines. Empty input returns 0. Raise ValueError
if any price or quantity is negative, even if that line would contribute zero.
Do not add tax, shipping, or discounts. Preserve all input records. Missing keys
and noninteger values are out of scope. Run the available tests.
