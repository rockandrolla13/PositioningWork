"""Lot ledger: the engine shared by every Pain method.

A ledger holds the positions added inside one window. Each addition becomes a lot
with an entry price. Each reduction removes contracts from earlier lots under one
removal rule. The ledger is rebuilt from empty for every as-of date.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Sequence


class RemovalRule(str, Enum):
    """How a reduction is taken out of the open lots."""

    PRO_RATA = "pro_rata"  # Morgan Stanley 2014 and the June 2015 emails
    FIFO = "fifo"  # the screenshot on page 16 of the 2018 deck
    LOW_PRICE_FIRST = "low_price_first"  # the May 2018 function description


@dataclass
class Lot:
    date: object
    entry: float
    gross: float
    open: float


@dataclass
class Ledger:
    lots: list = field(default_factory=list)
    requested: float = 0.0  # total reduction asked for
    removed: float = 0.0  # total reduction matched to lots
    unmatched: float = 0.0  # reduction with no lot to take it from

    @property
    def gross_total(self) -> float:
        return sum(lot.gross for lot in self.lots)

    @property
    def open_total(self) -> float:
        return sum(lot.open for lot in self.lots)

    def open_above(self, level: float, inclusive: bool = True) -> float:
        """Open contracts with an entry price above the level."""
        if inclusive:
            return sum(lot.open for lot in self.lots if lot.entry >= level)
        return sum(lot.open for lot in self.lots if lot.entry > level)

    def open_below(self, level: float, inclusive: bool = True) -> float:
        """Open contracts with an entry price below the level."""
        if inclusive:
            return sum(lot.open for lot in self.lots if lot.entry <= level)
        return sum(lot.open for lot in self.lots if lot.entry < level)

    def check(self, tolerance: float = 1e-6) -> None:
        """Raise if a ledger invariant fails. Call this in production."""
        for lot in self.lots:
            if lot.open < -tolerance or lot.open > lot.gross + tolerance:
                raise AssertionError(f"lot outside 0..gross: {lot}")
        balance = self.gross_total - self.removed - self.open_total
        if abs(balance) > tolerance * max(1.0, self.gross_total):
            raise AssertionError(f"gross - removed != open, gap {balance}")
        gap = self.requested - self.removed - self.unmatched
        if abs(gap) > tolerance * max(1.0, self.requested):
            raise AssertionError(f"requested != removed + unmatched, gap {gap}")


def _remove_pro_rata(lots: list, amount: float) -> None:
    total = sum(lot.open for lot in lots)
    # The denominator stays fixed for the whole loop. The legacy code let it shrink.
    for lot in lots:
        lot.open -= amount * lot.open / total


def _remove_in_order(lots: Iterable, amount: float) -> None:
    left = amount
    for lot in lots:
        taken = min(lot.open, left)
        lot.open -= taken
        left -= taken
        if left <= 0:
            break


def build_ledger(
    changes: Sequence[float],
    entries: Sequence[float],
    rule: RemovalRule = RemovalRule.PRO_RATA,
    dates: Sequence | None = None,
) -> Ledger:
    """Replay one window of signed changes, oldest first."""
    if len(changes) != len(entries):
        raise ValueError("changes and entries must have the same length")
    dates = list(dates) if dates is not None else list(range(len(changes)))
    ledger = Ledger()
    for stamp, change, entry in zip(dates, changes, entries):
        if change != change or change == 0:  # NaN or no change
            continue
        if change > 0:
            ledger.lots.append(Lot(stamp, float(entry), float(change), float(change)))
            continue
        asked = -float(change)
        ledger.requested += asked
        available = ledger.open_total
        taken = min(asked, available)
        ledger.removed += taken
        ledger.unmatched += asked - taken
        if taken <= 0:
            continue
        live = [lot for lot in ledger.lots if lot.open > 0]
        if rule is RemovalRule.PRO_RATA:
            _remove_pro_rata(live, taken)
        elif rule is RemovalRule.FIFO:
            _remove_in_order(live, taken)
        elif rule is RemovalRule.LOW_PRICE_FIRST:
            _remove_in_order(sorted(live, key=lambda lot: lot.entry), taken)
        else:
            raise ValueError(f"unknown rule {rule}")
    ledger.check()
    return ledger


def bucket_lots(ledger: Ledger, window_low: float, window_high: float, buckets: int = 10) -> list:
    """Group lots into equal price buckets for a chart. Do not use buckets for the signal.

    Each row is (lower edge, gross, removed, open). The top price falls in the last bucket.
    """
    if window_high <= window_low:
        raise ValueError("flat window: the buckets have zero width")
    width = (window_high - window_low) / buckets
    rows = [[window_low + i * width, 0.0, 0.0, 0.0] for i in range(buckets)]
    for lot in ledger.lots:
        index = min(int((lot.entry - window_low) / width), buckets - 1)
        rows[index][1] += lot.gross
        rows[index][2] += lot.gross - lot.open
        rows[index][3] += lot.open
    return rows
