"""Issue a signed premium access code (for workshop attendees or manual sales).

Usage:  ENTITLEMENT_SECRET=... python scripts/issue_access_code.py student@uni.ac.uk student 30
Arguments: subject (email or label), plan (student|workshop), days valid.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from entitlements import get_secret, issue_code  # noqa: E402

if len(sys.argv) != 4:
    sys.exit(__doc__)
subject, plan, days = sys.argv[1], sys.argv[2], int(sys.argv[3])
secret = get_secret()
if not secret:
    sys.exit("Set ENTITLEMENT_SECRET (24+ characters) in your environment first.")
print(issue_code(secret, subject, plan, int(time.time()) + days * 86400))
