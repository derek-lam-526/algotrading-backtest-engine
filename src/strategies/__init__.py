from .mean_reversion.bollinger_reversion import BollingerReversion
from .trend.sma_cross import SmaCross
from .periodic.monthly_dca import MonthlyDCA

# list of all available strategies for easy iteration later
__all__ = [
    'BollingerReversion',
    'SmaCross',
    'MonthlyDCA'
]
