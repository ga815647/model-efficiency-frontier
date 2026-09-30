"""Decode policy bytes obtained from a caller's trusted product Git tree.

The decoder checks content only; establishing that Git trust is the caller's
responsibility. An untrusted source map never selects compatibility mode.
"""

from bridge.inventory import _strict_json
from scripts.refresh_inventory import POLICY


class PolicyError(ValueError):
    """The trusted product marker exists but is not an approved policy."""


def decode_refresh_policy(data: bytes | None) -> str | None:
    if data is None:
        return None
    try:
        value = _strict_json(data)
        if (type(value) is not dict or set(value) != {'policy'} or
                type(value['policy']) is not str or value['policy'] != POLICY):
            raise ValueError('invalid product refresh policy')
        return value['policy']
    except (ValueError, TypeError, UnicodeError, AttributeError) as exc:
        raise PolicyError('invalid product refresh policy') from exc
