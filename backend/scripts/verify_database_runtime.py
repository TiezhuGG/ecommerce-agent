from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.runtime_verifier import run_database_smoke_checks


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the currently configured database runtime with a minimal smoke check.",
    )
    parser.add_argument(
        "--expect-backend",
        choices=["sqlite", "postgresql"],
        default=None,
        help="Fail if DATABASE_URL is not configured for the expected backend.",
    )
    args = parser.parse_args()

    report = run_database_smoke_checks(expect_backend=args.expect_backend)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
