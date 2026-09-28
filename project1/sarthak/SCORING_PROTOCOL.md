# Scoring protocol

Evaluate only after saving each raw classification response. The generator receives the domain description, the supplied classification rules, and a fixed clean phrase inventory. Never send the expert workbook, extracted reference elements, evaluation files, previous output, or target counts to the generator.

Score unique atomic model elements as sets within their categories: class name; attribute owner and name; relationship kind, label where applicable, and ordered endpoints; association-class name and endpoints. Do not silently change ownership, endpoints, relationship kind, or model concepts to improve a score.

Normalize typography, case, camel case, spaces, and hyphens by lowercasing names and removing non-alphanumeric characters. Normalize only the explicitly listed association-label verb inflections in `tools/evaluate.py`. Do not stem noun names or rewrite synonyms. Do not give automatic semantic-synonym credit. Record the exact normalization and reference extraction before calculating C1, then hold them fixed for C2/C3. One predicted element can match at most one reference element. Duplicates are logged and counted once. Unsupported or unparseable asserted elements count as false positives; explanations do not count as model elements.

TP = matched elements; FP = predicted elements minus TP; FN = reference elements minus TP.
Precision = TP/(TP+FP). Recall = TP/(TP+FN). F1 = 2TP/(2TP+FP+FN). Report micro totals across categories, with category breakdowns and explicit matched/unmatched lists.

Use C1 as the baseline. For each subsequent candidate, retain it if micro F1 increases; for equal F1 prefer greater precision, then the shorter prompt. Preserve regressions. Three single runs show observed optimization behavior, not statistical significance or held-out performance. The Library reference is development feedback, not an independent test set.

Only general modeling procedures may be added following error analysis. No domain-specific reference answers, corrected tuples, target category counts, or score targets may be inserted into revised prompts. Domain-specific text in the fixed domain description and inventory remains unchanged.

The executable mapping and parser were established for C1 and are frozen for C2/C3. Source spellings and cell coordinates remain in every evaluation report. Association labels have/had/having/has share the lexical base have; issue/issued/issues share issue, and analogous documented inflections are handled for borrow, reserve, renew, hold, show, scan, read, and search. Names such as Member and Customer, SubjectSection and Section, titleLanguage and language, and Loan and LoanTransaction are not equated.
