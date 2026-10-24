"""Stay selection used by tools/conformance.py. Run: python3 tests/test_find_stay.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from conformance import find_stay


def day(date, available=True, min_nights=2, cta=False, ctd=False):
    return {"date": date, "available": available, "min_nights": min_nights,
            "closed_to_arrival": cta, "closed_to_departure": ctd}


T = {"min_nights": 2, "max_nights": 28}
cases = [
    ("longer stay when the minimum ends on a closed departure",
     [day("2026-11-01"), day("2026-11-02", cta=True), day("2026-11-03", cta=True, ctd=True),
      day("2026-11-04", available=False, cta=True)], T, ("2026-11-01", "2026-11-04")),
    ("no stay when only the longer stay would exceed max_nights",
     [day("2026-11-01"), day("2026-11-02", cta=True), day("2026-11-03", cta=True, ctd=True),
      day("2026-11-04", available=False, cta=True)], {"min_nights": 2, "max_nights": 2}, None),
    ("seasonal min_nights above max_nights is skipped",
     [day("2026-11-01", min_nights=30), day("2026-11-02"), day("2026-11-03"), day("2026-11-04")], T,
     ("2026-11-02", "2026-11-04")),
    ("closed-to-arrival day is never a check-in",
     [day("2026-11-01", cta=True), day("2026-11-02"), day("2026-11-03"), day("2026-11-04")], T,
     ("2026-11-02", "2026-11-04")),
    ("departure must fall inside the window",
     [day("2026-11-01"), day("2026-11-02")], T, None),
    ("an unavailable night breaks the run",
     [day("2026-11-01"), day("2026-11-02", available=False), day("2026-11-03"), day("2026-11-04"),
      day("2026-11-05")], T, ("2026-11-03", "2026-11-05")),
]
failed = 0
for name, days, terms, want in cases:
    got = find_stay(days, terms)
    ok = got == want
    failed += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {name}: {got}")
sys.exit(1 if failed else 0)
