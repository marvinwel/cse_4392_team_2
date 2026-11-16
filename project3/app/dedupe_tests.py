"""Remove duplicate test cases from the merged EP + BVA JUnit class (assignment step 3).

The Java merger only skips members whose text is identical, so an EP test and a BVA
test that set up the same starting state and make the same call both survive under
different names. This module treats two tests as the same test case when their
setup and action statements are the same after normalising:

- comments and whitespace are ignored;
- ``x.on()`` / ``x.off()`` on ``ac`` or ``heater`` equals ``x.isOn = true/false``
  (that is all those methods do in SeasonSwitch.java);
- a leading ``SeasonSwitch.state = SeasonSwitch.OFF`` is ignored, because the
  shared @BeforeEach already sets it.

Only the assertions may differ. The test with more assertions is kept, and any
assertion that only the removed test had is appended to it, so no check is lost.
Coverage cannot drop, because both tests execute the same statements.

A test is left alone (never removed) when its body has nested blocks, lambdas,
or an assertion followed by more setup, so anything unusual is kept as it is.
"""
from __future__ import annotations

import re

_TEST_START = re.compile(
    r"(?P<lead>(?:[ \t]*//[^\n]*\n)*)"          # comment lines directly above
    r"(?P<annos>(?:[ \t]*@\w+(?:\([^)]*\))?[ \t]*\n)*?)"
    r"[ \t]*@Test\b[^\n]*\n"
    r"(?:[ \t]*@\w+(?:\([^)]*\))?[ \t]*\n)*"
    r"[ \t]*(?:public\s+)?void\s+(?P<name>\w+)\s*\(\s*\)[^{]*\{"
)
_DEVICE_CALL = re.compile(r"^(ss\.(?:ac|heater))\.(on|off)\(\)$")
_RESET_STATE = "SeasonSwitch.state=SeasonSwitch.OFF"


def _strip_comments(body: str) -> str:
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    return re.sub(r"//[^\n]*", "", body)


def _statements(body: str) -> list[str] | None:
    """Split a flat method body into normalised statements, or None if not flat."""
    code = _strip_comments(body)
    if "{" in code or "}" in code or "->" in code:
        return None
    parts = [re.sub(r"\s+", "", p) for p in code.split(";")]
    return [p for p in parts if p]


def _normalise_setup(stmt: str) -> str:
    match = _DEVICE_CALL.match(stmt)
    if match:
        return f"{match.group(1)}.isOn={'true' if match.group(2) == 'on' else 'false'}"
    return stmt


def _parse(src: str) -> list[dict]:
    tests = []
    for match in _TEST_START.finditer(src):
        open_brace = match.end() - 1
        depth, i = 0, open_brace
        while i < len(src):
            if src[i] == "{":
                depth += 1
            elif src[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        else:
            continue
        body = src[open_brace + 1:i]
        stmts = _statements(body)
        key = asserts = None
        if stmts is not None:
            first = next((n for n, s in enumerate(stmts) if s.startswith("assert")), len(stmts))
            setup, asserts = stmts[:first], stmts[first:]
            # Only "setup and action, then assertions" tests are compared.
            if setup and all(s.startswith("assert") for s in asserts):
                setup = [_normalise_setup(s) for s in setup]
                while setup and setup[0] == _RESET_STATE:
                    setup.pop(0)
                key = tuple(setup)
        # Remove the whole member: comments above, annotations, body, trailing newline.
        end = i + 1
        if src[end:end + 1] == "\n":
            end += 1
        start = match.start()
        tests.append({
            "name": match.group("name"), "start": start, "end": end,
            "close": i, "key": key, "asserts": asserts or [],
        })
    return tests


def _assert_lines(body: str) -> dict[str, str]:
    """Map each normalised assertion to its original source line."""
    lines = {}
    for line in _strip_comments(body).splitlines():
        text = line.strip()
        if text.startswith("assert"):
            lines.setdefault(re.sub(r"\s+", "", text.rstrip(";")), text)
    return lines


def remove_duplicate_tests(src: str) -> tuple[str, list[dict]]:
    """Return (deduplicated Java source, list of {kept, removed, assertions_added})."""
    tests = _parse(src)
    groups: dict[tuple, list[dict]] = {}
    for test in tests:
        if test["key"]:
            groups.setdefault(test["key"], []).append(test)

    pairs, removals, additions = [], [], {}
    for members in groups.values():
        if len(members) < 2:
            continue
        # Keep the strongest test; on a tie keep the first one in the file (EP before BVA).
        kept = max(members, key=lambda t: (len(t["asserts"]), -t["start"]))
        have = set(kept["asserts"])
        for other in members:
            if other is kept:
                continue
            body = src[other["start"]:other["close"]]
            extra = [line for norm, line in _assert_lines(body).items() if norm not in have]
            have.update(re.sub(r"\s+", "", line.rstrip(";")) for line in extra)
            additions.setdefault(kept["name"], (kept, []))[1].extend(extra)
            removals.append(other)
            pairs.append({"kept": kept["name"], "removed": other["name"],
                          "assertions_added": len(extra)})

    if not pairs:
        return src, []

    # Apply edits from the end of the file so earlier offsets stay valid.
    edits = [(t["start"], t["end"], "") for t in removals]
    for kept, extra in additions.values():
        if extra:
            text = "".join(f"        {line}\n" for line in extra)
            text = "        // Added from removed duplicate test(s)\n" + text
            line_start = src.rfind("\n", 0, kept["close"]) + 1
            edits.append((line_start, line_start, text))
    for start, end, text in sorted(edits, key=lambda e: e[0], reverse=True):
        src = src[:start] + text + src[end:]
    src = re.sub(r"\n{3,}", "\n\n", src)
    return src, pairs
