from .mean_reversion.bollinger_reversion import BollingerReversion
from .mean_reversion.lrc_reversion import LrcReversion
from .trend.sma_cross import SmaCross
from .trend.parabolic_trail import ParabolicTrail
from .trend.macd_cross import MacdCross
from .periodic.monthly_dca import MonthlyDCA

# list of all available strategies for easy iteration later
__all__ = [
    'BollingerReversion',
    'SmaCross',
    'MonthlyDCA',
    'MacdCross',
]
