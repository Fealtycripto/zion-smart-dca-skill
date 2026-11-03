"""Current Smart DCA base; personalize after a financial/patrimonial assessment."""
from math import isfinite

DEFAULT_FG_MULTIPLIERS = (2.0, 1.5, 1.0, 0.5, 0.25)
DEFAULT_FG_THRESHOLDS = (24, 44, 55, 74)
FG_LABELS = ("Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed")


def get_fg_band(fg, thresholds=DEFAULT_FG_THRESHOLDS):
    if not isfinite(fg) or not 0 <= fg <= 100:
        raise ValueError("Fear & Greed must be between 0 and 100")
    if len(thresholds) != 4 or not all(0 <= t < 100 for t in thresholds) or any(a >= b for a, b in zip(thresholds, thresholds[1:])):
        raise ValueError("Four strictly increasing F&G thresholds are required")
    return next((i for i, threshold in enumerate(thresholds) if fg <= threshold), 4)


def validate_multipliers(multipliers):
    if len(multipliers) != 5 or any(not isfinite(m) or m < 0 for m in multipliers):
        raise ValueError("Five finite, nonnegative multipliers are required")


def fg_multiplier(fg, multipliers=DEFAULT_FG_MULTIPLIERS, thresholds=DEFAULT_FG_THRESHOLDS):
    validate_multipliers(multipliers)
    return multipliers[get_fg_band(fg, thresholds)]
