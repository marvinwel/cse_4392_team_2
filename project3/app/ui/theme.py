"""Colors and small building blocks shared by every screen."""
from rich import box
from rich.console import Group
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

BG, PANEL, CARD, HOVER = "#101827", "#182438", "#1b2a40", "#21364c"
LINE, CLINE, FOCUS = "#2d3c52", "#31435a", "#49b8cb"
OVER, TITLE, INTRO, MUTED, FOOT = "#61ddf1", "#f8fafc", "#bac7d7", "#93a3b9", "#899bad"
NUMBG, NUMFG, CY = "#173b4d", "#86e9fa", "#67e8f9"
GREEN, AMBER, RED, BLUE, PURPLE = "#86efac", "#fbbf24", "#fda4af", "#93c5fd", "#c4b5fd"
BODY, SOFT = "#e2e8f0", "#b9cadb"
KB = "#bcd0e4 on #2b3d54"
SELECTED = "bold #0b1220 on #67e8f9"

CHIP_PLAIN = "bold #a8c0d6 on #25364c"
CHIP_GREEN = f"bold {GREEN} on #1b473b"
CHIP_AMBER = f"bold {AMBER} on #4e3f25"
CHIP_RED = f"bold {RED} on #4c2434"

BTN_PRIMARY = ("#d5faff", "#1d4456", "#3a7c8c")
BTN_PLAIN = ("#c6d5e6", "#1e2d41", "#394b63")
BTN_AMBER = ("#ffe2a4", "#573b24", "#8a6734")
BTN_RED = ("#ffd0d4", "#512c33", "#9c4a55")
BTN_OFF = ("#b98a90", "#3a2529", "#6e3a42")

STEPS = ["Load Java source", "EP/BVA generation", "AI test review & merge", "Human review #1",
         "Original JUnit & repair", "Original JaCoCo coverage", "Coverage-gap test generation",
         "State-pattern refactoring", "Human review #2", "Refactored JUnit & coverage", "Final Results"]
STEP_NOTES = ["Original SeasonSwitch input", "Parallel test generation agents", "Validate and deduplicate",
              "Generated JUnit tests", "Run and repair failures", "Full-program branch coverage",
              "Generate and rerun targeted tests", "Generate state classes", "Review Java changes",
              "Adapt tests and verify", "Automated verification only"]


def pad(item):
    return Padding(item, (0, 3))


def header(over, title, intro, pill=None, pill_style=None):
    top = Table.grid(expand=True)
    top.add_column()
    top.add_column(justify="right")
    top.add_row(Text(" ".join(over), style=f"bold {OVER}"),
                Text.assemble((f" {pill} ", pill_style or f"bold {AMBER} on #382d1e")) if pill else Text(""))
    return [Text(""), pad(top), pad(Rule(style=LINE)), Text(""),
            pad(Text(title, style=f"bold {TITLE}")), pad(Text(intro, style=INTRO)), Text("")]


def keyrow(lead, keys):
    row = Text(style=FOOT)
    row.append(lead)
    for key, label in keys:
        row.append(f" {key} ", style=KB)
        row.append(f" {label}    ")
    line = pad(row)
    line.pinned = True   # key hints stay on the bottom rows of the window, whatever the scroll position
    return line


def note_line(text):
    return pad(Text(text, style=FOOT))


def stage_strip(n, in_run=True):
    """Where-am-I strip: n is the 1-based workflow step this screen belongs to.
    in_run=False: the screen shows a saved report and no workflow is running, so the
    strip only says which step the screen belongs to."""
    dots = Text()
    for i in range(1, len(STEPS) + 1):
        if i < n:
            dots.append("● ", style=GREEN)
        elif i == n:
            dots.append("◉ ", style=f"bold {AMBER}")
        else:
            dots.append("○ ", style="#70849a")
    line1 = Text.assemble((f" STEP {n} OF {len(STEPS)} ", SELECTED), ("  " + STEPS[n - 1], f"bold {TITLE}"))
    top = Table.grid(expand=True)
    top.add_column(ratio=1)
    top.add_column(justify="right")
    top.add_row(line1, dots)
    nxt = STEPS[n] if n < len(STEPS) else "none, this is the last step"
    prev = STEPS[n - 2] if n > 1 else "none, this is the first step"
    if in_run:
        line2 = Text.assemble(("Done before this: ", MUTED), (prev, GREEN), ("     Next: ", MUTED), (nxt, INTRO))
    else:
        dots = Text("saved report", style=MUTED)
        line2 = Text("This screen belongs to this workflow step. No workflow run is in progress in this session.", style=MUTED)
    return pad(Panel(Group(top, line2), box=box.ROUNDED, border_style=LINE, style="on #101e30", padding=(0, 1)))


