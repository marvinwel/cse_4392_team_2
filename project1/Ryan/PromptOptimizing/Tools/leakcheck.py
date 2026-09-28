# Leak check: search a prompt for every answer-key entry (identification + classification) from all three domains.
import re, json, subprocess, sys
def toks(s): return re.findall(r"[a-z0-9()\[\]%'-]+", s.lower())
def sing(w): return w[:-1] if w.endswith('s') and len(w) > 3 and not w.endswith('ss') else w
def norm(s): return ' '.join(sing(w) for w in toks(s))
S = lambda a: [x.strip() for x in a.split(';') if x.strip()]
keys = {}
keys['Library ident'] = S('library; loan items / item; customers / customer; member; membership card; member number / membership number; details; name; address; date of birth; subject sections / section; classification mark; bar code; language tapes / language tape; books / book; title language; level; title; author(s); current loan; bar code reader; membership; book bar code; records; number of subject sections; types of loan items; number of items; update of records; issues / issued; shows; kept; denoted; borrow; reserved; renewed; extend; scanned; entered; read; stamped; searched; identified; French; beginner; daily; valid; two; 8 / maximum of 8; less than 8; a number of; has a title language; has a title, and author(s); made up of; customer is known as a member; language tapes, and books [are] two types of loan items')
keys['Car Rental ident'] = S('vehicle; manufacturer; price class; rental price; car; passenger car; transmission; doors; sedan; hatchback; options; additional charge; location; other forms of vehicle; customer; rental plan; daily unlimited miles plan; weekend savings plan; reservation; salesperson; reservation form; contract; block reservation; invoice; rentals; company; rental charge; credit card; credit card processing company; makes of car; model of car; depreciation of the rental cars; time of reservation; period of time; taken from; returned to; select; reserving; process; archive; sign; make; cover; checked out; pay; sent to; processed; available; not available; rented out; purchase; repair; maintenance; disposal; automatic; manual; in person; by phone; voided; opened; two; four; one or more; several; file cabinet')
G = json.loads(subprocess.run(['node', '-e', "console.log(JSON.stringify(require('./ntsskey.js')))"], capture_output=True, text=True).stdout)
keys['NTSS ident'] = [i for h, items in G for i in items]
keys['Library class'] = S('library; section; membership card; loan item; book; language tape; customer; bar code; title; name; address; date of birth; subject; language; level; loan transaction; borrow; renew; reserve; id; has; issue; hold')
keys['Car Rental class'] = S('Vehicle; Passenger Car; Location; Customer; Rental Plan; Daily unlimited Miles Plan; Weekend Savings Plan; Salesperson; Contract; Block Reservation; Invoice; Company; Credit Card Company; manufacturer; price class; price; status; make; model; transmission; number of doors; body style; additional charge; depreciation; time of reservation; grace period; means; void; opened; rental charge; purchase; repair; maintenance; disposed; automatic; manual; sedan; hatchback; in person; by phone; taken from; returned to; select; reserve; process; archive; sign; bill for; check out; pay; sent to; processed by; Reservation; Payment; Pay by Credit Card')
keys['NTSS class'] = S('Customer; Account; Event; Domain; Organizer; Trade Show; Participant; Exhibitor; Observer; Speaker; Seminar; Proposal; Committee; Reviewer; Booth; charges; payment; balance; contact information; website; type; theme; slogan; location; duration; fee; Keynote address; conference room; evaluation; status; pending review; accepted; rejected; invited; selected; price; size; create; promote; organize; run; has; attend; register; setup-with; submit; reviewed-by; rent; Registration; Review')
text = open(sys.argv[1]).read()
tn = ' ' + norm(text) + ' '
total = 0
for k, entries in keys.items():
    hits = []
    for e in entries:
        for alt in e.split(' / '):
            a = norm(alt)
            if a and re.search(r'(?<![a-z0-9])' + re.escape(a) + r'(?![a-z0-9])', tn):
                m = re.search(r'(?<![a-z0-9])' + re.escape(a) + r'(?![a-z0-9])', tn)
                hits.append((alt, tn[max(0, m.start()-30):m.end()+20].strip()))
    total += len(hits)
    print(f'== {k}: {len(entries)} entries, {len(hits)} matches')
    for h in hits: print('   ', repr(h[0]), '->', '...' + h[1] + '...')
# multi-word check: any 2-word sequence from any answer entry appearing in the prompt
bi = set()
for entries in keys.values():
    for e in entries:
        for alt in e.split(' / '):
            w = norm(alt).split()
            for i in range(len(w) - 1): bi.add(w[i] + ' ' + w[i+1])
found = sorted(b for b in bi if f' {b} ' in tn)
print('== any 2-word sequence from any key found in prompt:', found)
