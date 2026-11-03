import ast
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from multipliers import DEFAULT_FG_MULTIPLIERS, fg_multiplier
from strategy import DCAConfig, ZionSmartDCA, MarketSignals, CyclePhase

class MultiplierTests(unittest.TestCase):
    def test_all_boundaries(self):
        engine = ZionSmartDCA()
        for fg, expected in [(0,2),(24,2),(25,1.5),(44,1.5),(45,1),(55,1),(56,.5),(74,.5),(75,.25),(100,.25)]:
            with self.subTest(fg=fg):
                self.assertEqual(fg_multiplier(fg), expected)
                self.assertEqual(engine._get_fg_multiplier(fg)[0], expected)

    def test_personalized_profile(self):
        profile = (1.8,1.3,1,.4,.1)
        engine = ZionSmartDCA(DCAConfig(fg_multipliers=profile))
        for fg, expected in zip((0,25,45,56,75),profile):
            self.assertEqual(engine._get_fg_multiplier(fg)[0], expected)

    def test_cycle_floor_respects_base_and_personalization(self):
        for profile, expected in [(DEFAULT_FG_MULTIPLIERS, .25), ((1.8,1.3,1,.4,.1), .1)]:
            engine=ZionSmartDCA(DCAConfig(fg_multipliers=profile))
            signals=MarketSignals(btc_price_usd=70000,fear_greed_index=90,rsi_14d=50)
            with patch.object(engine, '_get_cycle_adjustment', return_value=(-.25, 'test reduction')):
                decision=engine.evaluate(signals)
            self.assertEqual(decision.multiplier,expected)

    def test_positive_cycle_adjustment_is_preserved(self):
        engine=ZionSmartDCA()
        signals=MarketSignals(btc_price_usd=70000,fear_greed_index=90,rsi_14d=50)
        with patch.object(engine, '_get_cycle_adjustment', return_value=(.25, 'test increase')):
            self.assertEqual(engine.evaluate(signals).multiplier,.5)

    def test_invalid_values(self):
        for fg in (-1,101,float('nan')):
            with self.assertRaises(ValueError): fg_multiplier(fg)
        for profile in ((1,2), (2,1.5,1,.5,-1), (2,1.5,1,.5,float('inf'))):
            with self.assertRaises(ValueError): fg_multiplier(50,profile)

    def test_dashboard_parity(self):
        html = (ROOT / 'dashboard/index.html').read_text()
        table = html.split('const FG_TABLE = [',1)[1].split('];',1)[0]
        self.assertEqual(tuple(map(float,re.findall(r'multiplier:\s*([\d.]+)',table))),DEFAULT_FG_MULTIPLIERS)

    def test_simulators_without_running_or_importing_side_effects(self):
        cfg=dict(fg_extreme_fear=24,fg_fear_top=44,fg_neutral_top=55,fg_greed_top=74)
        for path,name in [('backtest/backtest.py','get_fg_multiplier'),('backtest/live_simulation.py','get_multiplier')]:
            tree=ast.parse((ROOT/path).read_text())
            node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
            ns=dict(fg_multiplier=fg_multiplier,DEFAULT_FG_MULTIPLIERS=DEFAULT_FG_MULTIPLIERS)
            exec(compile(ast.Module(body=[node],type_ignores=[]),path,'exec'),ns)
            for fg in range(101):
                actual=ns[name](fg,cfg) if name=='get_fg_multiplier' else ns[name](fg)
                self.assertEqual(actual,fg_multiplier(fg))

if __name__=='__main__': unittest.main()
