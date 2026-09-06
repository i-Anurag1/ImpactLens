"""
A small, fully-specified demo repository: an e-commerce checkout flow.

The point of this fixture is the judge-facing "aha": PaymentService looks
low-risk from a naive diff (one file, ~12 lines changed), but Entire
Graph's call/co-change relationships reveal it actually reaches an
InventoryService dependency through a shared currency-rounding helper that
nothing in the PR touches directly — a hidden dependency a line-diff alone
would never surface. That's the "What will this change break?" moment.

Everything below is demo fixture data standing in for what the real Entire
Graph CLI / Databricks warehouse would return for this repo. See
entire_adapter.py and databricks_adapter.py for where the real calls go.
"""

REPO_FULL_NAME = "impactlens-demo/checkout-service"
DEFAULT_BRANCH = "main"

DEMO_COMMIT = {
    "base_sha": "a1c3f90",
    "head_sha": "e77d21b",
    "pr_title": "Fix currency rounding in processPayment",
    "author": "priya-dev",
}

# --- Symbol table -----------------------------------------------------
SYMBOLS = {
    "PaymentService.processPayment": {
        "file": "src/services/payment_service.py",
        "line": 42,
        "kind": "function",
    },
    "PaymentService.roundToCurrencyUnit": {
        "file": "src/services/payment_service.py",
        "line": 78,
        "kind": "function",
    },
    "CheckoutService.checkout": {
        "file": "src/services/checkout_service.py",
        "line": 31,
        "kind": "function",
    },
    "OrderController.placeOrder": {
        "file": "src/api/order_controller.py",
        "line": 19,
        "kind": "route",
    },
    "InventoryService.reserveStock": {
        "file": "src/services/inventory_service.py",
        "line": 55,
        "kind": "function",
    },
    "PricingUtils.applyRounding": {
        "file": "src/utils/pricing_utils.py",
        "line": 12,
        "kind": "function",
    },
    "CheckoutServiceTest.test_checkout_success": {
        "file": "tests/test_checkout_service.py",
        "line": 14,
        "kind": "test",
    },
    "PaymentServiceTest.test_process_payment_declined": {
        "file": "tests/test_payment_service.py",
        "line": 9,
        "kind": "test",
    },
    "OrderControllerTest.test_place_order_flow": {
        "file": "tests/test_order_controller.py",
        "line": 11,
        "kind": "test",
    },
    "InventoryServiceTest.test_reserve_stock_race": {
        "file": "tests/test_inventory_service.py",
        "line": 22,
        "kind": "test",
    },
}

# --- Changed files in this PR ------------------------------------------
CHANGED_FILES = [
    {
        "path": "src/services/payment_service.py",
        "additions": 9,
        "deletions": 3,
        "changed_symbols": [
            "PaymentService.processPayment",
            "PaymentService.roundToCurrencyUnit",
        ],
    }
]

# --- Call graph edges (what Entire Graph's `neighbors`/`impact` return) --
# direct: caller depends on the changed symbol directly.
# hidden: reachable only through a shared utility — the "hidden dependency".
CALL_EDGES = [
    ("CheckoutService.checkout", "PaymentService.processPayment", "calls", 0.97,
     "Direct call, 1 hop, resolved from import + call-site match."),
    ("OrderController.placeOrder", "CheckoutService.checkout", "calls", 0.95,
     "Direct call, 1 hop."),
    ("PaymentService.roundToCurrencyUnit", "PricingUtils.applyRounding", "calls", 0.90,
     "Direct call inside changed function."),
    ("InventoryService.reserveStock", "PricingUtils.applyRounding", "calls", 0.71,
     "Shared utility call — same rounding helper used for stock-hold pricing. "
     "Not visible from the PR diff; surfaced only via static call-graph traversal."),
]

# co-change: files that historically change together (from git history / Databricks)
CO_CHANGE_EDGES = [
    ("src/services/payment_service.py", "src/services/inventory_service.py", 0.42,
     "Co-changed in 5 of the last 12 commits touching PaymentService."),
    ("src/services/payment_service.py", "src/services/checkout_service.py", 0.83,
     "Co-changed in 10 of the last 12 commits touching PaymentService."),
]

TEST_COVERAGE = {
    "PaymentService.processPayment": ["PaymentServiceTest.test_process_payment_declined"],
    "CheckoutService.checkout": ["CheckoutServiceTest.test_checkout_success"],
    "OrderController.placeOrder": ["OrderControllerTest.test_place_order_flow"],
    "InventoryService.reserveStock": ["InventoryServiceTest.test_reserve_stock_race"],
}

PUBLIC_API_SYMBOLS = {"OrderController.placeOrder"}

# --- Seeded historical test-run data (Databricks stand-in) ---------------
# NOTE: clearly labeled seeded/demo data, not real production history.
HISTORICAL_TEST_RUNS = [
    {"commit_sha": "9f0a112", "symbol": "PaymentService.processPayment",
     "test_name": "PaymentServiceTest.test_process_payment_declined",
     "outcome": "fail", "failure_message": "AssertionError: rounding drift 0.01 on JPY",
     "occurred_at": "2026-06-02T10:14:00Z"},
    {"commit_sha": "9f0a112", "symbol": "InventoryService.reserveStock",
     "test_name": "InventoryServiceTest.test_reserve_stock_race",
     "outcome": "fail", "failure_message": "StockHoldMismatch: rounded price != ledger price",
     "occurred_at": "2026-06-02T10:14:20Z"},
    {"commit_sha": "b41cee0", "symbol": "PaymentService.processPayment",
     "test_name": "PaymentServiceTest.test_process_payment_declined",
     "outcome": "pass", "failure_message": None,
     "occurred_at": "2026-04-18T09:02:00Z"},
    {"commit_sha": "b41cee0", "symbol": "CheckoutService.checkout",
     "test_name": "CheckoutServiceTest.test_checkout_success",
     "outcome": "pass", "failure_message": None,
     "occurred_at": "2026-04-18T09:02:40Z"},
    {"commit_sha": "22ac9d1", "symbol": "InventoryService.reserveStock",
     "test_name": "InventoryServiceTest.test_reserve_stock_race",
     "outcome": "fail", "failure_message": "Flaky under concurrent reservation load",
     "occurred_at": "2026-02-11T22:40:00Z"},
]

# --- Checkpoints (Entire CLI session/agent context stand-in) -------------
CHECKPOINTS = [
    {
        "id": "ckpt_0031",
        "title": "Fix currency rounding drift in processPayment",
        "summary": "Agent session identified a rounding drift on JPY/zero-decimal "
                    "currencies and patched PaymentService.roundToCurrencyUnit to "
                    "use banker's rounding.",
        "author_type": "ai_agent",
        "author_name": "claude-code-session",
        "session_id": "sess_8827",
        "prompt_excerpt": "\"Investigate the JPY off-by-one-cent bug reported in "
                           "issue #482 and fix the rounding logic in payment processing.\"",
        "files_changed": ["src/services/payment_service.py"],
        "commit_sha": "e77d21b",
        "created_at": "2026-08-30T14:02:00Z",
    },
    {
        "id": "ckpt_0030",
        "title": "Baseline before rounding fix",
        "summary": "Checkpoint captured prior to the agent session, tests green.",
        "author_type": "human",
        "author_name": "priya-dev",
        "session_id": None,
        "prompt_excerpt": None,
        "files_changed": [],
        "commit_sha": "a1c3f90",
        "created_at": "2026-08-30T13:40:00Z",
    },
]
