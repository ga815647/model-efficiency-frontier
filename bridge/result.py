"""Versioned result reader; generation remains v1 until runner cutover."""
from . import result_v1, result_v2

ResultError = result_v1.ResultError
calculate_snapshot = result_v1.calculate_snapshot
make_envelope = result_v1.make_envelope


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
