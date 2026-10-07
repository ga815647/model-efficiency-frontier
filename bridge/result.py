"""Generate versioned window results while preserving exact historical schemas."""
from . import result_v1, result_v2, result_v3, window_report
from .subscription_cost import SUBSCRIPTION_PARAMETERS

ResultError = result_v1.ResultError


def calculate_snapshot(csv_path, parameters, provenance):
    calculator = (result_v3.calculate_v3 if type(parameters) is dict and
                  set(parameters) == SUBSCRIPTION_PARAMETERS else result_v2.calculate_v2)
    calculation = calculator(csv_path, parameters, provenance)
    return calculation, window_report.render_markdown(calculation)


def make_envelope(request, execution, *, calculation, errors):
    factory = result_v3.make_v3_envelope if request.get('schema_version') == 2 else result_v2.make_v2_envelope
    return factory(request, execution, calculation=calculation, errors=errors)


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
    if version == 3:
        return result_v3.validate_v3_envelope(envelope)
    raise ResultError('invalid_result_schema')
