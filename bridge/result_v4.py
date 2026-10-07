"""Schema v4: user-approved Claude eligibility; selection math is unchanged."""
from . import result_v2 as window


def calculate_v4(csv_path,parameters,provenance):
    return window._calculate(csv_path,parameters,provenance,schema_version=4)


def make_v4_envelope(request,execution,*,calculation,errors):
    return window._make_envelope(request,execution,calculation=calculation,errors=errors,schema_version=4)


def validate_v4_envelope(envelope):
    try:
        return window._validate(envelope,schema_version=4)
    except (OverflowError,ZeroDivisionError) as exc:
        raise window.ResultError('invalid_numeric_result') from exc
