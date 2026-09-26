"""Validate untrusted Chat request data and its Git transport identity.

This module checks locator syntax, not the existence or success status of a
snapshot. A consumer must read the pinned commit and verify a results snapshot
belongs to a successful refresh envelope before using its CSV.
"""

from datetime import datetime
import json
import math
import re
import uuid


class RequestError(ValueError):
    """An invalid request or request-only commit."""


_SHA = re.compile(r"[0-9a-fA-F]{40}\Z")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})\Z")
_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_ROOT = {"schema_version", "request_id", "created_at", "product_sha", "operation", "parameters"}
_PARAMETERS = {"gpt_factor", "grok_factor", "min_score", "min_score_reason", "max_cost"}


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RequestError("duplicate_key")
        result[key] = value
    return result


def _reject_constant(value):
    raise RequestError("invalid_number")


def decode_request(text: str) -> dict:
    """Decode one JSON object without duplicate keys or non-JSON constants."""
    try:
        value = json.loads(text, object_pairs_hook=_unique_pairs, parse_constant=_reject_constant)
    except (TypeError, ValueError) as exc:
        raise RequestError("invalid_json") from exc
    if type(value) is not dict:
        raise RequestError("invalid_request")
    return value


def _exact_keys(value, keys):
    if type(value) is not dict or value.keys() != keys:
        raise RequestError("invalid_fields")


def _sha(value):
    if type(value) is not str or not _SHA.fullmatch(value):
        raise RequestError("invalid_sha")


def _uuid(value):
    if type(value) is not str or not _UUID.fullmatch(value) or str(uuid.UUID(value)) != value:
        raise RequestError("invalid_request_id")


def finite_number(value, *, positive=False):
    if type(value) not in (int, float):
        raise RequestError("invalid_number")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise RequestError("invalid_number")
    if value < 0 or (positive and value == 0):
        raise RequestError("invalid_range")
    return value


def _snapshot(value):
    _exact_keys(value, {"commit", "path"})
    _sha(value["commit"])
    path = value["path"]
    if type(path) is not str:
        raise RequestError("invalid_snapshot_path")
    parts = path.split("/")
    if any(not _SEGMENT.fullmatch(part) or part in (".", "..") for part in parts):
        raise RequestError("invalid_snapshot_path")
    archived = len(parts) == 3 and parts[0] == "runs" and parts[2] == "candidates.csv"
    published = (len(parts) == 5 and parts[0] == "results" and
                 parts[3:] == ["snapshot", "candidates.csv"] and
                 _UUID.fullmatch(parts[1]) is not None and
                 re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*-[1-9][0-9]*", parts[2]) is not None)
    if not (archived or published):
        raise RequestError("invalid_snapshot_path")
    return {"commit": value["commit"], "path": path}


def validate_request(request: dict, *, branch: str, parent_sha: str,
                     changed_paths: list[tuple[str, str]]) -> dict:
    """Validate schema v1 and a single-file, added-only request commit."""
    if type(request) is not dict:
        raise RequestError("invalid_request")
    operation = request.get("operation")
    if operation not in ("refresh", "recompute"):
        raise RequestError("invalid_operation")
    _exact_keys(request, _ROOT | ({"source_snapshot"} if operation == "recompute" else set()))
    if type(request["schema_version"]) is not int or request["schema_version"] != 1:
        raise RequestError("invalid_schema_version")
    request_id = request["request_id"]
    _uuid(request_id)
    _sha(request["product_sha"])
    created_at = request["created_at"]
    if type(created_at) is not str or not _DATE.fullmatch(created_at):
        raise RequestError("invalid_created_at")
    try:
        parsed_at = datetime.fromisoformat(created_at)
    except ValueError as exc:
        raise RequestError("invalid_created_at") from exc
    if parsed_at.utcoffset() is None:
        raise RequestError("invalid_created_at")

    params = request["parameters"]
    _exact_keys(params, _PARAMETERS)
    for name in ("gpt_factor", "grok_factor"):
        finite_number(params[name], positive=True)
    finite_number(params["min_score"])
    if params["max_cost"] is not None:
        finite_number(params["max_cost"], positive=True)
    reason = params["min_score_reason"]
    if type(reason) is not str or not reason.strip():
        raise RequestError("invalid_min_score_reason")

    if type(branch) is not str or branch != "efficiency-run/" + request_id:
        raise RequestError("invalid_branch")
    _sha(parent_sha)
    if parent_sha != request["product_sha"]:
        raise RequestError("product_sha_mismatch")
    if (type(changed_paths) is not list or len(changed_paths) != 1 or
            type(changed_paths[0]) is not tuple or
            changed_paths[0] != ("A", "bridge/requests/" + request_id + ".json")):
        raise RequestError("invalid_changed_paths")

    result = {key: request[key] for key in _ROOT}
    result["parameters"] = {key: params[key] for key in _PARAMETERS}
    if operation == "recompute":
        result["source_snapshot"] = _snapshot(request["source_snapshot"])
    return result
