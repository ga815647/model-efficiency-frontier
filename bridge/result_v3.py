"""Schema v3: same frozen window policy, explicit Gemini/Claude cost factors."""
from . import result_v2 as window


def calculate_v3(csv_path, parameters, provenance):
    return window._calculate(csv_path, parameters, provenance, schema_version=3)


def make_v3_envelope(request, execution, *, calculation, errors):
    return window._make_envelope(request, execution, calculation=calculation,
                                 errors=errors, schema_version=3)


def validate_v3_envelope(envelope):
    try:
        return window._validate(envelope, schema_version=3)
    except (OverflowError, ZeroDivisionError) as exc:
        raise window.ResultError('invalid_numeric_result') from exc
