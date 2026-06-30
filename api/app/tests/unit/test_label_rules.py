"""Unit tests for rule-based label matching (pure logic, no DB)."""
from app.domains.transactions.models import Label, LabelRule
from app.domains.transactions.service import TransactionService


def _rule(rule_id: int, pattern: str, label_id: int) -> LabelRule:
    lb = Label(id=label_id, name=f"label-{label_id}", color="#000000")
    return LabelRule(id=rule_id, pattern=pattern, label_id=label_id, label=lb)


def test_auto_label_multiple_matches():
    """A description can match several patterns and gets every matching label."""
    svc = TransactionService(None)  # _auto_label never touches the session
    rules = [
        _rule(1, "CARREFOUR", 10),
        _rule(2, "PARIS", 20),
        _rule(3, "AMAZON", 30),
    ]
    ids = svc._auto_label("CB CARREFOUR MARKET 12/05 PARIS", rules)
    assert set(ids) == {10, 20}


def test_auto_label_case_insensitive():
    svc = TransactionService(None)
    rules = [_rule(1, "carrefour", 10)]
    assert svc._auto_label("CB CARREFOUR MARKET", rules) == [10]


def test_auto_label_no_match_returns_empty():
    svc = TransactionService(None)
    rules = [_rule(1, "CARREFOUR", 10)]
    assert svc._auto_label("VIR SALAIRE", rules) == []


def test_auto_label_regex_alternation():
    svc = TransactionService(None)
    rules = [_rule(1, "CARREFOUR|MONOPRIX", 10)]
    assert svc._auto_label("CB MONOPRIX 03/06", rules) == [10]


def test_labels_from_rules_dedupes_by_label_id():
    """Two rules pointing at the same label yield a single Label object."""
    svc = TransactionService(None)
    rules = [_rule(1, "A", 10), _rule(2, "B", 10), _rule(3, "C", 20)]
    labels = svc._labels_from_rules([10, 10, 20], rules)
    assert [lb.id for lb in labels] == [10, 20]
