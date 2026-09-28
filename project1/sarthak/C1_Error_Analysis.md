# C1 Error Analysis

Evaluation only. TP 10, FP 23, FN 17; precision 30.30%, recall 37.04%, F1 33.33%.

- Classes: six matches, three extras, one missing. The output duplicates the customer/member role, includes an input device, and uses SubjectSection where the reference says section.
- Attributes: only loan item.bar code and language tape.level match. Customer attributes moved to Member, and several source-derived labels or owners differ from the reference.
- Relationships: only the two inheritance links match. Procedural scanning/reading/searching relations inflate false positives. The borrowing endpoint, card relations, and section aggregation differ from the reference.
- Association class: Loan(Customer, LoanItem) does not match loan transaction(customer,book) under the strict naming/endpoint protocol.

The reference also contains modeling choices not stated literally in the description, including book.subject and the specific event fields and names. These are reference-conformity mismatches; the score does not establish that every source-grounded alternative is conceptually wrong. Do not supply those expected elements to the generator.

Hypothesis for C2: resolving naming aliases and filtering implementation actions will reduce unnecessary elements and prevent attribute ownership drift. Revised instructions describe general procedures only; they contain no expected Library tuples or target counts.

Decision: establish C1 as the baseline and test C2. Preserve the full C1 response and all its errors.
