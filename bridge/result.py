"""Generate window-policy v2 results and read both published result versions."""
from . import result_v1, result_v2, window_report

ResultError = result_v1.ResultError


def calculate_snapshot(csv_path, parameters, provenance):
    calculation = result_v2.calculate_v2(csv_path, parameters, provenance)
    return calculation, window_report.render_markdown(calculation)


def make_envelope(request, execution, *, calculation, errors):
    return result_v2.make_v2_envelope(request, execution, calculation=calculation, errors=errors)


def validate_envelope(envelope):
    if type(envelope) is not dict or type(envelope.get('schema_version')) is not int:
        raise ResultError('invalid_result_schema')
    version = envelope['schema_version']
    if version == 1:
        if set(envelope) & {'selection_policy', 'selection_parameters', 'anchors',
                            'chain_identities', 'selection_trace', 'grade_b_effects'}:
            raise ResultError('mixed_result_schema')
        return result_v1.validate_envelope(envelope)
    if version == 2:
        return result_v2.validate_v2_envelope(envelope)
    raise ResultError('invalid_result_schema')
