# C2 Error Analysis

Evaluation only. TP 12, FP 15, FN 15; precision 44.44%, recall 44.44%, F1 44.44%. Improvement over C1: 11.11 percentage points of F1.

C2 removed the duplicate Member and the input-device class, restored customer attribute ownership, recovered the section aggregation and customer/card possession, and eliminated many procedural associations. These changes reduced false positives from 23 to 15.

However, the generic instruction to prefer a shorter head noun changed LoanItem to Item. Under the fixed lexical protocol, this loses the class, its barcode attribute, and both inheritance endpoints. The same rule did recover Section. It should therefore be tightened, not converted into a Library-specific naming instruction.

The state audit added customer.membershipValid, Item.reserved, and Loan.current. They are plausible interpretations of domain states but absent from the reference. Several remaining attribute owners, association endpoints, and association-class names also differ. Expected labels and tuples must remain in evaluation files only.

Hypothesis for C3: protect informative compound noun identities, require evidence for stored state fields, and check attribute commonality and per-clause relationship participants. This should preserve C2's alias/scope gains while reducing naming drift and unsupported elements. The revision supplies no reference-specific names or corrected tuples.

Decision: accept C2 over C1 and use C2 as the parent for C3. Retain C2 unless C3 improves the fixed micro F1, with the preregistered tie-breakers.
