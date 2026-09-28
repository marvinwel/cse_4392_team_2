"""Post-generation evaluator. Never upload this file or its outputs to the generator."""
from pathlib import Path
import argparse, datetime, hashlib, json, re
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {'CLASSES': 'class', 'ATTRIBUTES': 'attr', 'RELATIONSHIPS': 'relation', 'ASSOCIATION CLASSES': 'assclass'}
VERB_INFLECTIONS = {
    'borrows': 'borrow', 'borrowed': 'borrow', 'borrowing': 'borrow',
    'issues': 'issue', 'issued': 'issue', 'issuing': 'issue',
    'reserves': 'reserve', 'reserved': 'reserve', 'reserving': 'reserve',
    'renews': 'renew', 'renewed': 'renew', 'renewing': 'renew',
    'holds': 'hold', 'held': 'hold', 'holding': 'hold',
    'has': 'have', 'had': 'have', 'having': 'have',
    'shows': 'show', 'showed': 'show', 'shown': 'show',
    'scans': 'scan', 'scanned': 'scan',
    'reads': 'read', 'searches': 'search', 'searched': 'search',
}

def name(s):
    # Deliberately no semantic aliases: e.g. different owner/name words remain different.
    return re.sub(r'[^a-z0-9]', '', s.casefold())

def key(category, text):
    text = text.strip().strip('`')
    if category == 'class':
        return (category, name(text))
    if category == 'attr' and '.' in text:
        owner, attribute = text.split('.', 1)
        return (category, name(owner), name(attribute))
    m = re.fullmatch(r'([^()]+)\(([^()]*)\)', text)
    if m:
        kind = name(m.group(1))
        args = [x.strip() for x in m.group(2).split(',')]
        if category == 'relation' and kind == 'as' and len(args) == 3:
            label = name(args[0])
            return (category, kind, VERB_INFLECTIONS.get(label, label), name(args[1]), name(args[2]))
        if category == 'relation' and kind in ('isa', 'ag') and len(args) == 2:
            return (category, kind, *(name(a) for a in args))
        if category == 'assclass' and len(args) == 2:
            return (category, kind, *(name(a) for a in args))
    return (category, 'UNPARSED', text)

def read_output(path):
    category = None
    elements, duplicates = {}, []
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        text = re.sub(r'^\s*[-*•]\s+', '', line).strip().strip('`')
        header = text.strip('*').rstrip(':').upper()
        if header in CATEGORIES:
            category = CATEGORIES[header]
            continue
        if not text or text.upper() == 'NONE' or text.startswith('```'):
            continue
        if category is None:
            raise ValueError(f'Unexpected preamble at line {line_no}: {text}')
        k = key(category, text)
        item = {'category': category, 'element': text, 'line': line_no, 'normalized_key': list(k)}
        if k in elements:
            duplicates.append(item)
        else:
            elements[k] = item
    return elements, duplicates

def reference():
    path = ROOT / 'inputs/evaluation_only/library-expert-1.xlsx'
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    elements = {}
    for sheet in CATEGORIES.values():
        for row in wb[sheet]:
            for cell in row:
                if cell.value is not None:
                    text = str(cell.value).strip()
                    k = key(sheet, text)
                    assert k not in elements, f'Duplicate reference element: {text}'
                    elements[k] = {'category': sheet, 'element': text, 'source': f'{sheet}!{cell.coordinate}', 'normalized_key': list(k)}
    assert len(elements) == 27
    (ROOT / 'inputs/evaluation_only/Reference_Elements.json').write_text(json.dumps(list(elements.values()), indent=2) + '\n')
    return elements

def metrics(tp, fp, fn):
    return {'TP': tp, 'FP': fp, 'FN': fn, 'precision': tp/(tp+fp) if tp+fp else 0,
            'recall': tp/(tp+fn) if tp+fn else 0, 'F1': 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0}

def evaluate(run):
    folder = ROOT / run
    raw = folder / f'{run}_Raw_Output.txt'
    assert raw.is_file(), 'Save the model response before opening the reference.'
    predicted, duplicates = read_output(raw)
    truth = reference()
    tp_keys, fp_keys, fn_keys = set(predicted)&set(truth), set(predicted)-set(truth), set(truth)-set(predicted)
    report = {'run': run, 'evaluated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'method': 'Frozen normalized lexical exact match with category, ownership, kind, and ordered endpoints preserved',
              'raw_output_sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
              'reference_count': len(truth), 'prediction_count': len(predicted),
              **metrics(len(tp_keys), len(fp_keys), len(fn_keys)),
              'by_category': {},
              'matches': [{'prediction': predicted[k], 'reference': truth[k]} for k in sorted(tp_keys)],
              'false_positives': [predicted[k] for k in sorted(fp_keys)],
              'false_negatives': [truth[k] for k in sorted(fn_keys)], 'duplicates_ignored': duplicates}
    for cat in CATEGORIES.values():
        report['by_category'][cat] = metrics(sum(k[0]==cat for k in tp_keys), sum(k[0]==cat for k in fp_keys), sum(k[0]==cat for k in fn_keys))
    (folder/f'{run}_Evaluation.json').write_text(json.dumps(report, indent=2)+'\n')
    lines = [f'# {run} Evaluation', '', '**Evaluation only — do not send to the generating model.**', '',
             f"TP **{report['TP']}**, FP **{report['FP']}**, FN **{report['FN']}**. Precision **{report['precision']:.2%}**, recall **{report['recall']:.2%}**, F1 **{report['F1']:.2%}**.", '',
             '| Category | TP | FP | FN |', '| --- | ---: | ---: | ---: |']
    lines += [f"| {cat} | {m['TP']} | {m['FP']} | {m['FN']} |" for cat,m in report['by_category'].items()]
    lines += ['', '## True positives', '']
    lines += [f"- `{m['prediction']['element']}` → `{m['reference']['element']}` ({m['reference']['source']})" for m in report['matches']]
    lines += ['', '## False positives', ''] + [f"- `{x['element']}` ({x['category']})" for x in report['false_positives']]
    lines += ['', '## False negatives', ''] + [f"- `{x['element']}` ({x['source']})" for x in report['false_negatives']]
    lines += ['', f"Unique predictions: {len(predicted)}. Reference elements: {len(truth)}. Duplicate predictions ignored: {len(duplicates)}.",
              '', 'These are reference-conformity scores under the stated lexical protocol; a mismatch does not by itself prove that the alternative model is semantically invalid.']
    (folder/f'{run}_Evaluation.md').write_text('\n'.join(lines)+'\n')
    return {k: report[k] for k in ['run','TP','FP','FN','precision','recall','F1','by_category']}

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('run', choices=['C1','C2','C3'])
    print(json.dumps(evaluate(parser.parse_args().run), indent=2))
