import unittest
from simulator import BASE_COSTS, evaluate
from storage import latest_per_group

class SimulatorTests(unittest.TestCase):
    def setUp(self):
        self.zero={k:0 for k in BASE_COSTS}

    def test_baseline(self):
        m=evaluate(self.zero)
        self.assertAlmostEqual(m['revenue_p1'],100)
        self.assertAlmostEqual(m['cost_p1'],135)
        self.assertAlmostEqual(m['profit_p1'],-35)
        self.assertAlmostEqual(m['satisfaction'],85)
        self.assertFalse(m['investor_approved'])

    def test_invalid(self):
        bad=dict(self.zero)
        bad['Discounts']=80
        with self.assertRaises(ValueError):evaluate(bad)

    def test_discount_reduces_demand(self):
        cuts=dict(self.zero)
        cuts['Discounts']=25
        m=evaluate(cuts)
        self.assertLess(m['revenue_p1'],100)
        self.assertLess(m['retention'],0.85)

    def test_tech_cut_affects_satisfaction(self):
        cuts=dict(self.zero)
        cuts['Technology']=30
        self.assertLess(evaluate(cuts)['satisfaction'],85)

    def test_latest(self):
        rows=[{'section':'A','group_id':'1','timestamp_utc':'2026-01-01','submission_id':'x'},
              {'section':'A','group_id':'1','timestamp_utc':'2026-01-02','submission_id':'y'},
              {'section':'B','group_id':'1','timestamp_utc':'2026-01-01','submission_id':'z'}]
        latest=latest_per_group(rows)
        self.assertEqual(len(latest),2)
        self.assertEqual(next(r for r in latest if r['section']=='A')['submission_id'],'y')

if __name__=='__main__':unittest.main()
