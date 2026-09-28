# Identification Prompt Optimization Changelog

## Results

| Version | Hypothesis | Major Change | TP | FP | FN | Precision | Recall | F1 | Decision |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| **V1** | A structured zero-leakage prompt should improve identification over a generic request. | Added phrase families, coverage pass, precision pass, and flat-list output. | 35 | 31 | 20 | 53.03% | 63.64% | **57.85%** | **Revise.** Recall and precision were both too low; the prompt still missed many expected phrases and returned too many non-matching variants. |
| **V2** | Better phrase boundaries, alias control, and X-of-Y extraction should reduce FP while recovering missed items. | Added X-of-Y extraction, duplicate/alias rules, base-form verbs, tighter phrase boundaries, and dedicated value/quantity passes. | 44 | 17 | 11 | 72.13% | 80.00% | **75.86%** | **Keep V2 as the baseline and revise.** It produced the highest F1 and improved both precision and recall, but it remains below the 97% target. |
| **V3** | Preserving coordinated relationships and filtering fragments should further reduce FP. | Added coordinated-relationship preservation and stronger fragment filtering. | 42 | 16 | 13 | 72.41% | 76.36% | **74.34%** | **Revert to V2.** Precision improved only slightly, while recall dropped and overall F1 decreased. |
| **V4** | Keeping meaningful nested nouns, values, and quantities should recover V3 false negatives. | Added stronger atomic noun, value/state, quantity, and X-of-Y retention. | 47 | 30 | 8 | 61.04% | 85.45% | **71.21%** | **Revert to V2.** Recall improved, but false positives increased sharply and reduced precision and F1. |

**Current best:** V2 — **75.86% F1**  
**Required target:** **97% F1**

## Version Notes

### V1
Introduced a structured zero-leakage identification method with explicit phrase families plus coverage and precision checks.

### V2
Added tighter phrase boundaries, X-of-Y extraction, alias/duplicate control, and normalized verbs. This produced the best F1.

### V3
Added coordinated-relationship preservation and stronger fragment filtering. Recall fell, so the change was not retained.

### V4
Tried to recover missed atomic phrases by keeping more nested nouns, values, and quantities. Recall rose, but over-extraction increased false positives.

## Current Direction

Return to **V2** and make the next change from that version. The next iteration should focus on exact phrase granularity without sacrificing V2's recall.
