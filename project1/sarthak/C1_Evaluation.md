# C1 Evaluation

**Evaluation only — do not send to the generating model.**

TP **10**, FP **23**, FN **17**. Precision **30.30%**, recall **37.04%**, F1 **33.33%**.

| Category | TP | FP | FN |
| --- | ---: | ---: | ---: |
| class | 6 | 3 | 1 |
| attr | 2 | 8 | 10 |
| relation | 2 | 11 | 5 |
| assclass | 0 | 1 | 1 |

## True positives

- `LanguageTape.level` → `language tape.level` (attr!A8)
- `LoanItem.barCode` → `loan item.bar code` (attr!A1)
- `Book` → `book` (class!A5)
- `Customer` → `customer` (class!A7)
- `LanguageTape` → `language tape` (class!A6)
- `Library` → `library` (class!A1)
- `LoanItem` → `loan item` (class!A4)
- `MembershipCard` → `membership card` (class!A3)
- `isa(Book, LoanItem)` → `isa(book,loan item)` (relation!A5)
- `isa(LanguageTape, LoanItem)` → `isa(language tape,loan item)` (relation!A6)

## False positives

- `Loan(Customer, LoanItem)` (assclass)
- `Book.author` (attr)
- `Book.title` (attr)
- `LanguageTape.titleLanguage` (attr)
- `Member.address` (attr)
- `Member.dateOfBirth` (attr)
- `Member.membershipNumber` (attr)
- `Member.name` (attr)
- `SubjectSection.classificationMark` (attr)
- `BarCodeReader` (class)
- `Member` (class)
- `SubjectSection` (class)
- `ag(Library, SubjectSection)` (relation)
- `as(borrows, Customer, LoanItem)` (relation)
- `as(issued, Customer, MembershipCard)` (relation)
- `as(issues, Library, LoanItem)` (relation)
- `as(reads, BarCodeReader, LoanItem)` (relation)
- `as(renews, Customer, LoanItem)` (relation)
- `as(reserves, Customer, LoanItem)` (relation)
- `as(scans, BarCodeReader, Member)` (relation)
- `as(searches, Library, LoanItem)` (relation)
- `as(shows, MembershipCard, Member)` (relation)
- `isa(Customer, Member)` (relation)

## False negatives

- `loan transaction(customer,book)` (assclass!A1)
- `book.subject` (attr!A6)
- `customer.address` (attr!A4)
- `customer.date of birth` (attr!A5)
- `customer.name` (attr!A3)
- `language tape.language` (attr!A7)
- `loan item.title` (attr!A2)
- `loan transaction.borrow` (attr!A9)
- `loan transaction.renew` (attr!A10)
- `loan transaction.reserve` (attr!A11)
- `membership card.id` (attr!A12)
- `section` (class!A2)
- `ag(library,section)` (relation!A7)
- `as(borrow, customer,book)` (relation!A1)
- `as(has,customer,membership card)` (relation!A2)
- `as(hold,section,loan item)` (relation!A4)
- `as(issue,library,membership card)` (relation!A3)

Unique predictions: 33. Reference elements: 27. Duplicate predictions ignored: 0.

These are reference-conformity scores under the stated lexical protocol; a mismatch does not by itself prove that the alternative model is semantically invalid.
