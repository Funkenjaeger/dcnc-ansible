#!/usr/bin/env python3
"""Prove the apt-refresh classification in playbook.yml, against real apt output.

    python3 tests/test_apt_classification.py     # exits non-zero on failure

WHY THIS EXISTS. The playbook decides whether to abort a provisioning run by
regex-parsing `apt-get update` output inside a Jinja expression. That decision
is load-bearing -- get it wrong in the permissive direction and a run continues
past an unreachable Debian mirror into an install it cannot perform -- and it
is invisible to `--syntax-check`, which validates YAML shape and never renders
a template.

It has already been wrong exactly that way. Written with single backslashes,
`regex_replace(..., '\1')` looked correct in YAML but Jinja read '\1' as a
Python escape and returned the control character 0x01, so EVERY failed repo
collapsed to the same unmatchable string and sorted into the incidental bucket.
Reading the expression did not reveal it. Rendering it did, in one run.

The expressions are pulled out of playbook.yml by task name rather than
retyped, so this tests what will actually run. Rename those tasks and this
fails loudly instead of quietly testing nothing.
"""
import ast
import os
import re
import sys

import yaml
from jinja2 import Environment

PLAYBOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "playbook.yml")

# Ansible's filters and tests, reimplemented at the fidelity this needs. The
# escaping behaviour under test lives in Jinja's string-literal parsing, which
# is the real Jinja here, not a stand-in.
env = Environment()
env.filters["regex_replace"] = lambda v, p, r: re.sub(p, r, v)
env.filters["regex_escape"] = re.escape
env.tests["match"] = lambda v, p: re.match(p, v) is not None
env.tests["search"] = lambda v, p: re.search(p, v) is not None

play = yaml.safe_load(open(PLAYBOOK, encoding="utf-8"))[0]
tasks = {t["name"]: t for t in play["tasks"] if isinstance(t, dict) and "name" in t}

try:
    facts_a = tasks["work out which repos failed to refresh"]["ansible.builtin.set_fact"]
    facts_b = tasks["split those into load-bearing and incidental"]["ansible.builtin.set_fact"]
except KeyError as exc:
    sys.exit(f"cannot find the task named {exc} in playbook.yml -- was it renamed?")

EXPR = {
    "repos": facts_a["apt_failed_repos"],
    "pattern": facts_a["apt_required_pattern"],
    "required": facts_b["apt_failed_required"],
    "optional": facts_b["apt_failed_optional"],
}
REQUIRED_HOSTS = play["vars"]["cncpc_apt_required_hosts"]


def render(expr, **ctx):
    out = env.from_string(expr).render(**ctx).strip()
    try:
        return ast.literal_eval(out)
    except (ValueError, SyntaxError):
        return out


def classify(stdout, rc):
    """Mirror the three when: conditions the playbook acts on, in their order."""
    ctx = {
        "apt_update": {"stdout_lines": stdout.splitlines(), "rc": rc},
        "cncpc_apt_required_hosts": REQUIRED_HOSTS,
    }
    repos = render(EXPR["repos"], **ctx)
    ctx = dict(ctx, apt_failed_repos=repos,
               apt_required_pattern=render(EXPR["pattern"], **ctx))
    required = render(EXPR["required"], **ctx)
    optional = render(EXPR["optional"], **ctx)

    if required:
        return "FATAL: required repo", required
    if rc != 0 and not repos:
        return "FATAL: unattributable", []
    if optional:
        return "CONTINUE: reported", optional
    return "CLEAN", []


# Verbatim from cncpc, 2026-09-07 -- the run this hardening came out of.
REAL = """Hit:1 http://deb.debian.org/debian trixie InRelease
Hit:2 http://deb.debian.org/debian trixie-updates InRelease
Get:3 https://repository.qtpyvcp.com/apt develop InRelease [3,286 B]
Err:3 https://repository.qtpyvcp.com/apt develop InRelease
  Sub-process /usr/bin/sqv returned an error code (1), error message is: Missing key 50F874571F20C5B0BA225E2F0CDFCCE0388CFA48, which is needed to verify signature.
Hit:4 http://security.debian.org/debian-security trixie-security InRelease
Fetched 3,286 B in 0s (19.2 kB/s)
Reading package lists... Done"""

CLEAN = "\n".join(
    line for line in REAL.splitlines()
    if "qtpyvcp" not in line and not line.startswith("  Sub-process")
)

CASES = [
    # The rotated QtPyVCP key must NOT stop a run: nothing installs from it.
    ("the real 2026-09-07 failure", REAL, 0, "CONTINUE: reported"),
    ("after disabling qtpyvcp", CLEAN, 0, "CLEAN"),
    # Debian must stop a run: everything installs from it.
    ("Debian mirror down",
     "Err:1 http://deb.debian.org/debian trixie InRelease\n  Could not connect",
     100, "FATAL: required repo"),
    ("security repo down",
     "Err:1 http://security.debian.org/debian-security trixie-security InRelease\n"
     "  Temporary failure",
     100, "FATAL: required repo"),
    # A required failure outranks an incidental one; do not let the tolerated
    # case swallow the fatal one when both appear.
    ("both a required and an optional repo down",
     "Err:1 http://deb.debian.org/debian trixie InRelease\n"
     "Err:2 https://repository.qtpyvcp.com/apt develop InRelease",
     100, "FATAL: required repo"),
    # Nonzero exit with nothing to attribute it to: refuse to guess.
    ("apt dies with no Err: to blame", "Reading package lists... Done",
     100, "FATAL: unattributable"),
    # The other third-party repo cncpc carries, for when its key rotates too.
    ("EtherLab key rotates next",
     "Hit:1 http://deb.debian.org/debian trixie InRelease\n"
     "Err:2 http://download.opensuse.org/repositories/science:/EtherLab/Debian_Testing/ ./ InRelease\n"
     "  Missing key",
     0, "CONTINUE: reported"),
]


def main():
    failures = 0
    for label, stdout, rc, expected in CASES:
        got, detail = classify(stdout, rc)
        ok = got == expected
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {label:42} -> {got}"
              f"{'  ' + str(detail) if detail else ''}"
              f"{'' if ok else f'   (expected {expected})'}")
    print(f"\n{len(CASES) - failures}/{len(CASES)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