def pnl(*items, border=LINE, bg=PANEL, padding=(1, 2)):
    return Panel(Group(*items), box=box.ROUNDED, border_style=border, style=f"on {bg}", padding=padding)


def warn_pnl(*items):
    return pnl(*items, border="#82632d", bg="#2f281e")


def head(text):
    return Text(text, style=f"bold {TITLE}")


def chip(text, style=CHIP_PLAIN):
    return Text.assemble((f" {text} ", style))


def btn(label, key, colors=BTN_PLAIN):
    fg, bg, border = colors
    return Panel(Text.assemble((label, f"bold {fg}"), (f"  ·  press {key}", fg)), box=box.ROUNDED,
                 border_style=border, style=f"on {bg}", padding=(0, 1), expand=False)


def btnrow(*buttons):
    row = Table.grid(padding=(0, 1))
    row.add_row(*buttons)
    return row


def bar(fraction, width):
    filled = max(0, min(width, round(width * fraction)))
    return Text.assemble(("█" * filled, "#22d3ee"), ("█" * (width - filled), "#324156"))


def amber_note(text):
    return Text.assemble(("▌", "#efb84c on #3b3022"), (f" {text} ", "#f3ca73 on #3b3022"))


def stat_row(items):
    """items: (label, big value, color, optional small note)."""
    row = Table.grid(expand=True, padding=(0, 1))
    cells = []
    for label, big, color, *rest in items:
        row.add_column(ratio=1)
        parts = [Text(label, style=f"bold {TITLE}"), Text(""), Text(str(big), style=f"bold {color}")]
        if rest:
            parts.append(Text(rest[0], style=MUTED))
        cells.append(Panel(Group(*parts), box=box.ROUNDED, border_style=LINE, style=f"on {PANEL}", padding=(0, 2)))
    row.add_row(*cells)
    return pad(row)


def tabs(names, active):
    """names: [(key, label)]; the active tab is filled."""
    row = Table.grid(expand=True)
    cells = []
    for key, label in names:
        row.add_column(ratio=1)
        cells.append(Text(label, style="bold #eafcff on #294a60" if key == active else "bold #9fb1c4", justify="center"))
    row.add_row(*cells)
    return Panel(row, box=box.ROUNDED, border_style="#2c3c52", style="on #101e30", padding=(0, 1))


def expander(label, is_open=False):
    return Panel(Text.assemble(("▼ " if is_open else "▶ ", INTRO), (label, f"bold {TITLE}")),
                 box=box.ROUNDED, border_style=CLINE, style="on #16263a", padding=(0, 1))


def select_card(items, focus, title_text):
    """A card that is unmistakable when selected: solid label, heavy cyan border."""
    title = Text.assemble((f" SELECTED · {title_text} ", SELECTED)) if focus else Text.assemble((f" {title_text} ", MUTED))
    return Panel(Group(*items), title=title, title_align="left", box=box.HEAVY if focus else box.ROUNDED,
                 border_style=CY if focus else "#33455c", style=f"on {'#1a3c50' if focus else '#15243a'}",
                 padding=(0, 1))


def code_box(title, right, body):
    top = Table.grid(expand=True)
    top.add_column(ratio=1)
    top.add_column(justify="right")
    top.add_row(Text(title, style="bold #a8bed2"), Text(right, style="bold #a8bed2"))
    return Panel(Group(top, Rule(style="#33445a"), body), box=box.ROUNDED, border_style="#32435a",
                 style="on #0d1726", padding=(0, 1))


def kind_badge(kind):
    if kind == "EP":
        return (" EP ", f"bold {BLUE} on #163958")
    if kind == "BVA":
        return (" BVA ", f"bold {PURPLE} on #3a2755")
    return (" TEST ", CHIP_PLAIN)
