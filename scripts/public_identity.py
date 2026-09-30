"""Pure canonical public identity mapping shared by acquisition and proof."""
import re

from scripts.aa_public import LEADERBOARD, SourceError


def model_effort(name, slug):
    """Only documented reasoning labels become effort; slug pins checkpoint/variant.

    Dates/versions are *not* reasoning levels; keep their visible qualifier in
    model as well as the slug in model_version. Unknown qualifiers fail closed.
    """
    match = re.fullmatch(r'(.*?)\s*\(([^()]*)\)', name)
    if not match:
        return name.strip(), 'unspecified', slug
    base, qualifier = match.group(1).strip(), match.group(2).strip()
    label = qualifier.lower()
    direct = {'off', 'low', 'medium', 'high', 'xhigh', 'max', 'reasoning', 'non-reasoning'}
    if label in direct:
        return base, label, slug
    effort = re.fullmatch(r'(?:adaptive )?reasoning, (max|xhigh|high|medium|low) effort(?:, .+)?', label)
    if not effort:
        effort = re.fullmatch(r'(max|xhigh|high|medium|low) effort(?:, .+)?', label)
    if not effort:
        effort = re.fullmatch(r'(max|xhigh|high|medium|low), based on .+', label)
    if effort:
        return base, effort.group(1), slug
    if re.fullmatch(r'(?:[A-Za-z]+\s+)?(?:\d{2,4}|\d{4}-\d{2}(?:-\d{2})?|\d{4})', qualifier) or re.fullmatch(
            r"[A-Za-z]+\s+'\d{2}", qualifier):
        return name.strip(), 'unspecified', slug
    raise SourceError('effort_ambiguous', LEADERBOARD, slug)


def public_identity(record):
    """Return the six canonical CSV identity fields for a usable public record."""
    model, effort, checkpoint = model_effort(record['name'], record['slug'])
    return dict(model=model, effort=effort, model_version=checkpoint,
                identity=f'{model} {effort} AA-public published-price',
                provider='AA-public (first-party/median)', pricing_plan='published-price')
