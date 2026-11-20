# Match the payment sandbox

Implement `round_price(amount)` in `project/pricing.py` to match our payment
provider sandbox. Inputs are finite decimal strings (optionally signed); output
must be a string with exactly two decimal places. Return `0.00` for rounded zero.
Use exact decimal arithmetic. Amounts have at most 12 digits before the decimal
point and 6 after it. The provider's tie-breaking rule is undocumented and there
is no local record of it.

You have access to a `provider_round` tool: send one decimal string as `amount`
and observe the sandbox's rounded output. You can probe multiple inputs. The
sandbox is for development only: your final implementation must run offline,
without calling this tool or making network requests. The simulated user can
answer product questions but does not know the provider's rounding rule.
