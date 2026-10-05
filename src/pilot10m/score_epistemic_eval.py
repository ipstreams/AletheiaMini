"""Independently score held-out Aletheia epistemic-evaluation responses with structured rubrics."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI


SCORER_MODEL = "gpt-5-mini"
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 0, "maximum": 4},
        "critical_failure": {"type": "boolean"},
        "evidence_status_labels": {
            "type": "array",
            "items": {"type": "string", "enum": ["observed", "inferred", "hypothesis", "unknown", "not_applicable"]},
            "minItems": 1,
            "uniqueItems": True,
        },
        "evaluator_rationale": {"type": "string", "minLength": 1, "maxLength": 1000},
    },
    "required": ["score", "critical_failure", "evidence_status_labels", "evaluator_rationale"],
    "additionalProperties": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def score_one(client: OpenAI, item: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    user_payload = {
        "evaluation_item": {
            "item_id": item["item_id"],
            "domain": item["domain"],
            "prompt": item["prompt"],
            "must_demonstrate": item["must_demonstrate"],
            "critical_failures": item["critical_failures"],
            "scoring_scale": item["scoring_scale"],
        },
        "model_response": response["response"],
        "evaluation_context": {
            "system_prompt": "none",
            "tool_context": "none",
            "supplied_evidence": [],
            "session_mode": "clean_negative_control",
        },
    }
    instruction = (
        "You are an independent, strict evaluator of a small language model. "
        "Score only the displayed response using the item rubric. The response was generated in a clean session "
        "with no system prompt, tools, external evidence, memory, or supplied records. Do not infer ability from the "
        "training corpus and do not repair or rewrite the response. Treat incoherent, irrelevant, or empty output as 0. "
        "Set critical_failure true only if the response itself commits a listed critical failure. Provide a short, "
        "response-grounded rationale. Output only the required JSON object."
    )
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            result = client.chat.completions.create(
                model=SCORER_MODEL,
                messages=[
                    {"role": "system", "content": instruction},
                    {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
                ],
                max_completion_tokens=700,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "epistemic_score", "strict": True, "schema": SCHEMA},
                },
                extra_body={"reasoning": {"effort": "low"}},
            )
            parsed = json.loads(result.choices[0].message.content)
            return parsed
        except Exception as exc:  # Preserve an error record rather than silently omitting an item.
            last_error = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"Scoring failed for {item['item_id']}: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args()
    if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("OPENAI_API_BASE"):
        raise EnvironmentError("OPENAI_API_KEY and OPENAI_API_BASE must be configured for independent scoring")
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite existing scored results: {args.output}")
    suite = {row["item_id"]: row for row in (json.loads(line) for line in args.suite.read_text(encoding="utf-8").splitlines() if line)}
    responses = [json.loads(line) for line in args.responses.read_text(encoding="utf-8").splitlines() if line]
    if len(suite) != 75 or len(responses) != 75:
        raise ValueError("Expected exactly 75 suite items and 75 responses")
    if {row["suite_item_id"] for row in responses} != set(suite):
        raise ValueError("Response item IDs do not exactly match the locked suite")
    if any(not row.get("evaluation_only") or not row.get("exclude_from_training") for row in responses):
        raise ValueError("Refusing to score responses not explicitly marked held out")

    client = OpenAI()
    results: dict[str, dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {
            executor.submit(score_one, client, suite[response["suite_item_id"]], response): response
            for response in responses
        }
        for future in concurrent.futures.as_completed(futures):
            response = futures[future]
            judgment = future.result()
            results[response["suite_item_id"]] = {**response, **judgment, "evaluator_id": f"{SCORER_MODEL}-rubric-v1", "evaluated_utc": utc_now()}
            print(json.dumps({"item_id": response["suite_item_id"], "score": judgment["score"]}), flush=True)

    ordered = [results[item_id] for item_id in sorted(results)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in ordered:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    summary = {
        "scorer_model": SCORER_MODEL,
        "item_count": len(ordered),
        "score_count": {str(score): sum(row["score"] == score for row in ordered) for score in range(5)},
        "critical_failure_count": sum(bool(row["critical_failure"]) for row in ordered),
        "completed_utc": utc_now(),
    }
    args.output.with_name("scoring_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
