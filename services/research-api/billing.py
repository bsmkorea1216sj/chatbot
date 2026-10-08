"""Integer-only policy for the research service. Amounts use micro-KRW.

Persistence adapters must commit payment IDs, grants and reservations in one
Firestore transaction. This module never trusts browser-provided payment data.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING

MICRO = 1_000_000
MONTHLY_PRICE_KRW = 22_000
FREE_RUNS = 3

@dataclass(frozen=True)
class Balance:
    granted: int = 0
    spent: int = 0
    reserved: int = 0

    @property
    def available(self):
        return max(0, self.granted - self.spent - self.reserved)

def grant_for_payment(paid_krw: int) -> int:
    if type(paid_krw) is not int or paid_krw <= 0:
        raise ValueError('Verified positive integer KRW payment required')
    return paid_krw * MICRO // 2

def token_cost(input_tokens: int, output_tokens: int,
               input_usd_per_million: str, output_usd_per_million: str,
               krw_per_usd: str) -> int:
    """Use operator-configured, versioned prices and FX; no hardcoded rates."""
    if any(type(n) is not int or n < 0 for n in (input_tokens, output_tokens)):
        raise ValueError('Invalid provider token usage')
    rates = [Decimal(x) for x in (input_usd_per_million,
                                  output_usd_per_million, krw_per_usd)]
    if any(not x.is_finite() or x <= 0 for x in rates):
        raise ValueError('Invalid configured price or exchange rate')
    return int(((input_tokens*rates[0] + output_tokens*rates[1])*rates[2])
               .to_integral_value(rounding=ROUND_CEILING))

def reserve(balance: Balance, worst_case_cost: int) -> Balance:
    if type(worst_case_cost) is not int or worst_case_cost <= 0:
        raise ValueError('A bounded positive task cost is required')
    if worst_case_cost > balance.available:
        raise PermissionError('TOP_UP_REQUIRED')
    return Balance(balance.granted, balance.spent,
                   balance.reserved + worst_case_cost)

def settle(balance: Balance, reserved_cost: int, actual_cost: int) -> Balance:
    if any(type(n) is not int or n < 0 for n in (reserved_cost, actual_cost)):
        raise ValueError('Invalid cost')
    if reserved_cost > balance.reserved:
        raise ValueError('Reservation mismatch')
    # Provider expenses remain recorded even if a report later fails to save.
    return Balance(balance.granted, balance.spent + actual_cost,
                   balance.reserved - reserved_cost)

def free_eligible(successes: int, pending: int, mode: str) -> bool:
    if any(type(n) is not int or n < 0 for n in (successes, pending)):
        raise ValueError('Invalid free usage counts')
    return mode == 'basic' and successes + pending < FREE_RUNS
