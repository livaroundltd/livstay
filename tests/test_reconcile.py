"""Deadline ordering in tools/reconcile.py. Run: python3 tests/test_reconcile.py"""
import copy, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from reconcile import quote_problems

q = json.load(open(os.path.join(HERE, "..", "fixtures", "0.2", "valid", "quote.json")))
failed = 0


def expect(name, quote, ok):
    global failed
    probs = [p for p in quote_problems(quote) if "deadline" in p]
    good = (not probs) == ok
    failed += not good
    print(f"{'ok  ' if good else 'FAIL'} {name}: {probs or 'no deadline problems'}")


a = copy.deepcopy(q)
a["cancellation"][0]["until"], a["cancellation"][1]["until"] = "2026-12-13T08:30:00Z", "2026-12-13T08:30:00.500Z"
expect("fractional seconds in chronological order pass", a, True)
b = copy.deepcopy(a)
b["cancellation"][0]["until"], b["cancellation"][1]["until"] = b["cancellation"][1]["until"], b["cancellation"][0]["until"]
expect("the same deadlines reversed fail", b, False)
c = copy.deepcopy(q); c["cancellation"][1]["until"] = c["cancellation"][0]["until"]
expect("duplicate deadlines fail", c, False)
sys.exit(1 if failed else 0)
