# ai-generated: 100% - implemented the Lab 5 SARIF normalization, matching, and scoring rules
"""Build a per-tool confusion matrix from SARIF results and labelled defects."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any
from urllib.parse import unquote


_CLASSES = frozenset(
    {
        "secret",
        "injection",
        "deserialization",
        "weak-crypto",
        "insecure-transport",
        "path-traversal",
        "ssrf",
        "vulnerable-dependency",
        "misconfiguration",
        "access-control",
    }
)
_CWE_CLASSES = {
    259: {"secret"},
    260: {"secret"},
    321: {"secret"},
    798: {"secret"},
    74: {"injection"},
    77: {"injection"},
    78: {"injection"},
    79: {"injection"},
    80: {"injection"},
    88: {"injection"},
    89: {"injection"},
    90: {"injection"},
    91: {"injection"},
    94: {"injection"},
    95: {"injection"},
    96: {"injection"},
    611: {"injection"},
    776: {"injection"},
    917: {"injection"},
    943: {"injection"},
    1336: {"injection"},
    502: {"deserialization"},
    261: {"weak-crypto"},
    326: {"weak-crypto"},
    327: {"weak-crypto"},
    328: {"weak-crypto"},
    330: {"weak-crypto"},
    331: {"weak-crypto"},
    338: {"weak-crypto"},
    759: {"weak-crypto"},
    760: {"weak-crypto"},
    916: {"weak-crypto"},
    295: {"insecure-transport"},
    297: {"insecure-transport"},
    319: {"insecure-transport"},
    322: {"insecure-transport"},
    757: {"insecure-transport"},
    22: {"path-traversal"},
    23: {"path-traversal"},
    35: {"path-traversal"},
    36: {"path-traversal"},
    73: {"path-traversal"},
    918: {"ssrf"},
    937: {"vulnerable-dependency"},
    1035: {"vulnerable-dependency"},
    1104: {"vulnerable-dependency"},
    1395: {"vulnerable-dependency"},
    16: {"misconfiguration"},
    215: {"misconfiguration"},
    250: {"misconfiguration"},
    489: {"misconfiguration"},
    668: {"misconfiguration"},
    732: {"misconfiguration"},
    1188: {"misconfiguration"},
    284: {"access-control"},
    285: {"access-control"},
    639: {"access-control"},
    862: {"access-control"},
    863: {"access-control"},
}
_SEMGREP_NAMES = frozenset(
    {
        "semgrep",
        "semgrep oss",
        "semgrep ce",
        "semgrep community edition",
        "semgrep pro",
    }
)
_TRIVY_TAG_CLASSES = {
    "vulnerability": "vulnerable-dependency",
    "secret": "secret",
    "misconfiguration": "misconfiguration",
}
_CWE_TAG = re.compile(
    r"(?<![A-Za-z0-9])CWE-([0-9]+)", re.IGNORECASE | re.ASCII
)
_TOOL_SEPARATOR = re.compile(r"[^a-z0-9]+")
_PACKAGE_SEPARATOR = re.compile(r"[-_.]+")
_PACKAGE_TOKEN = re.compile(r"[A-Za-z0-9._-]+")


def _array(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _driver(run: dict[str, Any]) -> dict[str, Any]:
    tool = run.get("tool")
    if not isinstance(tool, dict):
        return {}
    driver = tool.get("driver")
    return driver if isinstance(driver, dict) else {}


def _tool_id(run: dict[str, Any]) -> str:
    name = _driver(run).get("name")
    if not isinstance(name, str):
        return "unknown"

    name = name.strip()
    lowered = name.lower()
    if lowered in _SEMGREP_NAMES:
        return "semgrep"

    normalized = _TOOL_SEPARATOR.sub("-", lowered).strip("-")
    return normalized or "unknown"


def _string_tags(properties: Any) -> list[str]:
    if not isinstance(properties, dict):
        return []
    return [tag for tag in _array(properties.get("tags")) if isinstance(tag, str)]


def _rule_tags(driver: dict[str, Any]) -> dict[str, list[str]]:
    tags_by_id: dict[str, list[str]] = {}
    for rule in _array(driver.get("rules")):
        if not isinstance(rule, dict):
            continue
        rule_id = rule.get("id")
        if isinstance(rule_id, str) and rule_id not in tags_by_id:
            tags_by_id[rule_id] = _string_tags(rule.get("properties"))
    return tags_by_id


def _result_classes(
    result: dict[str, Any], tool_id: str, rule_tags: list[str]
) -> set[str]:
    properties = result.get("properties")
    own_class = properties.get("class") if isinstance(properties, dict) else None
    if isinstance(own_class, str) and own_class in _CLASSES:
        return {own_class}

    if tool_id == "gitleaks":
        return {"secret"}
    if tool_id in {"grype", "osv-scanner"}:
        return {"vulnerable-dependency"}
    if tool_id == "trivy":
        classes = {
            _TRIVY_TAG_CLASSES[tag.lower()]
            for tag in rule_tags
            if tag.lower() in _TRIVY_TAG_CLASSES
        }
        if classes:
            return classes

    result_tags = _string_tags(properties)
    classes: set[str] = set()
    for tag in (*result_tags, *rule_tags):
        for match in _CWE_TAG.finditer(tag):
            classes.update(_CWE_CLASSES.get(int(match.group(1)), set()))
    return classes or {"other"}


def _location(
    result: dict[str, Any], set_root: str
) -> tuple[str, int | None, int | None] | None:
    locations = _array(result.get("locations"))
    if not locations or not isinstance(locations[0], dict):
        return None

    physical = locations[0].get("physicalLocation")
    if not isinstance(physical, dict):
        return None
    artifact = physical.get("artifactLocation")
    if not isinstance(artifact, dict):
        return None
    uri = artifact.get("uri")
    if not isinstance(uri, str) or not uri:
        return None

    path = unquote(uri)
    if path[:7].lower() == "file://":
        path = path[7:]
    if path.startswith("./"):
        path = path[2:]

    components = path.split("/")
    root_positions = [
        index for index, component in enumerate(components) if component == set_root
    ]
    if not root_positions:
        return None
    file_path = "/".join(components[root_positions[-1] :])

    region = physical.get("region")
    start_line = region.get("startLine") if isinstance(region, dict) else None
    if type(start_line) is not int or start_line < 1:
        return file_path, None, None

    end_line = region.get("endLine") if isinstance(region, dict) else None
    if type(end_line) is not int or end_line < start_line:
        end_line = start_line
    return file_path, start_line, end_line


def _canonical_package(package: str) -> str:
    return _PACKAGE_SEPARATOR.sub("-", package.lower())


def _package_tokens(result: dict[str, Any]) -> set[str]:
    message = result.get("message")
    text = message.get("text") if isinstance(message, dict) else None
    if not isinstance(text, str):
        return set()

    tokens = set()
    for match in _PACKAGE_TOKEN.finditer(text):
        token = match.group().strip("._-")
        if token:
            tokens.add(_canonical_package(token))
    return tokens


def _matched_defects(
    result: dict[str, Any],
    file_path: str,
    start_line: int | None,
    end_line: int | None,
    classes: set[str],
    defects: list[dict[str, Any]],
) -> set[int]:
    matched: set[int] = set()
    packages: set[str] | None = None

    for index, defect in enumerate(defects):
        if defect.get("file") != file_path or defect.get("class") not in classes:
            continue

        if defect.get("class") == "vulnerable-dependency":
            package = defect.get("package")
            if not isinstance(package, str):
                continue
            if packages is None:
                packages = _package_tokens(result)
            if _canonical_package(package) in packages:
                matched.add(index)
            continue

        if start_line is None or end_line is None:
            continue
        if (
            start_line <= defect["end_line"]
            and defect["start_line"] <= end_line
        ):
            matched.add(index)
    return matched


def confusion_matrix(labels: dict, sarif_documents: list[dict]) -> dict:
    defects = labels["defects"]
    set_root = labels["set"]
    matched_by_tool: dict[str, set[int]] = {}
    false_positives: dict[str, set[tuple[Any, ...]]] = {}

    for document in sarif_documents:
        if not isinstance(document, dict):
            continue
        for run in _array(document.get("runs")):
            if not isinstance(run, dict):
                continue

            tool_id = _tool_id(run)
            matched_by_tool.setdefault(tool_id, set())
            false_positives.setdefault(tool_id, set())

            driver = _driver(run)
            tags_by_rule = _rule_tags(driver)
            for result in _array(run.get("results")):
                if not isinstance(result, dict):
                    continue
                kind = result.get("kind")
                if kind is not None and kind != "fail":
                    continue
                if result.get("suppressions"):
                    continue

                location = _location(result, set_root)
                if location is None:
                    continue
                file_path, start_line, end_line = location
                rule_id = result.get("ruleId")
                rule_tags = tags_by_rule.get(rule_id, []) if isinstance(rule_id, str) else []
                classes = _result_classes(result, tool_id, rule_tags)
                matches = _matched_defects(
                    result,
                    file_path,
                    start_line,
                    end_line,
                    classes,
                    defects,
                )
                if matches:
                    matched_by_tool[tool_id].update(matches)
                    continue

                rule_key = ("string", rule_id) if isinstance(rule_id, str) else ("no-rule",)
                false_positives[tool_id].add(
                    (rule_key, file_path, start_line, end_line)
                )

    tools: dict[str, dict[str, Any]] = {}
    defect_count = len(defects)
    for tool_id, matched in matched_by_tool.items():
        tp = len(matched)
        fp = len(false_positives[tool_id])
        fn = defect_count - tp
        precision_denominator = tp + fp
        f1_denominator = 2 * tp + fp + fn
        tools[tool_id] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": (
                round(tp / precision_denominator, 4)
                if precision_denominator
                else None
            ),
            "recall": round(tp / defect_count, 4) if defect_count else None,
            "f1": (
                round(2 * tp / f1_denominator, 4) if f1_denominator else None
            ),
        }

    return {"set": set_root, "defects": defect_count, "tools": tools}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="per-tool confusion matrix of SARIF against labels (CI-SPEC.md P-23)"
    )
    parser.add_argument("--labels", required=True, help="the labels file (P-14)")
    parser.add_argument("sarif", nargs="+", help="SARIF 2.1.0 files")
    args = parser.parse_args(argv)
    with open(args.labels, encoding="utf-8") as fh:
        labels = json.load(fh)
    documents = []
    for path in args.sarif:
        with open(path, encoding="utf-8") as fh:
            documents.append(json.load(fh))
    json.dump(confusion_matrix(labels, documents), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
