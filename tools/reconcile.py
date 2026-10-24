"""Money precision and reconciliation checks (spec §2.1)."""
from decimal import Decimal

# ISO 4217 minor units for the currencies we expect; extend as Host Platforms appear.
MINOR_UNITS = {"AED": 2, "AUD": 2, "BHD": 3, "BRL": 2, "CAD": 2, "CHF": 2, "EUR": 2, "GBP": 2,
               "IDR": 2, "INR": 2, "JOD": 3, "JPY": 0, "KRW": 0, "KWD": 3, "LKR": 2, "MXN": 2,
               "MYR": 2, "NPR": 2, "NZD": 2, "OMR": 3, "SGD": 2, "THB": 2, "USD": 2, "VND": 0, "ZAR": 2}


def money_problems(m, path, currency=None):
    out = []
    digits = MINOR_UNITS.get(m["currency"])
    frac = m["amount"].split(".")[1] if "." in m["amount"] else ""
    if digits is None:
        out.append(f"{path}: currency {m['currency']} not in the validator's table; precision not checked")
    elif len(frac) != digits:
        out.append(f"{path}: {m['currency']} amounts need exactly {digits} fraction digits, got {m['amount']!r}")
    if currency and m["currency"] != currency:
        out.append(f"{path}: currency {m['currency']} differs from {currency}")
    return out


def D(m):
    return Decimal(m["amount"])


def quote_problems(q):
    """Return a list of reconciliation failures for a Quote (empty means it reconciles)."""
    c, out = q["currency"], []
    for i, l in enumerate(q["lines"]):
        out += money_problems(l["amount"], f"lines[{i}]", c)
    out += money_problems(q["total"], "total", c)
    for i, p in enumerate(q["payment_schedule"]):
        out += money_problems(p["amount"], f"payment_schedule[{i}]", c)
    for i, x in enumerate(q["cancellation"]):
        out += money_problems(x["refund"], f"cancellation[{i}]", c)
    out += money_problems(q["deposit"]["amount"], "deposit.amount", c)
    if out and any("fraction digits" in p or "differs" in p for p in out):
        return out
    # §2.1: negatives only where a field says so. In a Quote that is discount and
    # channel_adjustment lines; deposits, instalments, refunds and other lines are >= 0.
    for i, l in enumerate(q["lines"]):
        if l["kind"] not in ("discount", "channel_adjustment") and D(l["amount"]) < 0:
            out.append(f"lines[{i}] ({l['kind']}) must not be negative")
    for i, p in enumerate(q["payment_schedule"]):
        if D(p["amount"]) < 0:
            out.append(f"payment_schedule[{i}] must not be negative")
    if D(q["deposit"]["amount"]) < 0:
        out.append("deposit.amount must not be negative")
    total = D(q["total"])
    s = sum((D(l["amount"]) for l in q["lines"] if l["in_total"]), Decimal(0))
    if s != total:
        out.append(f"lines with in_total sum to {s}, total is {total}")
    ps = sum((D(p["amount"]) for p in q["payment_schedule"]), Decimal(0))
    if ps != total:
        out.append(f"payment_schedule sums to {ps}, total is {total}")
    deadlines = [x["until"] for x in q["cancellation"][:-1]]
    if None in deadlines:
        out.append("only the last cancellation entry may have until null")
    elif deadlines != sorted(deadlines) or len(set(deadlines)) != len(deadlines):
        out.append("cancellation deadlines must be strictly earliest first")
    prev = None
    for i, x in enumerate(q["cancellation"]):
        r = D(x["refund"])
        if r < 0 or r > total:
            out.append(f"cancellation[{i}].refund {r} outside 0..{total}")
        if prev is not None and r > prev:
            out.append(f"cancellation[{i}].refund {r} is larger than an earlier deadline's {prev}")
        prev = r
    if q["cancellation"][-1]["until"] is not None:
        out.append("cancellation must end with an entry whose until is null")
    for l in q["lines"]:
        if l["kind"] == "discount" and l["in_total"] and D(l["amount"]) > 0:
            out.append(f"discount line {l['label']!r} must not be positive")
    return out


def booking_terms_problems(t, quote):
    """§9.3: a book/change revision must restate its bound Quote."""
    out = []
    for k in ("total", "due_now", "price_difference", "refund"):
        if k in t:
            out += money_problems(t[k], f"terms.livstay.{k}", quote["currency"])
    if out:
        return out
    for k in ("home_id", "check_in", "check_out", "party", "total"):
        if t.get(k) != quote.get(k):
            out.append(f"terms.livstay.{k} differs from the Quote")
    due = sum((D(p["amount"]) for p in quote["payment_schedule"] if p["at_booking"]), Decimal(0))
    if "due_now" in t and D(t["due_now"]) != due:
        out.append(f"due_now {t['due_now']['amount']} differs from the Quote's at-booking amount {due}")
    if t.get("deposit") and t["deposit"] != quote["deposit"]:
        out.append("terms.livstay.deposit differs from the Quote")
    if t.get("quote_id") != quote["quote_id"] or t.get("quote_signature") != quote["signature"]:
        out.append("quote_id or quote_signature does not name this Quote")
    return out
