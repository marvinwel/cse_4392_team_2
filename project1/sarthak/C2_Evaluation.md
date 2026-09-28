# C2 Evaluation

**Evaluation only — do not send to the generating model.**

TP **12**, FP **15**, FN **15**. Precision **44.44%**, recall **44.44%**, F1 **44.44%**.

| Category | TP | FP | FN |
| --- | ---: | ---: | ---: |
| class | 6 | 1 | 1 |
| attr | 4 | 9 | 8 |
| relation | 2 | 4 | 5 |
| assclass | 0 | 1 | 1 |

## True positives

- `Customer.address` → `customer.address` (attr!A4)
- `Customer.dateOfBirth` → `customer.date of birth` (attr!A5)
- `Customer.name` → `customer.name` (attr!A3)
- `LanguageTape.level` → `language tape.level` (attr!A8)
- `Book` → `book` (class!A5)
- `Customer` → `customer` (class!A7)
- `LanguageTape` → `language tape` (class!A6)
- `Library` → `library` (class!A1)
- `MembershipCard` → `membership card` (class!A3)
- `Section` → `section` (class!A2)
- `ag(Library, Section)` → `ag(library,section)` (relation!A7)
- `as(has, Customer, MembershipCard)` → `as(has,customer,membership card)` (relation!A2)

## False positives

- `Loan(Customer, Item)` (assclass)
- `Book.author` (attr)
- `Book.title` (attr)
- `Customer.membershipNumber` (attr)
- `Customer.membershipValid` (attr)
- `Item.barCode` (attr)
- `Item.reserved` (attr)
- `LanguageTape.titleLanguage` (attr)
- `Loan.current` (attr)
- `Section.classificationMark` (attr)
- `Item` (class)
- `as(borrows, Customer, Item)` (relation)
- `as(issues, Library, Item)` (relation)
- `isa(Book, Item)` (relation)
- `isa(LanguageTape, Item)` (relation)

## False negatives

- `loan transaction(customer,book)` (assclass!A1)
- `book.subject` (attr!A6)
- `language tape.language` (attr!A7)
- `loan item.bar code` (attr!A1)
- `loan item.title` (attr!A2)
- `loan transaction.borrow` (attr!A9)
- `loan transaction.renew` (attr!A10)
- `loan transaction.reserve` (attr!A11)
- `membership card.id` (attr!A12)
- `loan item` (class!A4)
- `as(borrow, customer,book)` (relation!A1)
- `as(hold,section,loan item)` (relation!A4)
- `as(issue,library,membership card)` (relation!A3)
- `isa(book,loan item)` (relation!A5)
- `isa(language tape,loan item)` (relation!A6)

Unique predictions: 27. Reference elements: 27. Duplicate predictions ignored: 0.

These are reference-conformity scores under the stated lexical protocol; a mismatch does not by itself prove that the alternative model is semantically invalid.
