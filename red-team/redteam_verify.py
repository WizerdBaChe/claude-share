#!/usr/bin/env python3
"""redteam_verify - acceptance layer 5: send each finding to a REFUTER.

Layers 2-4 (`score_redteam.py`) check that a finding is well-formed, anchored to
a real line, and in scope. None of that checks whether the claim is TRUE. The
fabricated finding of 2026-08-15 would have passed a structure check; what
exposed it was reading the source. This layer automates that reading, and it
does so adversarially on purpose.

Two design choices that are the whole point:

  * The verifier is told to REFUTE, not to confirm. A verifier asked "is this
    right?" agrees with a confident-sounding report far too often; asked "prove
    this wrong", it goes and looks at the line.
  * Ties break toward refuted WHEN THE VERIFIER SPOKE. If it read the code and
    remained unsure, that is a refutation: the cost of dropping a real finding is
    one missed bug, the cost of keeping a fake one is trust in the whole report.
  * A verifier that never ruled is INCONCLUSIVE, never refuted. Tool failure --
    an unparseable reply, a dispatch that died -- is not evidence about the
    claim. The first live run of this tool got that wrong and reported two
    independently-proven-true findings as refuted; see verdict_of().

The verifier must be a DIFFERENT model from the author (enforced below): a model
asked to check its own work reproduces its own error.

Usage:
  python redteam_verify.py --repo <project-root> --report arm.json \\
      --author <model-a> --verifier <model-b> --grant <token> \\
      [--dispatcher <module-or-path>]
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jsonspan  # noqa: E402
from score_redteam import extract_findings  # noqa: E402


def load_dispatcher(name: str) -> Any:
    """Import the module that talks to models, by NAME, and check its contract.

    SHARE-REPO EDIT. The source environment writes `import extdispatch as ed`
    here: one provider-bound dispatcher, always present, resolved at import
    time. That dispatcher does not ship — it carries an allowlist of local
    project paths, key handling and a provider registry that are properties of
    one machine — so this copy resolves it by name instead, defaulting to
    `extdispatch` so the source's own invocation is byte-for-byte unchanged.

    Everything above this line is the transferable part; a dispatcher is the
    part that is not. The contract is two symbols and no more:

        MODELS   -- a container of model keys, `in` and iteration
        dispatch(profile, prompt, repo, grant, verbose=..., only_model=...)
                 -> {"ok": bool, "answer": str, "trail": [{"stage": str}, ...]}

    `ok` false must not be reported as a refutation — see verdict_of(). Write
    ~20 lines against your own tier; README.md carries a worked skeleton.
    """
    if name.endswith(".py"):
        path = Path(name).expanduser().resolve()
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            raise SystemExit(f"REFUSED: cannot load a dispatcher from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        try:
            module = importlib.import_module(name)
        except ImportError as exc:
            raise SystemExit(
                f"REFUSED: no dispatcher module {name!r} ({exc}). This layer needs "
                "something that can call a model; point --dispatcher at yours. "
                "Contract: MODELS + dispatch(), see load_dispatcher.__doc__."
            ) from exc
    missing = [s for s in ("MODELS", "dispatch") if not hasattr(module, s)]
    if missing:
        raise SystemExit(
            f"REFUSED: dispatcher {name!r} does not satisfy the contract; missing "
            f"{missing}. See load_dispatcher.__doc__."
        )
    return module

PROMPT = """Reply with ONE fenced ```json block containing a JSON object with exactly these three keys, and nothing else: {{"refuted": true|false, "reason": "<one sentence>", "quote": "<the entire text of {file} line {line}, copied character for character>"}}

YOUR JOB IS TO REFUTE THE CLAIM BELOW, not to confirm it. Go and read the source. If after reading you cannot demonstrate that the claim is wrong, set refuted to false. If you are UNSURE for any reason, set refuted to TRUE — an unproven claim is treated as refuted here, and that is the correct outcome, not a failure on your part.

CLAIM under test, made by a different reviewer about this repository:
  file: {file}
  line: {line}
  defect: {defect}
  failure scenario: {failure}

Check specifically: does that line actually say what the claim implies? Does the described failure actually follow from the code as written, or does something elsewhere in the file already prevent it? Read the surrounding function, not just the one line.
"""


def _find_verdict_object(answer: str) -> dict[str, Any] | None:
    """Find the verdict object, tolerating prose that contains braces.

    The naive version — slice from the first `{` to the last `}` — reported the
    CALIBRATION run as inconclusive when the verifier had in fact refuted the
    planted false claim correctly. Its explanation quoted the source, and the
    source contains braces:
        el.getAnimations({ subtree: true }).forEach((a) => { a.finish(); })
    so the slice began inside a JavaScript snippet and could never parse. A
    verifier that reasons in prose about code is the NORMAL case here, not an
    edge case, and a parser that punishes it manufactures inconclusives.

    The scan itself now lives in `jsonspan`, which is the only copy: this
    function held one of three, and the third had never been fixed.
    """
    return jsonspan.first_parsable(
        answer, want=lambda value: isinstance(value, dict) and "refuted" in value
    )


def verdict_of(answer: str) -> dict[str, Any]:
    """THREE outcomes, not two: survived / refuted / inconclusive.

    Corrected 2026-08-16, after the first live run of this tool got 2 of 3 wrong
    in the SAME direction. The original code applied the tie-break "unproven
    means refuted" to INFRASTRUCTURE failures -- an unparseable reply and a
    dispatch that never completed -- and so reported two findings as refuted that
    no verifier had ever ruled on. Both were findings independently proven TRUE
    (one matched the control arm; the other's crash was reproduced locally).

    The tie-break is right for model uncertainty and wrong for tool failure. "The
    verifier looked and could not confirm" and "the verifier never got to look"
    are different facts, and collapsing them silently destroys true findings.
    This is the third time in this project that a three-valued space was written
    as a boolean (finish=tool-calls; all-non-stop-as-failure; now this one).
    """
    data = _find_verdict_object(answer)
    if data is None:
        return {"outcome": "inconclusive",
                "reason": "verifier produced no parseable verdict object -- NOT a refutation",
                "quote": ""}
    if "refuted" not in data:
        return {"outcome": "inconclusive",
                "reason": "verifier omitted the refuted field", "quote": data.get("quote", "")}
    # Genuine model uncertainty still breaks toward refuted -- that tie-break is
    # about what the verifier SAID, and it only applies once it said something.
    data["outcome"] = "refuted" if data.get("refuted") else "survived"
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--author", required=True)
    parser.add_argument("--verifier", required=True)
    parser.add_argument("--grant", required=True, help="one grant use per finding")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--dispatcher", default="extdispatch",
                        help="module name or .py path providing MODELS + dispatch()")
    args = parser.parse_args(argv)

    # SHARE-REPO EDIT: the source validates these two through argparse
    # `choices=sorted(ed.MODELS)`, which requires the dispatcher at
    # parser-build time. Resolving it by name defers that, so the same
    # rejection is made here instead -- an unknown model key still stops the
    # run before a single grant is spent.
    ed = load_dispatcher(args.dispatcher)
    for role, key in (("author", args.author), ("verifier", args.verifier)):
        if key not in ed.MODELS:
            print(f"REFUSED: --{role} {key!r} is not a model this dispatcher knows; "
                  f"choose from {sorted(ed.MODELS)}", file=sys.stderr)
            return 2

    if args.author == args.verifier:
        print("REFUSED: verifier must differ from author -- a model checking its own "
              "work reproduces its own error.", file=sys.stderr)
        return 2

    findings, note = extract_findings(args.report.read_text("utf-8", "replace"))
    if findings is None:
        print(f"STRUCTURE-FAIL ({note}); nothing to verify", file=sys.stderr)
        return 2

    results = []
    for index, finding in enumerate(findings, 1):
        prompt = PROMPT.format(
            file=finding.get("file"), line=finding.get("line"),
            defect=finding.get("defect"), failure=finding.get("failure"),
        )
        print(f"[verify] {index}/{len(findings)} {finding.get('file')}:{finding.get('line')}",
              file=sys.stderr)
        outcome = ed.dispatch(
            "review", prompt, args.repo, args.grant, verbose=False, only_model=args.verifier
        )
        if not outcome.get("ok"):
            stage = (outcome.get("trail") or [{}])[-1].get("stage", "unknown")
            results.append({**finding, "verdict": {
                "outcome": "inconclusive",
                "reason": f"verifier dispatch failed ({stage}) -- NOT a refutation; re-run this one",
                "quote": ""}})
            continue
        results.append({**finding, "verdict": verdict_of(outcome["answer"])})

    def of(name: str) -> list[dict[str, Any]]:
        return [r for r in results if r["verdict"].get("outcome") == name]

    print(f"\n=== layer 5: adversarial verification "
          f"(author={args.author}, verifier={args.verifier}) ===")
    for row in results:
        mark = {"survived": "SURVIVED", "refuted": "REFUTED",
                "inconclusive": "INCONCLUSIVE"}[row["verdict"]["outcome"]]
        print(f"  [{mark:<12}] {row.get('file')}:{row.get('line')}  "
              f"{str(row['verdict'].get('reason', ''))[:100]}")
    print(f"{len(of('survived'))} survived / {len(of('refuted'))} refuted / "
          f"{len(of('inconclusive'))} inconclusive, of {len(results)}.")
    if of("inconclusive"):
        print("INCONCLUSIVE IS NOT REFUTED. Those findings were never ruled on -- "
              "re-run them before treating the report as verified.")

    if args.out:
        args.out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
