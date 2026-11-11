"""Validate reference-bound layout and choreography audits before acceptance."""
import argparse
import hashlib
import json
from pathlib import Path


def validate(project, audit_path, require_render=False):
    errors = []
    if not audit_path.is_file():
        return ['Missing fidelity audit file']
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    groups = audit.get('groups', [])
    if not groups:
        return ['No audited occurrences']
    strict = audit.get('schema', 1) >= 2
    if strict:
        ids = [group.get('id') for group in groups]
        if len(set(ids)) != len(ids) or set(audit.get('scope', [])) != set(ids):
            errors.append('Audit scope must match the unique occurrence records')
    for group in groups:
        ident = group.get('id', '?')
        reference = group.get('reference', {})
        stages = group.get('choreography', [])
        if not reference.get('frames') or not reference.get('evidence'):
            errors.append(f'{ident} missing reference process evidence')
        if len(stages) < 2 or any(not stage.get('action') or 'frame' not in stage for stage in stages):
            errors.append(f'{ident} missing phase actions and frame clock')
        if strict:
            source_path = project / reference.get('path', '')
            if not source_path.is_file() or hashlib.sha256(source_path.read_bytes()).hexdigest() != reference.get('sha256'):
                errors.append(f'{ident} missing or stale reference clip binding')
            if group.get('presenter', {}).get('fit') not in {'bottom-full-width', 'bounded', 'not-applicable'}:
                errors.append(f'{ident} must explicitly classify presenter coverage')
            if group.get('subtitle', {}).get('visibility') not in {'unoccluded', 'intentionally-occluded', 'not-applicable'}:
                errors.append(f'{ident} must explicitly classify subtitle visibility')
            if any(stage.get('frame') not in reference.get('frames', []) for stage in stages):
                errors.append(f'{ident} phase clocks must be backed by source frame evidence')
        for record in [reference] + group.get('samples', []):
            for filename in record.get('evidence', []):
                if not (project / filename).is_file():
                    errors.append(f'{ident} missing evidence {filename}')
        if not require_render:
            continue
        media = group.get('media', {})
        media_path = project / media.get('path', '')
        if not media_path.is_file() or hashlib.sha256(media_path.read_bytes()).hexdigest() != media.get('sha256'):
            errors.append(f'{ident} stale media binding')
        samples = group.get('samples', [])
        if not samples:
            errors.append(f'{ident} missing rendered samples')
        expected = group.get('presenter', {})
        subtitle = group.get('subtitle', {})
        if strict:
            frames = media.get('frames', 0)
            if not isinstance(frames, int) or frames <= 0 or [s.get('frame') for s in samples] != list(range(frames)):
                errors.append(f'{ident} missing ordered frame measurements for the encoded result')
            if expected.get('fit') == 'bottom-full-width':
                settled = [s for s in samples if s.get('settled') is True]
                if not settled or {s.get('phase') for s in settled} != set(expected.get('settledPhases', [])):
                    errors.append(f'{ident} bottom coverage must be checked in every settled phase')
                for sample in settled:
                    holes = sample.get('bottomUncoveredPixels', [])
                    if len(holes) < 3 or any(not isinstance(x, int) or not 0 <= x <= 2 for x in holes):
                        errors.append(f'{ident} presenter alpha leaves gaps in lower scanlines at frame {sample.get("frame")}')
                        break
            if subtitle.get('visibility') == 'unoccluded' and not any(s.get('textVisible') is True for s in samples):
                errors.append(f'{ident} no visible subtitle ink was checked')
        for sample in samples:
            if expected.get('fit') == 'bottom-full-width' and sample.get('settled'):
                bounds = sample.get('presenterAlphaBox', [])
                canvas = sample.get('canvas', [])
                if len(bounds) != 4 or len(canvas) != 2:
                    errors.append(f'{ident} missing measured presenter alpha bounds')
                elif bounds[0] > 1 or bounds[2] < canvas[0] - 1 or bounds[3] < canvas[1] - 1:
                    errors.append(f'{ident} presenter does not cover bottom width')
            if subtitle.get('visibility') == 'unoccluded' and sample.get('textVisible'):
                if sample.get('occludedGlyphPixels') != 0:
                    errors.append(f'{ident} foreground hides subtitle ink')
        comparison = group.get('phaseComparison', {})
        if not comparison.get('evidence') or not comparison.get('reviewed'):
            errors.append(f'{ident} missing reviewed encoded phase comparison')
        for filename in comparison.get('evidence', []):
            if not (project / filename).is_file():
                errors.append(f'{ident} missing phase comparison {filename}')
        if strict and [x.get('referenceFrame') for x in comparison.get('phaseFrames', [])] != [x.get('frame') for x in stages]:
            errors.append(f'{ident} encoded comparison must cover every observed phase')
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--rendered', action='store_true')
    args = parser.parse_args()
    findings = validate(args.project.resolve(), args.audit.resolve(), args.rendered)
    print(json.dumps({'passed': not findings, 'errors': findings}, ensure_ascii=False, indent=2))
    raise SystemExit(bool(findings))
