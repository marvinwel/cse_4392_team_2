"""The dashboard's screens. Each one shows real data handed to it and turns keys into actions."""
from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from . import data
from . import theme as T
from .runner import NODE_LABEL, STEP_AI, STEP_AI_WHEN, CommandRun, WorkflowRun, redact
from .term import Screen

MENU = [
    ("Run Complete Workflow", "make run · make auto · LangGraph end-to-end",
     [("run", "Generate/review/run tests through current LangGraph"),
      ("auto", "Same run with the human reviews auto-approved (testing only)")]),
    ("Original Java Testing", "test-original · test-original-current · verify-original",
     [("test-original", "Copy latest merged tests; run JUnit + JaCoCo"),
      ("test-original-current", "Run installed original tests (no copying)"),
      ("verify-original", "Strict Maven build/100% branch coverage gate")]),
    ("Refactored Java Testing", "test-refactored · verify-refactored",
     [("test-refactored", "Run installed refactored tests"),
      ("verify-refactored", "Strict refactored Maven coverage gate")]),
    ("Python & Project Checks", "test-python · check",
     [("test-python", "Run Python unit tests (no LLM/Maven)"), ("check", "Check Python syntax")]),
    ("Tools & Maintenance", "help · build-merger · clean · clean-all",
     [("build-merger", "Force clean rebuild of Java test merger"),
      ("clean", "Clean Java test build outputs, preserve merger JAR"),
      ("clean-all", "Also clean merger JAR (run auto-rebuilds it)")]),
]
PHASE_OF_TARGET = {"test-original": "original", "test-original-current": "original", "verify-original": "original",
                   "test-refactored": "refactored", "verify-refactored": "refactored"}


def quit_or_warn(app):
    run = app.workflow
    if run and run.status in ("running", "waiting", "starting") and not getattr(app, "quit_armed", False):
        app.quit_armed = True
        app.message = "A workflow run is in progress. Press q again to stop it and quit."
        return
    app.quit()


def number_badge(n):
    badge = Text()
    badge.append("     \n", style=f"on {T.NUMBG}")
    badge.append(f"  {n}  \n", style=f"bold {T.NUMFG} on {T.NUMBG}")
    badge.append("     ", style=f"on {T.NUMBG}")
    return badge


def menu_card(n, title, sub, selected):
    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(width=5)
    grid.add_column(ratio=1)
    grid.add_column(width=2, justify="right")
    body = Text()
    body.append("\n")
    body.append(title + "\n", style=f"bold {T.TITLE}")
    body.append(sub, style=T.MUTED)
    grid.add_row(number_badge(n), body, Text("\n▶" if selected else "\n›", style=f"bold {T.CY}"))
    return Panel(grid, box=box.ROUNDED, border_style=T.FOCUS if selected else T.CLINE,
                 style=f"on {T.HOVER if selected else T.CARD}", padding=(0, 1))


def edge_of(index, count):
    """Tells the display when the selection is the first or last item of a list."""
    return "first" if index <= 0 else "last" if index >= count - 1 else None


def agent_record(kind, phase, app):
    """What the repair agent (kind 'repair') or the gap-test agent (kind 'gap') recorded for a phase.
    Nothing is inferred: each line is one row the workflow wrote."""
    rows, where, limits = data.repair_rows(kind, phase, app.workflow.values if app.workflow else None)
    agent = "Repair agent" if kind == "repair" else "Gap-test agent"
    line = Table.grid(expand=True, padding=(0, 1))
    line.add_column(width=2)
    line.add_column(ratio=1)
    if not where:
        line.add_row(Text("○", style="#70849a"),
                     Text.assemble((f"{agent}: no record yet\n", f"bold {T.TITLE}"),
                                   ("It runs inside the complete workflow (make run). No run with a repair list "
                                    "has been saved yet.", T.SOFT)))
        return [line]
    if not rows:
        why = ("no test run failed" if kind == "repair" else "no branch was left uncovered")
        line.add_row(Text("●", style=T.GREEN),
                     Text.assemble((f"{agent} was not needed in the {phase} phase\n", f"bold {T.TITLE}"),
                                   (f"It recorded nothing for this phase, so {why} when the workflow checked. "
                                    f"Source: {where}.", T.SOFT)))
        return [line]
    last = rows[-1].get("outcome", "")
    good, bad = ("rerun_passed", "approved", "applied"), ("exhausted", "rerun_failed", "ai_error", "human_rejected")
    color = T.GREEN if last == "rerun_passed" else T.RED if last in bad else T.AMBER
    unit = "try" if kind == "repair" else "round"
    used = limits.get("used", 0)
    line.add_row(Text("◉", style=color),
                 Text.assemble((f"{agent}: {data.REPAIR_OUTCOME.get(last, last)}\n", f"bold {T.TITLE}"),
                               (f"{used} of 3 {unit}{'s' if used != 1 else ''} used in the {phase} phase. Source: {where}.", T.SOFT)))
    # One card per try: a try starts when the AI answers, then come the review and the rerun.
    tries = []
    for row in rows:
        if row.get("outcome") in ("proposed", "ai_error", "exhausted") or not tries:
            tries.append([])
        tries[-1].append(row)
    items = [line]
    for number, steps in enumerate(tries, 1):
        final = steps[-1].get("outcome", "")
        edge = "#2f6b52" if final in good else "#9c4a55" if final in bad else "#8a6734"
        head = Text.assemble((f" {unit.upper()} {steps[0].get('attempt') or number} ", "bold #0b1220 on #86e9fa"), ("  ", ""))
        for i, step in enumerate(steps):
            outcome = step.get("outcome", "")
            words = data.REPAIR_OUTCOME.get(outcome, outcome)
            if outcome == "approved" and step.get("auto"):
                words = "Auto-approved (no person)"
            if step.get("total") is not None:
                words += f" {step.get('passed')}/{step.get('total')}"
            style = T.CHIP_GREEN if outcome in good and not step.get("auto") else T.CHIP_RED if outcome in bad else T.CHIP_AMBER
            head.append_text(T.chip(words, style))
            if i < len(steps) - 1:
                head.append("  →  ", style=T.MUTED)
        body = [head]
        facts = Table.grid(expand=True, padding=(0, 2))
        facts.add_column(width=19)
        facts.add_column(ratio=1)

        def fact(label, value, value_style=T.BODY):
            facts.add_row(Text(label, style="bold #9dc6fb"), value if isinstance(value, Text) else Text(redact(str(value)), style=value_style, overflow="fold"))

        first = steps[0]
        if first.get("target"):
            what = "production Java code" if first["target"] == "code" else "tests only"
            fact("What it changes", f"{first.get('path') or first['target']} ({what})")
        if first.get("tests"):
            names = [str(name) for name in first["tests"]]
            fact("New tests" if kind == "gap" else "Failing tests",
                 f"{len(names)}: " + ", ".join(names[:8]) + (f" and {len(names) - 8} more" if len(names) > 8 else ""))
        if first.get("diagnosis"):
            reasons = [part.strip() for part in redact(str(first["diagnosis"])).split("; ") if part.strip()]
            shown = Text(overflow="fold")
            for n, reason in enumerate(reasons[:5]):
                shown.append(("\n" if n else "") + "• " + reason, style=T.SOFT)
            if len(reasons) > 5:
                shown.append(f"\n• and {len(reasons) - 5} more (full list in the change log)", style=T.MUTED)
            fact("Branches targeted" if kind == "gap" else "Reason from the AI", shown)
        for step in steps:
            if step.get("error"):
                fact("Why it failed", step["error"], T.RED)
            if step.get("feedback"):
                fact("Reviewer said", step["feedback"], T.AMBER)
        if facts.row_count:
            body += [Text(""), facts]
        items.append(Panel(Group(*body), box=box.ROUNDED, border_style=edge, style=f"on {T.CARD}", padding=(0, 1)))
    return items


# =========================================================================== 01 Main Menu
class MenuScreen(Screen):
    page_arrows = False
    focus_marker = "▶"

    def __init__(self):
        self.sel = 0

    def focus_edge(self):
        return edge_of(self.sel, len(MENU))

    def render(self, app):
        rows = [T.head("MAIN MENU"), Text("")]
        for i, (title, sub, _) in enumerate(MENU):
            rows.append(menu_card(i + 1, title, sub, i == self.sel))
        return T.header("LAUNCHER", "Multi-Agent Testing System",
                        "Choose an operation. Each one runs the same command as the plain Makefile target.") + [
            T.pad(T.pnl(*rows)), Text(""),
            T.keyrow("Navigation: ", [("1-5", "select"), ("↑ ↓", "move"), ("Enter", "open"), ("?", "help"), ("q", "quit")]),
            T.note_line("Without the dashboard: make run (human review), make auto (auto-approve), and the other make targets."), Text("")]

    def on_key(self, key, app):
        if key in ("1", "2", "3", "4", "5"):
            self.sel = int(key) - 1
            self.open(app)
        elif key == "up":
            self.sel, app.follow = (self.sel - 1) % len(MENU), True
        elif key == "down":
            self.sel, app.follow = (self.sel + 1) % len(MENU), True
        elif key == "enter":
            self.open(app)
        elif key == "?":
            app.push(HelpScreen())
        elif key == "q":
            quit_or_warn(app)

    def open(self, app):
        title, _, targets = MENU[self.sel]
        if self.sel == 0:
            run = app.workflow
            if run and run.status in ("starting", "running", "waiting"):
                app.open_workflow()            # a run is in progress: go back to it
            else:
                app.push(RunChoiceScreen())
        elif self.sel == 4:
            app.push(ToolsScreen())
        else:
            app.push(CommandMenuScreen(self.sel + 1, title, targets))


RUN_CHOICES = [
    ("Run with human review", "make run",
     "You approve the tests, the refactoring, and every repair or gap-test proposal. Use this for final evidence."),
    ("Test run with auto-approve", "make auto",
     "Every human review is approved automatically, with nobody checking. For testing only: not valid as final evidence."),
]


class RunChoiceScreen(Screen):
    """Menu item 1: run the complete workflow with the human reviews, or as an auto-approved test run."""
    focus_marker = "▶"
    page_arrows = False

    def __init__(self):
        self.sel = 0

    def focus_edge(self):
        return edge_of(self.sel, len(RUN_CHOICES))

    def render(self, app):
        rows = [T.head("RUN COMPLETE WORKFLOW"), Text("")]
        for i, (title, command, what) in enumerate(RUN_CHOICES):
            rows.append(menu_card(i + 1, title, f"{command} · {what}", i == self.sel))
        if app.workflow:
            rows += [Text(""), T.amber_note("A new run replaces the finished run shown in this session. "
                                            "Its saved reports stay on disk until the new run writes its own.")]
        return T.header("MENU ITEM 1", "Run Complete Workflow",
                        "Choose how the human review steps are answered. Both choices run the same LangGraph workflow.") + [
            T.pad(T.pnl(*rows)), Text(""),
            T.keyrow("Navigation: ", [("1-2", "select"), ("↑ ↓", "move"), ("Enter", "start the run"),
                                      ("Esc", "main menu"), ("q", "quit")]), Text("")]

    def on_key(self, key, app):
        if key in ("1", "2"):
            self.sel = int(key) - 1
            self.start(app)
        elif key in ("up", "down"):
            self.sel, app.follow = (self.sel + (1 if key == "down" else -1)) % len(RUN_CHOICES), True
        elif key == "enter":
            self.start(app)
        elif key == "esc":
            app.pop()
        elif key == "q":
            quit_or_warn(app)

    def start(self, app):
        app.pop()
        app.open_workflow(fresh=True, auto=self.sel == 1)


class HelpScreen(Screen):
    focus_marker = ""
    back_label = "Close Help"

    def render(self, app):
        keys = Table.grid(padding=(0, 2))
        keys.add_column(width=9)
        keys.add_column()
        for key, what in [("1-5", "Open that menu item"), ("↑ ↓", "Move the selection"),
                          ("Enter", "Open the selected item"), ("?", "Open this help"), ("q", "Quit")]:
            keys.add_row(Text(f" {key} ", style=T.KB), Text(what, style=T.INTRO))
        runs = Table.grid(padding=(0, 2))
        runs.add_column(width=28)
        runs.add_column()
        for i, (title, _, targets) in enumerate(MENU):
            if i:
                runs.add_row("", "")
            runs.add_row(Text(f"{i + 1}  {title}", style=f"bold {T.TITLE}"), "")
            for target, what in targets:
                runs.add_row(Text(f"  make {target}", style=T.CY), Text(what, style=T.MUTED))
        body = Group(T.head("KEYS"), Text(""), keys, Text(""), Rule(style=T.LINE), Text(""),
                     T.head("WHAT EACH ITEM RUNS"), Text(""), runs)
        return T.header("LAUNCHER", "Multi-Agent Testing System", "Help for the main menu.") + [
            T.pad(Panel(body, box=box.ROUNDED, border_style=T.FOCUS, style=f"on {T.PANEL}", padding=(1, 2))),
            Text(""), T.keyrow("Navigation: ", [("Esc", "close help"), ("q", "quit")]), Text("")]

    def on_key(self, key, app):
        if key == "esc":
            app.pop()
        elif key == "q":
            quit_or_warn(app)


class CommandMenuScreen(Screen):
    """Menu items 2 to 4 hold more than one Makefile target; this picks which one to run."""
    page_arrows = False
    focus_marker = "▶"

    def __init__(self, number, title, targets):
        self.number, self.title, self.targets, self.sel = number, title, targets, 0

    def focus_edge(self):
        return edge_of(self.sel, len(self.targets))

    def render(self, app):
        rows = [T.head(self.title.upper()), Text("")]
        for i, (target, what) in enumerate(self.targets):
            rows.append(menu_card(i + 1, f"make {target}", what, i == self.sel))
        last = len(self.targets)
        return T.header(f"MENU ITEM {self.number}", self.title,
                        "Choose the command to run. Its real output and exit code are shown.") + [
            T.pad(T.pnl(*rows)), Text(""),
            T.keyrow("Navigation: ", [(f"1-{last}", "select"), ("↑ ↓", "move"), ("Enter", "run it"),
                                      ("Esc", "main menu"), ("q", "quit")]), Text("")]

    def on_key(self, key, app):
        if key.isdigit() and 1 <= int(key) <= len(self.targets):
            self.sel = int(key) - 1
            app.push(CommandScreen(self.targets[self.sel][0]))
        elif key == "up":
            self.sel, app.follow = (self.sel - 1) % len(self.targets), True
        elif key == "down":
            self.sel, app.follow = (self.sel + 1) % len(self.targets), True
        elif key == "enter":
            app.push(CommandScreen(self.targets[self.sel][0]))
        elif key == "esc":
            app.pop()
        elif key == "q":
            quit_or_warn(app)


# =========================================================================== running one make target
class CommandScreen(Screen):
    focus_marker = ""

    def __init__(self, target, direct=False):
        self.target, self.direct = target, direct
        self.cmd = CommandRun(target)
        self.shown_result = False

    @property
    def refresh(self):
        return self.cmd.running

    stick_bottom = True   # new output keeps the end of the page in view until you scroll up

    def render(self, app):
        cmd = self.cmd
        if cmd.running:
            pill, style = f"RUNNING · {cmd.elapsed()}", None
        elif cmd.exit_code == 0:
            pill, style = "EXIT CODE 0", T.CHIP_GREEN
        else:
            pill, style = f"EXIT CODE {cmd.exit_code}", T.CHIP_RED
        if self.direct and not cmd.running:
            app.exit_code = cmd.exit_code
        if not cmd.running and not self.shown_result:
            self.shown_result = True
            app.scroll = 10 ** 6   # bring the result and its buttons into view
        body = Text("\n".join(cmd.lines) or "(no output yet)", style="#dbe8ef", overflow="fold")
        right = f"{len(cmd.lines)} lines" if cmd.lines else "waiting for output"
        items = [T.head("COMMAND OUTPUT"), Text(""), T.code_box(f"make {self.target}", right, body)]
        out = T.header("MAKE TARGET", f"make {self.target}",
                       "The command runs exactly as it does outside the dashboard. Its output is shown unchanged.",
                       pill, style) + [T.pad(T.pnl(*items))]
        keys = [("↑ ↓", "scroll the page")]
        if not cmd.running:
            ok = cmd.exit_code == 0
            line = Text.assemble(("●  ", T.GREEN if ok else T.RED),
                                 (f"Finished in {cmd.elapsed()} with exit code {cmd.exit_code}", f"bold {T.GREEN if ok else T.AMBER}"))
            result = [T.head("RESULT"), Text(""), line]
            if self.target in PHASE_OF_TARGET:
                result += [Text(""), T.btnrow(T.btn("View Test Results", "T", T.BTN_PRIMARY), T.btn("Inspect Coverage", "C"))]
            out.append(T.pad(T.pnl(*result) if ok else T.warn_pnl(*result)))
        out += [Text(""), T.keyrow("Navigation: ", keys + [("Esc", "back"), ("q", "quit")]), Text("")]
        return out

    def on_key(self, key, app):
        phase = PHASE_OF_TARGET.get(self.target)
        if key == "t" and phase and not self.cmd.running:
            app.push(JUnitScreen(phase))
        elif key == "c" and phase and not self.cmd.running:
            app.push(CoverageScreen(phase))
        elif key == "esc":
            if self.cmd.running:
                app.message = "The command is still running. Wait for it to finish."
            elif len(app.stack) > 1:
                app.pop()
            else:
                app.replace(MenuScreen())
        elif key == "q":
            if self.cmd.running:
                app.message = "The command is still running. Wait for it to finish."
            else:
                app.quit(self.cmd.exit_code if self.direct else app.exit_code)


# =========================================================================== 02 / 03 Workflow
STEP_CHIP = {"done": ("Done", T.CHIP_GREEN, "●", T.GREEN), "active": ("Active", T.CHIP_AMBER, "◉", T.AMBER),
             "pending": ("Pending", T.CHIP_PLAIN, "○", "#70849a"), "skipped": ("Not run", T.CHIP_PLAIN, "○", "#70849a"),
             "again": ("Runs again", T.CHIP_PLAIN, "○", "#70849a"), "failed": ("Stopped", T.CHIP_RED, "●", T.RED),
             "blocked": ("Not connected", T.CHIP_RED, "●", T.RED)}
# =========================================================================== workflow graph
# The LangGraph nodes of app/main.py (build_graph), laid out top to bottom. Each row is
# (node names shown side by side on the main path, node names of its side branch, note under the row).
GRAPH_ROWS = [
    (["load_source"], [], ""),
    (["ep_agent", "bva_agent"], [], "EP and BVA run in parallel"),
    (["review_ep", "review_bva"], [], "rejected: back to its generator (3 tries, then handed to the human review)"),
    (["ep_done", "bva_done"], [], ""),
    (["merge_tests"], [], "merge failed: back to the generators"),
    (["review_tests"], [], "changes requested: back to the generators · also approves each repair and gap-test proposal"),
    (["run_tests"], ["repair_agent", "apply_code_repair"], "tests failed: Repair Agent proposes a fix, the human review approves it, tests run again"),
    (["check_coverage"], ["generate_gap_tests"], "below 100%: gap-test agent proposes tests, the human review approves them, tests run again"),
    (["save_results"], [], ""),
    (["save_change_log"], [], "original phase saved: continue to refactoring · refactored phase saved: end"),
    (["refactor_agent"], [], "unusable reply: retried"),
    (["review_refactor"], [], "approved: back up to JUnit run, now for the refactored program · changes requested: back to the refactoring agent"),
]
GRAPH_STOP = "escalate_review"   # reached from any step that runs out of tries or is blocked


def workflow_graph(run):
    """The workflow's graph with the node that is running now highlighted. Only what the run reported is marked."""
    waiting = (run.pending or {}).get("node") if run.status == "waiting" else None

    def box_for(node):
        runs = run.node_runs.get(node, 0)
        label = NODE_LABEL.get(node, node)
        if node in run.active and node != waiting:
            mark, color, border, state = "◉", T.AMBER, T.AMBER, "RUNNING NOW"
        elif node == waiting:
            mark, color, border, state = "◉", T.CY, T.FOCUS, "NEEDS YOUR REVIEW"
        elif runs:
            mark, color, border, state = "●", T.GREEN, "#2f6b52", "done" + (f" × {runs}" if runs > 1 else "")
        else:
            mark, color, border, state = "○", "#70849a", T.CLINE, "not reached"
        live = node in run.active or node == waiting
        model = run.model_of(node)
        body = Text.assemble((f"{mark} ", color), (label, f"bold {T.TITLE}" if live or runs else T.MUTED),
                             ("\n  " + state, f"bold {color}" if live else color))
        if model is not None:   # only nodes that call an AI model get a model line
            body.append("\n  AI: " + (model or "shown when the run has loaded"), T.BLUE if live or runs else T.MUTED)
        body.overflow = "fold"   # a long model name wraps inside a narrow box; it is never cut off
        return Panel(body, box=box.HEAVY if live else box.ROUNDED, border_style=border,
                     style=f"on {T.HOVER if live else T.CARD}", padding=(0, 1))

    def side_by_side(nodes):
        grid = Table.grid(expand=True, padding=(0, 1))
        for _ in nodes:
            grid.add_column(ratio=1)
        grid.add_row(*[box_for(node) for node in nodes])
        return grid

    listed = {GRAPH_STOP}
    phase = run.values.get("phase") or "original"
    items = [T.head("WORKFLOW GRAPH"),
             Text.assemble(("The LangGraph nodes in the order they run. ", T.MUTED),
                           ("◉ running now", T.AMBER), ("  ", T.MUTED), ("◉ waiting for you", T.CY), ("  ", T.MUTED),
                           ("● done", T.GREEN), ("  ", T.MUTED), ("○ not reached", "#70849a"),
                           (f"     Phase now: {phase}", f"bold {T.TITLE}"),
                           ("     The page follows the running step.", T.MUTED)), Text("")]
    for index, (main, side, note) in enumerate(GRAPH_ROWS):
        listed.update(main + side)
        row = Table.grid(expand=True, padding=(0, 1))
        row.add_column(ratio=4)
        row.add_column(width=5)
        row.add_column(ratio=5)
        if side:
            row.add_row(side_by_side(main), Text("\n ◀─▶", style=T.MUTED), side_by_side(side))
        else:
            row.add_row(side_by_side(main), Text(""), Text(""))
        items.append(row)
        arrow = "      ▼" if index < len(GRAPH_ROWS) - 1 else "       "
        if note or index < len(GRAPH_ROWS) - 1:
            items.append(Text.assemble((arrow, T.MUTED), ("   ↺ " + note if note else "", T.FOOT)))
    items += [Text(""), Text("  Reached from any step that runs out of tries or is blocked:", style=T.FOOT)]
    stop = Table.grid(expand=True, padding=(0, 1))
    stop.add_column(ratio=4)
    stop.add_column(width=5)
    stop.add_column(ratio=5)
    stop.add_row(box_for(GRAPH_STOP), Text(""), Text(""))
    items.append(stop)
    other = [node for node in list(run.node_runs) + list(run.active) if node not in listed]
    if other:
        items += [Text(""), Text("  Other nodes this run reported:", style=T.FOOT), side_by_side(list(dict.fromkeys(other)))]
    return T.pnl(*items)


TAG_STYLE = {"checkpoint": T.AMBER, "error": T.RED, "done": T.GREEN}


class WorkflowScreen(Screen):
    refresh = True
    back_label = "Main Menu"
    seen = None   # what the graph last showed as running, so the page can follow it

    @property
    def focus_marker(self):
        if self.tab != "graph":
            return ""
        return "NEEDS YOUR REVIEW" if self.waiting else "RUNNING NOW"

    @property
    def stick_bottom(self):
        return self.tab == "detailed"   # new events keep the end of the page in view until you scroll up

    def __init__(self):
        self.tab = "overview"
        self.waiting = False
        self.offset = 0

    def render(self, app):
        run = app.workflow
        pill, style = {
            "starting": ("STARTING", None), "running": (f"RUNNING · {run.elapsed()}", None),
            "waiting": ("WAITING FOR YOUR REVIEW", None), "finished": (f"FINISHED · {run.elapsed()}", T.CHIP_GREEN),
            "failed": ("STOPPED WITH AN ERROR", T.CHIP_RED)}[run.status]
        if run.status == "finished" and run.stopped:
            pill, style = f"STOPPED EARLY · {run.elapsed()}", T.CHIP_RED
        if run.auto:
            pill = "AUTO-APPROVE · " + pill
        out = T.header("STAGE 1–6", "Complete Workflow Dashboard",
                       "Live run monitoring with clear agent activity and real state transitions. Overview is the "
                       "default; Detailed adds available logs and source context.", pill, style)
        out.append(T.stage_strip(max(1, run.step)))
        if run.auto:
            out.append(T.pad(T.warn_pnl(T.amber_note(
                "AUTO-APPROVE TEST RUN (AUTO_APPROVE=1). Every human review is approved automatically and nobody "
                "checks the tests or the Java. Not valid as final evidence."))))
        out.append(T.pad(T.tabs([("overview", "Overview · O"), ("graph", "Graph · G"), ("detailed", "Detailed · D")], self.tab)))
        self.waiting = run.status == "waiting"
        if self.tab == "graph":
            now = (tuple(run.active), run.status)
            if now != self.seen:
                self.seen, app.follow = now, True   # keep the running step in view
            out.append(T.pad(workflow_graph(run)))
            out.append(T.pad(self.active_panel(run)))
            keys = [("O", "overview"), ("G", "graph"), ("D", "detailed"), ("↑ ↓", "scroll the page")]
            if run.status in ("waiting", "finished", "failed"):
                keys.append(("Enter", "open the review" if run.status == "waiting" else "open the results"))
            out += [Text(""), T.keyrow("Navigation: ", keys + [("Esc", "main menu"), ("q", "quit")]), Text("")]
            return out
        live = {"starting": "Starting", "running": "Live", "waiting": "Paused", "finished": "Ended", "failed": "Stopped"}[run.status]
        live = "Stopped" if run.stopped else live
        out.append(T.stat_row([("Stages", "11", T.CY, "Visible workflow steps"),
                               ("Human Review", "HITL", T.AMBER, "2 reviews + any repair or gap proposal"),
                               ("Execution", live, T.TITLE, "No fake checkmarks")]))
        rows = []
        for i, (name, sub) in enumerate(zip(T.STEPS, T.STEP_NOTES), 1):
            if i > 1:
                rows.append(Rule(style="#29384d"))
            label, chip_style, dot, color = STEP_CHIP[run.step_state(i)]
            line = Table.grid(expand=True, padding=(0, 1))
            line.add_column(width=2)
            line.add_column(ratio=1)
            line.add_column(justify="right")
            words = Text.assemble((name + "\n", f"bold {T.TITLE}"), (sub, T.MUTED))
            if i in STEP_AI:   # only steps that call an AI model get a model line
                words.append("\n" + run.model_line(STEP_AI[i])
                             + (f" ({STEP_AI_WHEN[i]})" if i in STEP_AI_WHEN else ""), T.BLUE)
            line.add_row(Text(dot, style=color), words,
                         T.chip(label, chip_style))
            rows.append(line)
        out.append(T.pad(T.pnl(T.head("WORKFLOW PROGRESS"), Text(""), *rows)))
        out.append(T.pad(self.active_panel(run)))
        if self.tab == "detailed":
            log = Text(overflow="fold")
            for n, (clock, tag, text) in enumerate(run.events):
                log.append(f"{clock} ", style="#61738c")
                log.append(f"[{tag}] ", style=TAG_STYLE.get(tag, "#91bdfa"))
                log.append(text + ("" if n == len(run.events) - 1 else "\n"), style="#dbe8ef")
            right = f"Live events from this run · {len(run.events)} events" if run.events else "No events yet"
            out.append(T.pad(T.pnl(T.head("DETAILED EVENT HISTORY"), Text(""),
                                   T.code_box("Recorded event stream", right, log),
                                   Text("Credentials are redacted. The full log is generated_tests/agent_run.log.", style=T.FOOT))))
        keys = [("O", "overview"), ("G", "graph"), ("D", "detailed"), ("↑ ↓", "scroll the page")]
        if run.status in ("waiting", "finished", "failed"):
            keys.append(("Enter", "open the review" if run.status == "waiting" else "open the results"))
        out += [Text(""), T.keyrow("Navigation: ", keys + [("Esc", "main menu"), ("q", "quit")]), Text("")]
        return out

    def active_panel(self, run):
        def panel(title, line1, line2, chip_text, button=None, chip_style=T.CHIP_PLAIN):
            grid = Table.grid(expand=True)
            grid.add_column(ratio=1)
            grid.add_column(justify="right")
            grid.add_row(Text.assemble((line1 + "\n", f"bold {T.TITLE}"), (line2, T.MUTED)), T.chip(chip_text, chip_style))
            items = [T.head(f"ACTIVE COMPONENT — {title}"), Text(""), grid]
            if button:
                items += [Rule(style="#324052"), button]
            return T.pnl(*items, border="#326b7a", bg="#142b3a")

        node = (run.pending or {}).get("node")
        kind = (run.pending or {}).get("review_context")
        if run.status == "waiting" and node == "review_tests" and kind in PROPOSAL:
            return panel(PROPOSAL[kind][0], "Awaiting reviewer decision",
                         "The proposed change has not been written or run. It needs your approval first.",
                         "Human input required", T.btn("Open Proposal Review", "Enter", T.BTN_PRIMARY))
        if run.status == "waiting" and node == "review_tests":
            return panel("Human Test Review", "Awaiting reviewer decision",
                         "Generated tests must be approved before JUnit executes.", "Human input required",
                         T.btn("Open Test Review", "Enter", T.BTN_PRIMARY))
        if run.status == "waiting":
            return panel("Human Refactoring Review", "Awaiting reviewer decision",
                         "Generated Java must be approved before the refactored tests run.", "Human input required",
                         T.btn("Open Refactoring Review", "Enter", T.BTN_PRIMARY))
        if run.status == "finished" and run.stopped:
            why = run.values.get("repair_error") or run.values.get("gap_error") or run.values.get("refactor_error") \
                or run.values.get("merge_error") or "See the event history (press D)."
            return panel("Stopped", f"The workflow stopped early: {run.values.get('workflow_status')}",
                         redact(str(why))[:300], "Stopped", T.btn("Open Final Results", "Enter"), T.CHIP_RED)
        if run.status == "finished":
            return panel("Final Results", f"Workflow ended: {run.values.get('workflow_status', 'finished')}",
                         "Open the results to see what the automated checks found.", "Ended",
                         T.btn("Open Final Results", "Enter", T.BTN_PRIMARY))
        if run.status == "failed":
            return panel("Stopped", "The run stopped with an error", run.error[:300], "Error",
                         T.btn("Open Final Results", "Enter"), T.CHIP_RED)
        names = " + ".join(NODE_LABEL.get(n, n) for n in run.active) or "Starting the workflow"
        return panel(names, "Working · " + run.model_line(run.active) if run.model_line(run.active) else "Working",
                     f"Elapsed {run.elapsed()}. This screen updates when each step finishes.",
                     "Running", chip_style=T.CHIP_AMBER)

    def on_key(self, key, app):
        run = app.workflow
        if key == "o":
            self.tab = "overview"
        elif key == "d":
            self.tab = "detailed"
            app.at_bottom = False   # stay where the reader is; scrolling to the end follows new events
        elif key == "g":
            self.tab, self.seen = "graph", None
        elif key == "enter":
            node = (run.pending or {}).get("node")
            if run.status == "waiting" and node == "review_tests" and run.pending.get("review_context") in PROPOSAL:
                app.push(ProposalReviewScreen(app))
            elif run.status == "waiting" and node == "review_tests":
                app.push(TestReviewScreen(app))
            elif run.status == "waiting":
                app.push(RefactorReviewScreen(app))
            elif run.status in ("finished", "failed"):
                app.push(ResultsScreen())
        elif key == "esc":
            app.home()
        elif key == "q":
            quit_or_warn(app)


# =========================================================================== 04 Test Review
DEFINITIONS = [
    ("EP", T.BLUE, "Equivalence Partitioning. Inputs are split into classes that behave the same way, and one "
                   "representative value from the middle of each class is tested."),
    ("BVA", T.PURPLE, "Boundary Value Analysis. Each numeric comparison against N is tested at N-1, N and N+1, "
                      "and each range at its minimum, maximum and just outside them."),
]


class TestReviewScreen(Screen):
    page_arrows = False
    def __init__(self, app):
        run = app.workflow
        self.payload = run.pending
        methods = data.public_methods(run.values.get("source_code", ""), run.values.get("class_name", "SeasonSwitch"))
        self.tests = data.parse_tests(run.values.get("merged_tests", ""), methods)
        self.groups = data.group_tests(self.tests, methods)
        self.changed = data.changed_tests(app.previous_tests, self.tests) if app.previous_tests else {}
        self.gi = self.ti = 0
        self.marks = {}          # test name -> comment
        self.open = set()        # test names whose source is shown
        self.defs_open = False

    def current(self):
        return self.groups[self.gi][1][self.ti]

    def focus_edge(self):
        return edge_of(self.ti, len(self.groups[self.gi][1])) if self.tests else None

    def render(self, app):
        out = T.header("HUMAN REVIEW #1", "Generated JUnit Test Review",
                       "Review expected outcomes and exact assertions before executing the merged JUnit suite.",
                       "AWAITING TEST APPROVAL")
        out.append(T.stage_strip(4))
        for name, note in (self.payload.get("ai_review_notes") or {}).items():
            out.append(T.pad(T.warn_pnl(
                T.head(f"WARNING · THE AI REVIEWER REJECTED THE {name} TESTS 3 TIMES"), Text(""),
                Text(f"The {name} tests were passed to you without the AI reviewer's approval. Check these points "
                     "before you approve:", style=T.BODY),
                Text(redact(note), style=T.SOFT, overflow="fold"))))
        top = Table.grid(expand=True)
        top.add_column(ratio=1)
        top.add_column(justify="right")
        top.add_row(Text.assemble(("Grouped by Java method · ", T.MUTED), ("EP blue", T.BLUE), (" · ", T.MUTED), ("BVA purple", T.PURPLE)),
                    T.chip("Approval required"))
        out.append(T.pad(top))
        defs = [Text.assemble(("Understanding Test Types (", f"bold {T.TITLE}"), ("EP", f"bold {T.BLUE}"), (" & ", f"bold {T.TITLE}"),
                              ("BVA", f"bold {T.PURPLE}"), (")", f"bold {T.TITLE}")), Text(""),
                T.expander(("Hide" if self.defs_open else "Expand") + " test-type definitions"
                           + ("" if self.defs_open else " (closed by default)") + " · press T", self.defs_open)]
        if self.defs_open:
            for name, color, text in DEFINITIONS:
                defs.append(Text.assemble((f"{name}  ", f"bold {color}"), (text, T.SOFT)))
        out.append(T.pad(T.pnl(*defs)))
        if not self.tests:
            out.append(T.pad(T.warn_pnl(T.head("NO TESTS FOUND"), Text(""),
                                        Text("The merged test file has no @Test methods to review.", style=T.SOFT))))
        else:
            chips, line, width = [], Text(), 0
            for i, (method, members) in enumerate(self.groups):
                kinds = sorted({t["kind"] for t in members})
                label = f"{method}() · {len(members)} {' + '.join(kinds)} tests"
                piece = (Text.assemble((f" ▶ {label} ", T.SELECTED)) if i == self.gi
                         else Text.assemble((f" {label} ", "#afc0d6 on #16283a")))
                if width + len(piece) + 1 > app.width - 12 and width:
                    chips += [line, Text("")]
                    line, width = Text(), 0
                line.append_text(piece)
                line.append(" ")
                width += len(piece) + 1
            chips.append(line)
            out.append(T.pad(T.pnl(Text.assemble(("TEST GROUPS", f"bold {T.TITLE}"),
                                                 (f"   group {self.gi + 1} of {len(self.groups)}", T.MUTED)), Text(""), *chips)))
            method, members = self.groups[self.gi]
            cards = [T.head(f"GENERATED TESTS — {method}()"), Text("")]
            for i, test in enumerate(members):
                cards.append(self.card(test, i == self.ti, f"test {i + 1} of {len(members)}", app))
            out.append(T.pad(T.pnl(*cards)))
        buttons = T.btnrow(T.btn("Approve All", "A", T.BTN_PRIMARY), T.btn("Preview Revision Batch", "R", T.BTN_AMBER),
                           T.btn("Reject", "X", T.BTN_RED))
        decision = [T.head("HUMAN DECISION"), Text(""), buttons, Text("")]
        marked = len(self.marks)
        if marked:
            decision.append(Text(f"{marked} test{'s' if marked != 1 else ''} marked for changes.", style=f"bold {T.AMBER}"))
        if self.payload.get("prior_feedback"):
            decision.append(Text("Your previous feedback: " + self.payload["prior_feedback"][:400], style=T.SOFT))
        decision.append(Text("No partial approval. Revised EP/BVA requests return to their generation agents and back "
                             "to human review.", style=T.FOOT))
        out.append(T.pad(T.pnl(*decision)))
        out += [Text(""),
                T.keyrow("Navigation: ", [("← →", "change group"), ("↑ ↓", "change test"), ("Esc", "back")]),
                T.keyrow("This test:  ", [("Enter", "inspect this test"), ("Space", "mark this test for changes")]),
                T.keyrow("Decide:     ", [("A", "approve all tests"), ("R", "preview revision batch"), ("X", "reject")])]
        return out

    def card(self, test, focus, position, app):
        badge = T.kind_badge(test["kind"])
        name = test["name"]
        if name in self.marks:
            status = T.chip("Changes requested", T.CHIP_AMBER)
        elif name in self.changed:
            status = T.chip("Revised since last review" if self.changed[name] == "revised" else "New since last review", T.CHIP_GREEN)
        else:
            status = T.chip("Pending review")
        top = Table.grid(expand=True)
        top.add_column(ratio=1)
        top.add_column(justify="right")
        top.add_row(Text.assemble(("▶ " if focus else "  ", f"bold {T.CY}"), badge, ("  " + name, f"bold {T.TITLE}")), status)
        items = [top, Text("  " + (test["comment"] or "The generator wrote no comment for this test."), style=T.MUTED)]
        is_open = name in self.open
        items.append(T.expander("Inspect actual test setup, action, and assertions", is_open))
        if is_open:
            items.append(T.code_box(f"{name}()", f"merged test file, line {test['line']}",
                                    Text(test["source"].expandtabs(4), style="#dbe8ef")))
        if name in self.marks:
            items.append(Text.assemble(("  ☑ ", T.AMBER), ("Request changes to this test: ", T.INTRO),
                                       (self.marks[name] or "(no comment)", T.BODY)))
        else:
            items.append(Text.assemble(("  ☐ ", T.INTRO), ("Request changes to this test", T.INTRO)))
        return T.select_card(items, focus, position)

    def on_key(self, key, app):
        run = app.workflow
        if key == "esc":
            app.pop()
            return
        if key == "t":
            self.defs_open = not self.defs_open
        elif key == "x":
            reason = app.ask_text("Reject the whole suite: what must change? (required)")
            if reason:
                app.previous_tests = self.tests
                run.answer({"approved": False, "feedback": reason})
                app.pop()
            elif reason == "":
                app.message = "A reason is required to reject. Nothing was sent."
        elif key == "a":
            if self.marks and not getattr(self, "approve_armed", False):
                self.approve_armed = True
                app.message = (f"You marked {len(self.marks)} test(s) for changes. Press A again to approve everything "
                               "anyway, or R to preview the revision batch.")
                return
            app.previous_tests = []
            run.answer({"approved": True, "feedback": ""})
            app.pop()
        elif key == "r":
            if self.marks:
                app.push(RevisionBatchScreen(self))
            else:
                app.message = "No tests are marked yet. Press Space on a test to mark it for changes."
        elif self.tests:
            self.move(key, app)
        self.approve_armed = False

    def move(self, key, app):
        members = self.groups[self.gi][1]
        if key == "left":
            self.gi, self.ti = (self.gi - 1) % len(self.groups), 0
        elif key == "right":
            self.gi, self.ti = (self.gi + 1) % len(self.groups), 0
        elif key == "up":
            self.ti = (self.ti - 1) % len(members)
        elif key == "down":
            self.ti = (self.ti + 1) % len(members)
        elif key == "enter":
            self.open ^= {self.current()["name"]}
        elif key == "space":
            name = self.current()["name"]
            if name in self.marks:
                del self.marks[name]
            else:
                note = app.ask_text(f"What should change in {name}? (Enter with no text marks it without a comment)")
                if note is not None:
                    self.marks[name] = note
        else:
            return
        app.follow = True


# =========================================================================== repair / gap proposal review
PROPOSAL = {  # review_context -> (title, what it is)
    "repair": ("Proposed Repair Review", "The repair agent proposes this change because a test run failed."),
    "gap": ("Coverage-Gap Test Review", "The gap-test agent proposes these new tests for branches JaCoCo reported as missed."),
}
CODE_STYLE = {"plain": ("#61738c", "#dbe8ef"), "add": ("#61738c on #12281f", "#91ebbe on #12281f"),
              "del": ("#61738c on #2a1620", "#f3a3ad on #2a1620"), "file": ("#e8d091", "#e8d091"), "hunk": ("#91bdfa", "#91bdfa")}


class ProposalReviewScreen(Screen):
    """The same human review step (review_tests), when it asks about a repair or gap-test proposal."""
    focus_marker = ""

    def __init__(self, app):
        run = app.workflow
        self.payload = run.pending
        self.kind = self.payload.get("review_context")
        self.phase = run.values.get("phase") or "original"
        proposals = [row for row in run.values.get("repair_log") or []
                     if row.get("kind") == self.kind and row.get("outcome") == "proposed"]
        self.row = proposals[-1] if proposals else {}

    def render(self, app):
        title, what = PROPOSAL[self.kind]
        row, payload = self.row, self.payload
        out = T.header("HUMAN REVIEW · PROPOSED CHANGE", title,
                       "Nothing has been written or run yet. Read the change, then approve or reject it.",
                       "AWAITING HUMAN APPROVAL")
        out.append(T.stage_strip(max(1, app.workflow.step)))
        target = payload.get("proposed_target") or "the merged JUnit tests"
        is_code = row.get("target") == "code"
        facts = [T.head("WHAT IS PROPOSED"), Text(""), Text(what, style=T.BODY), Text(""),
                 Text.assemble(("Changes: ", f"bold {T.TITLE}"), (str(target), T.BODY),
                               ("  (production Java code)" if is_code else "  (tests only)", T.AMBER if is_code else T.SOFT)),
                 Text.assemble(("Phase: ", f"bold {T.TITLE}"), (self.phase, T.BODY),
                               (f"   Try {row['attempt']} of 3" if row.get("attempt") else "", T.SOFT))]
        if row.get("diagnosis"):
            facts.append(Text.assemble(("Reason given by the AI: ", f"bold {T.TITLE}"), (redact(row["diagnosis"]), T.SOFT),
                                       overflow="fold"))
        if row.get("tests"):
            label = "New tests: " if self.kind == "gap" else "Failing tests: "
            facts.append(Text.assemble((label, f"bold {T.TITLE}"), (", ".join(str(t) for t in row["tests"]), T.SOFT),
                                       overflow="fold"))
        if is_code:
            facts += [Text(""), T.amber_note("This changes the program itself, not the tests. Approve only if the test "
                                             "is right and the code is wrong.")]
        out.append(T.pad(T.pnl(*facts)))

        lines = data.diff_lines(payload.get("proposed_diff"))
        code = Text()
        for n, (number, text, style) in enumerate(lines):
            gutter, body = CODE_STYLE[style]
            code.append(f" {number:>4}  ", style=gutter)
            code.append(text[:app.width - 22].ljust(app.width - 22) if style in ("add", "del") else text[:app.width - 22], style=body)
            if n < len(lines) - 1:
                code.append("\n")
        added = sum(1 for _, _, style in lines if style == "add")
        removed = sum(1 for _, _, style in lines if style == "del")
        if lines:
            viewer = T.code_box(str(target), f"PROPOSED DIFF · {added} lines added, {removed} removed", code)
        else:
            viewer = T.amber_note("The workflow sent no diff for this proposal.")
        out.append(T.pad(T.pnl(T.head("PROPOSED CHANGE"),
                               Text("Green lines are added, red lines are removed. This is the exact change that will be "
                                    "written if you approve.", style=T.MUTED), viewer)))
        after = ("the code fix is written, then the tests run again" if is_code else "the tests run again with this change")
        review = [T.head("YOUR DECISION"), Text(""),
                  T.btnrow(T.btn("Approve This Change", "A", T.BTN_PRIMARY), T.btn("Reject", "X", T.BTN_RED)), Text("")]
        if payload.get("prior_feedback"):
            review.append(Text("Your previous feedback: " + payload["prior_feedback"][:400], style=T.SOFT))
        review.append(Text(f"Approve: {after}. Reject: nothing is written, your reason goes back to the agent, "
                           "and it may propose again (3 tries per phase).", style=T.FOOT))
        out.append(T.pad(T.pnl(*review)))
        out += [T.keyrow("Navigation: ", [("↑ ↓", "scroll the page"), ("Esc", "back")]),
                T.keyrow("Decide:     ", [("A", "approve this change"), ("X", "reject with a reason")])]
        return out

    def on_key(self, key, app):
        run = app.workflow
        if key == "esc":
            app.pop()
        elif key == "a":
            run.answer({"approved": True, "feedback": ""})
            app.pop()
        elif key == "x":
            reason = app.ask_text("Reject this proposal: what is wrong with it? (required)")
            if reason:
                run.answer({"approved": False, "feedback": reason})
                app.pop()
            elif reason == "":
                app.message = "A reason is required to reject. Nothing was sent."


# =========================================================================== 05 Revision Batch
class RevisionBatchScreen(Screen):
    """Shows every flagged item with its feedback before anything is sent. Used for tests and for Java files."""
    back_label = ""   # this page has its own "Return to ..." button
    page_arrows = False

    def __init__(self, review, files=False):
        self.review, self.files, self.sel = review, files, 0
        self.open = set()

    def items(self):
        if self.files:
            return [(name, None, note, self.review.files[name]) for name, note in self.review.notes.items()]
        by_name = {t["name"]: t for t in self.review.tests}
        return [(name, by_name[name]["kind"], note, by_name[name]["source"]) for name, note in self.review.marks.items()]

    def focus_edge(self):
        return edge_of(self.sel, len(self.items()))

    def render(self, app):
        items = self.items()
        noun = "file" if self.files else "test"
        if self.files:
            out = T.header("HUMAN REVIEW #2 · REVISIONS", "Batch Revision Preview",
                           "Review every flagged Java file and its notes together before sending revisions to the "
                           "refactoring agent.", "NOT SUBMITTED")
            out.append(T.stage_strip(9))
        else:
            out = T.header("HUMAN REVIEW #1 · REVISIONS", "Batch Revision Preview",
                           "Review every flagged test and its individual feedback together before sending revisions "
                           "to the appropriate EP/BVA agent.", "NOT SUBMITTED")
            out.append(T.stage_strip(4))
        cards = [T.head(f"SELECTED {noun.upper()}S · {len(items)}"), Text("")]
        for i, (name, kind, note, source) in enumerate(items):
            focus = i == self.sel
            lead = [("▶ " if focus else "  ", f"bold {T.CY}")]
            if kind:
                lead.append(T.kind_badge(kind))
            body = [Text.assemble(*lead, ("  " + name, f"bold {T.TITLE}")), Rule(style="#324052"),
                    Text("  Reviewer feedback", style="bold #aabbd0"),
                    Text("  " + (note or "(marked for changes, no comment)"), style=T.BODY),
                    T.expander("View full original test source" if not self.files else "View the generated Java file",
                               name in self.open)]
            if name in self.open:
                body.append(T.code_box(name, "as generated", Text(source.expandtabs(4), style="#dbe8ef")))
            cards.append(T.select_card(body, focus, f"{noun} {i + 1} of {len(items)}"))
            cards.append(Text(""))
        out.append(T.pad(T.pnl(*cards[:-1])))
        if self.files:
            steps = [("Join the per-file notes into one request, labeled by file name", "The review step keeps its single comment"),
                     ("Send the request to the refactoring agent", "It regenerates the Java and the adapted tests"),
                     ("Return to Human Review #2", "Refactored tests do not run until the refactoring is approved")]
        else:
            steps = [("Route EP feedback to EP generation/revision agent", "Told to change only the flagged tests"),
                     ("Route BVA feedback to BVA generation/revision agent", "Told to change only the flagged tests"),
                     ("AI review, merge & deduplicate", "Same checks as the first round"),
                     ("Compare old and new tests", "Changed tests are labeled when the review reopens"),
                     ("Return to Human Test Review", "Still no JUnit execution until entire suite approved")]
        rows = []
        for i, (name, sub) in enumerate(steps):
            if i:
                rows.append(Rule(style="#29384d"))
            line = Table.grid(expand=True, padding=(0, 1))
            line.add_column(width=2)
            line.add_column(ratio=1)
            line.add_column(justify="right")
            line.add_row(Text("○", style="#70849a"), Text.assemble((name + "\n", f"bold {T.TITLE}"), (sub, T.MUTED)), T.chip("Pending"))
            rows.append(line)
        out.append(T.pad(T.pnl(T.head("WHAT HAPPENS AFTER SUBMISSION"), Text(""), *rows)))
        back = "Return to Refactoring Review" if self.files else "Return to Test Review"
        out.append(T.pad(T.pnl(T.head("CONFIRM REVISION BATCH"), Text(""),
                               T.amber_note("Nothing is sent to an AI agent and no files change until you press S."), Text(""),
                               T.btnrow(T.btn("Send Revisions to AI", "S", T.BTN_PRIMARY), T.btn(back, "Esc")))))
        out += [Text(""), T.keyrow("Navigation: ", [("↑ ↓", f"change {noun}")]),
                T.keyrow(f"This {noun}:  ", [("Enter", f"view source of this {noun}"), ("E", f"edit feedback for this {noun}")]), Text("")]
        return out

    def on_key(self, key, app):
        items = self.items()
        name = items[self.sel][0]
        store = self.review.notes if self.files else self.review.marks
        if key == "esc":
            app.pop()
        elif key == "up":
            self.sel = (self.sel - 1) % len(items)
            app.follow = True
        elif key == "down":
            self.sel = (self.sel + 1) % len(items)
            app.follow = True
        elif key == "enter":
            self.open ^= {name}
        elif key == "e":
            note = app.ask_text(f"Feedback for {name}", store[name])
            if note is not None:
                store[name] = note
        elif key == "s":
            self.review.send(app)
            app.pop()
            app.pop()


TestReviewScreen.send = lambda self, app: (
    setattr(app, "previous_tests", self.tests),
    app.workflow.answer({"approved": False, "feedback": "", "test_feedback": dict(self.marks)}))


# =========================================================================== 06 / 10 JUnit
class JUnitScreen(Screen):
    def __init__(self, phase):
        self.phase = phase
        self.report = data.junit_report(phase)
        self.sel = 0
        self.open = {0}
        self.passing_open = False
        self.tab = "overview"
        test_file = self.report.get("report_files") and data.java_tools.java_project_dir(phase) / "src" / "test" / "java" / "cse4392"
        self.tests = {}
        if test_file and test_file.is_dir():
            methods = data.public_methods(data.read(data.ORIGINAL_SOURCE))
            for path in test_file.glob("*.java"):
                for test in data.parse_tests(data.read(path), methods):
                    self.tests[test["name"]] = test

    def focus_edge(self):
        return edge_of(self.sel, len(self.report.get("failures") or []))

    @property
    def page_arrows(self):
        return not self.report.get("failures")   # with failures, ↑ ↓ choose the failed test

    def render(self, app):
        r, original = self.report, self.phase == "original"
        pill = "REPORT ON DISK" if r["reports_found"] else "NO REPORT FOUND"
        if original:
            out = T.header("PHASE 1 · JUNIT EXECUTION", "Original JUnit Testing & Repair",
                           "Failure groups expand automatically. Passed tests remain collapsed until requested.", pill)
        else:
            out = T.header("STAGE 6 · REFACTORED VERIFICATION", "Refactored JUnit Testing",
                           "Keep original and refactored results separate. Tests can pass while coverage is incomplete.", pill)
        out.append(T.stage_strip(5 if original else 10, in_run=bool(app.workflow)))
        if not r["reports_found"]:
            target = "make test-original" if original else "make test-refactored"
            out.append(T.pad(T.warn_pnl(T.head("NO JUNIT REPORT"), Text(""),
                                        Text(f"No Surefire report exists for the {self.phase} project yet. Run {target} "
                                             "or the complete workflow first.", style=T.SOFT))))
            out += [Text(""), T.keyrow("Navigation: ", [("Esc", "back"), ("q", "quit")]), Text("")]
            return out
        out.append(T.pad(T.tabs([("overview", "Overview · O"), ("detailed", "Detailed · D")], self.tab)))
        bad = r["failed"] + r["errors"]
        out.append(T.stat_row([("Executed", r["total"], T.TITLE), ("Passed", r["passed"], T.GREEN),
                               ("Failed", bad, T.RED if bad else T.TITLE)]))
        failures = r["failures"]
        if failures:
            cards = [T.head("FAILED TESTS · AUTO-EXPANDED"), Text("")]
            for i, failure in enumerate(failures):
                cards.append(self.failure_card(failure, i, len(failures), app))
                cards.append(Text(""))
            out.append(T.pad(T.pnl(*cards[:-1])))
        else:
            line = Table.grid(expand=True, padding=(0, 1))
            line.add_column(width=2)
            line.add_column(ratio=1)
            line.add_row(Text("●", style=T.GREEN),
                         Text.assemble((f"All {r['total']} JUnit tests passed\n", f"bold {T.GREEN}"),
                                       ("Passing groups collapsed by default; expand to inspect specific tests.", T.MUTED)))
            out.append(T.pad(T.pnl(T.head("TEST EXECUTION"), Text(""), line)))
        passed = [t["test"].split(".")[-1] for t in r["tests"] if t["status"] == "passed"]
        label = (f"{len(passed)} passed · " + ("Hide" if self.passing_open else "Expand to see") + " test names · press P")
        items = [T.head("PASSING TESTS"), Text(""), T.expander(label, self.passing_open)]
        if self.passing_open:
            names = Table.grid(expand=True, padding=(0, 2))
            names.add_column(ratio=1)
            names.add_column(ratio=1)
            for i in range(0, len(passed), 2):
                names.add_row(Text("✓ " + passed[i], style=T.SOFT), Text("✓ " + passed[i + 1], style=T.SOFT) if i + 1 < len(passed) else "")
            items.append(names)
        out.append(T.pad(T.pnl(*items)))
        if self.tab == "detailed":
            out.append(T.pad(T.pnl(T.head("REPORT DETAILS"), Text(""),
                                   Text.assemble(("Source: ", T.MUTED), (r["source_note"] + "\n", T.BODY),
                                                 ("Files: ", T.MUTED), (", ".join(p.split("/")[-1] for p in r["report_files"]) + "\n", T.BODY),
                                                 ("Skipped: ", T.MUTED), (f"{r['skipped']}\n", T.BODY),
                                                 ("Test time: ", T.MUTED), (f"{r['time_s']} s", T.BODY)))))
        if not original:
            out.append(T.pad(self.coverage_gate(app)))
        out.append(T.pad(self.repair_panel(app, original)))
        other = "Refactored" if original else "Original"
        out.append(T.note_line(r["source_note"] + f".   Press J to view the {other} JUnit results."))
        out.append(Text(""))
        nav = [("↑ ↓", "change failed test")] if failures else []
        out.append(T.keyrow("Navigation: ", nav + [("O", "overview"), ("D", "detailed"), ("Esc", "back")]))
        if failures:
            out.append(T.keyrow("This test:  ", [("Enter", "show or hide details of this test")]))
        out.append(Text(""))
        return out

    def failure_card(self, failure, i, count, app):
        focus = i == self.sel
        test = self.tests.get(failure["name"].split("(")[0])
        top = Table.grid(expand=True)
        top.add_column(ratio=1)
        top.add_column(justify="right")
        top.add_row(Text.assemble(("▶ " if focus else "  ", f"bold {T.CY}"), (failure["name"] + "()", f"bold {T.RED}")),
                    T.chip("Failed" if failure["kind"] == "failure" else "Error", T.CHIP_RED))
        method = f"SeasonSwitch.{test['method']}()" if test and test["method"] != "other" else "not identified from the test"
        items = [top, Text.assemble(("  Affected Java method: ", T.BODY), (method, T.BLUE)),
                 Text("  " + (failure["message"] or failure["type"] or "No message in the report")[:300], style=T.MUTED)]
        if i in self.open:
            detail = [Text.assemble(("▼ ", T.INTRO), ("Exception, original code, and assertion details", f"bold {T.TITLE}")), Text(""),
                      Text((failure["type"] + "\n" if failure["type"] else "")
                           + "\n".join(failure["details"].splitlines()[:8]), style="#dbe8ef")]
            if test:
                detail += [Text(""), Text(test["source"].expandtabs(4), style="#dbe8ef")]
            items.append(Panel(Group(*detail), box=box.ROUNDED, border_style=T.CLINE, style="on #16263a", padding=(0, 1)))
        return T.select_card(items, focus, f"failed test {i + 1} of {count}")

    def coverage_gate(self, app):
        cov = data.coverage_report(self.phase)
        if not cov["found"]:
            return T.warn_pnl(T.head("COVERAGE"), Text(""), Text("No JaCoCo report found for this phase.", style=T.SOFT))
        full, scoped = cov["full"], cov["scoped"]
        done = full["missed"] == 0
        items = [T.head("COVERAGE GATE MET" if done else "COVERAGE GATE STILL OPEN"), Text(""),
                 Text(f"{full['percent']:.2f}%", style=f"bold {T.GREEN if done else T.AMBER}"),
                 Text(f"Full program: {full['covered']}/{full['total']}" + ("" if cov["same_scope"] else
                      f" · Configured scope: {scoped['covered']}/{scoped['total']} ({scoped['percent']:.2f}%)"), style=T.SOFT),
                 T.bar(full["covered"] / full["total"] if full["total"] else 0, app.width - 14), Text("")]
        if not done:
            inside = "" if cov["same_scope"] else f" ({scoped['missed']} in the configured scope)"
            items += [T.amber_note(f"{full['missed']} full-program branches remain uncovered{inside}. "
                                   "A passing JUnit suite is NOT completion."), Text("")]
        items.append(T.btnrow(T.btn("Inspect Refactored Coverage", "C", T.BTN_PRIMARY)))
        return T.pnl(*items) if done else T.warn_pnl(*items)

    def repair_panel(self, app, original):
        """The repair agent's own record (state key repair_log, also saved in the change log)."""
        title = "AUTOMATED FAILURE ANALYSIS & REPAIR" if original else "AUTOMATED FAILURE REPAIR"
        items = [T.head(title), Text("")] + agent_record("repair", self.phase, app)
        if original:
            items += [Rule(style="#5a4a2c"), T.btn("Coverage Dashboard", "C")]
        return T.warn_pnl(*items)

    def on_key(self, key, app):
        failures = self.report.get("failures") or []
        if key == "esc":
            app.pop()
        elif key == "q":
            quit_or_warn(app)
        elif key == "o":
            self.tab = "overview"
        elif key == "d":
            self.tab = "detailed"
        elif key == "p":
            self.passing_open = not self.passing_open
        elif key == "c":
            app.push(CoverageScreen(self.phase))
        elif key == "j":
            app.replace(JUnitScreen("refactored" if self.phase == "original" else "original"))
        elif failures and key in ("up", "down"):
            self.sel = (self.sel + (1 if key == "down" else -1)) % len(failures)
            app.follow = True
        elif failures and key == "enter":
            self.open ^= {self.sel}


# =========================================================================== 07 / 08 Coverage
class CoverageScreen(Screen):
    focus_marker = ""

    def __init__(self, phase):
        self.phase = phase
        self.cov = data.coverage_report(phase)

    def render(self, app):
        cov, original = self.cov, self.phase == "original"
        name = "Original" if original else "Refactored"
        out = T.header(f"STAGE {4 if original else 6} · JACOCO BRANCH COVERAGE", f"Coverage — {name} Java",
                       "Full-program branch coverage is always primary. Any narrower configured scope appears underneath.",
                       "REPORT ON DISK" if cov["found"] else "NO REPORT FOUND")
        out.append(T.stage_strip(6 if original else 10, in_run=bool(app.workflow)))
        other_key, other = ("R", "View Refactored Coverage") if original else ("O", "View Original Coverage")
        if not cov["found"]:
            out.append(T.pad(T.warn_pnl(T.head("NO JACOCO REPORT"), Text(""),
                                        Text(f"No JaCoCo XML exists for the {self.phase} project yet. Run "
                                             f"make test-{self.phase} or the complete workflow first.", style=T.SOFT), Text(""),
                                        T.btnrow(T.btn(other, other_key), T.btn("Final Results", "F")))))
            out += [Text(""), T.keyrow("Navigation: ", [("Esc", "back"), ("q", "quit")]), Text("")]
            return out
        full, scoped, width = cov["full"], cov["scoped"], app.width - 14
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        grid.add_column(justify="right")
        grid.add_row(Text.assemble((f"Entire {self.phase} program\n", "#aabbd0"),
                                   (f"{full['percent']:.2f}%", f"bold {T.GREEN if not full['missed'] else T.AMBER}")),
                     Text.assemble((f"{full['covered']} / {full['total']}\n", f"bold {T.TITLE}"),
                                   (f"{full['missed']} missed", T.RED if full["missed"] else T.GREEN), justify="right"))
        out.append(T.pad(T.pnl(T.head("FULL-PROGRAM BRANCH COVERAGE"), Text(""), grid, Text(""),
                               T.bar(full["covered"] / full["total"] if full["total"] else 0, width),
                               Text("Goal: 100%", style=T.MUTED))))
        grid2 = Table.grid(expand=True)
        grid2.add_column(ratio=1)
        grid2.add_column(justify="right")
        tail = f"{scoped['covered']} / {scoped['total']} covered" + (f" · {scoped['missed']} missed" if scoped["missed"] else "")
        grid2.add_row(Text(f"{scoped['percent']:.2f}%", style=f"bold {T.GREEN if not scoped['missed'] else T.AMBER}"),
                      Text(tail, style=T.MUTED))
        outside = [data.java_label(m["class"], m["method"]) for m in cov["missed"] if not m["in_scope"]]
        scope_items = [T.head("CONFIGURED SCOPE — SECONDARY"), Text(""), grid2, Text(""),
                       T.bar(scoped["covered"] / scoped["total"] if scoped["total"] else 0, width), Text("")]
        if scoped["missed"]:
            scope_items.append(T.amber_note("Selected-scope result is incomplete. It cannot be reported as full-program success."))
        elif outside:
            scope_items.append(T.amber_note(f"Selected scope leaves out {full['total'] - scoped['total']} branches "
                                            f"({', '.join(outside)}). This is not full-program coverage."))
        else:
            scope_items.append(Text("The configured scope and the full program agree.", style=T.GREEN))
        if cov["scope"]["include_classes"]:
            classes = ("only the class " + ", ".join(cov["scope"]["include_classes"])
                       + " is measured, so inner classes such as Room are left out")
        else:
            classes = "every class is measured"
        excluded = ", ".join(m + "()" for m in cov["scope"]["exclude_methods"]) or "none"
        scope_items.append(Text(f"Scope used by the workflow: {classes}. Methods excluded by name: {excluded}.", style=T.FOOT))
        if cov["same_scope"]:
            out.append(T.pad(T.pnl(T.head("MEASURED SCOPE"), Text(""),
                                   Text("The workflow measures the full program: every class and main(), with no method "
                                        "excluded. There is no separate narrower number.", style=T.SOFT))))
        else:
            out.append(T.pad(T.pnl(*scope_items)))
        table = Table(box=box.SIMPLE_HEAD, expand=True, border_style="#304055", header_style="bold #a3b5c8",
                      padding=(0, 1), show_edge=False)
        table.add_column("JAVA METHOD", ratio=5)
        table.add_column("MISSED", ratio=1)
        table.add_column("SOURCE LINES", ratio=2)
        if not cov["same_scope"]:
            table.add_column("IN CONFIGURED SCOPE", ratio=3)
        for m in cov["missed"]:
            cells = [Text(data.java_label(m["class"], m["method"]), style=T.BODY), Text(str(m["missed"]), style=T.RED),
                     Text(", ".join(str(n) for n in m["lines"]), style=T.SOFT)]
            if not cov["same_scope"]:
                cells.append(Text("yes" if m["in_scope"] else "no, excluded", style=T.BODY if m["in_scope"] else T.AMBER))
            table.add_row(*cells)
        if cov["missed"]:
            out.append(T.pad(T.pnl(T.head("UNCOVERED FULL-PROGRAM BRANCHES"), Text(""), table, Text(""),
                                   Text(cov["source_note"] + ". Read from the JaCoCo XML; no filter was changed.", style=T.FOOT))))
        else:
            out.append(T.pad(T.pnl(T.head("UNCOVERED FULL-PROGRAM BRANCHES"), Text(""),
                                   Text("None. Every branch in the program is covered.", style=f"bold {T.GREEN}"),
                                   Text(cov["source_note"] + ".", style=T.FOOT))))
        gap = [T.head("COVERAGE-GAP TEST GENERATION"), Text("")] + agent_record("gap", self.phase, app)
        gap += [Rule(style="#5a4a2c"), T.btnrow(T.btn(other, other_key), T.btn("Final Results", "F"))]
        out.append(T.pad(T.warn_pnl(*gap) if full["missed"] else T.pnl(*gap)))
        out += [Text(""), T.keyrow("Navigation: ", [("Esc", "back"), ("q", "quit")]), Text("")]
        return out

    def on_key(self, key, app):
        if key == "esc":
            app.pop()
        elif key == "q":
            quit_or_warn(app)
        elif key == "r" and self.phase == "original":
            app.replace(CoverageScreen("refactored"))
        elif key == "o" and self.phase == "refactored":
            app.replace(CoverageScreen("original"))
        elif key == "f":
            app.replace(ResultsScreen())


# =========================================================================== 09 Refactoring review
ROOM = "roomTick()"
GUIDE = {
    "SeasonSwitch.java": ("Context class", "The switch statements on the mode are replaced by delegation to the current State object.",
                          "cool(), heat(), off(), timerOff() and the Room timer hand their work to the current State.",
                          "The public API, package, thresholds, devices, timers and messages behave as in the original program.",
                          [("cool() / heat() / off()", "Each one delegates to the current State and does nothing else."),
                           ("timerOff()", "Delegates to the current State. actionPerformed() still calls timerOff()."),
                           ("Room.actionPerformed()", "Delegates the room temperature step to the current State."),
                           ("No mode switch left", "No switch statement and no if/else chain on the mode remains anywhere."),
                           ("OFF, COOL, HEAT", "The constants are State objects and the state starts as OFF."),
                           ("main()", "Arguments, printed messages and exit codes are unchanged.")]),
    "State.java": ("Shared interface", "Every concrete State class needs to support the same operations.",
                   "Introduce a common contract used by OFF, COOL, and HEAT.",
                   "Every class implements the interface methods with correct Java signatures.",
                   [("cool()", "OffState: AC on and switch to COOL. CoolState: no-op. HeatState: heater off, AC on, switch to COOL."),
                    ("heat()", "OffState: heater on and switch to HEAT. CoolState: AC off, heater on, switch to HEAT. HeatState: no-op."),
                    ("off()", "OffState: no-op. CoolState: AC off and timer stopped. HeatState: heater off and timer stopped."),
                    ("timerOff()", "OffState: no-op. CoolState: AC on only if room.temp > coolTemp. HeatState: heater on only if room.temp < heatTemp."),
                    (ROOM, "OffState: no temperature change. CoolState: temp decreases if AC is on, increases otherwise. "
                           "HeatState: temp increases if heater is on, decreases otherwise.")]),
    "OffState.java": ("Concrete OFF state", "Off-specific actions belong in the off state.",
                      "OFF transitions move here; the timer and room steps do nothing while off.",
                      "Starting cooling or heating from OFF behaves as in the original program.",
                      [("cool()", "Turn AC on, start timer, transition to COOL."),
                       ("heat()", "Turn heater on, start timer, transition to HEAT."),
                       ("off()", "No change: already OFF."),
                       ("timerOff()", "No change while OFF."),
                       (ROOM, "No temperature change while OFF.")]),
    "CoolState.java": ("Concrete COOL state", "Cooling-specific actions belong in the cooling state.",
                       "COOL transitions, timer checks, and room temperature updates move here.",
                       "Cooling transitions and simulated room temperature behavior match the original program.",
                       [("cool()", "No change: already COOL."),
                        ("heat()", "Turn AC off, heater on, start timer, transition to HEAT."),
                        ("off()", "Turn AC off, stop timer, transition to OFF."),
                        ("timerOff()", "If room.temp > coolTemp, AC on; otherwise AC off (equality turns AC off)."),
                        (ROOM, "If AC is on, decrement room.temp; otherwise increment it.")]),
    "HeatState.java": ("Concrete HEAT state", "Heating-specific actions belong in the heating state.",
                       "HEAT transitions, timer checks, and room temperature updates move here.",
                       "Heating transitions and simulated room temperature behavior match the original program.",
                       [("cool()", "Turn heater off, AC on, start timer, transition to COOL."),
                        ("heat()", "No change: already HEAT."),
                        ("off()", "Turn heater off, stop timer, transition to OFF."),
                        ("timerOff()", "If room.temp < heatTemp, heater on; otherwise heater off (equality turns heater off)."),
                        (ROOM, "If heater is on, increment room.temp; otherwise decrement it.")]),
}
OTHER_FILE = ("Generated file", "The refactoring agent added this file; it is not one of the five expected files.",
              "See the Changes tab for exactly what it contains.",
              "The program must still compile and behave as the original does.",
              [("Purpose", "Confirm this file is needed and does not duplicate another class."),
               ("Behavior", "Confirm it does not change any threshold, device, timer or message.")])


class RefactorReviewScreen(Screen):
    focus_marker = ""

    def __init__(self, app):
        run = app.workflow
        self.payload = run.pending
        self.files = {path.split("/")[-1]: source for path, source in (self.payload.get("files") or {}).items()}
        self.names = data.file_order(self.files)
        self.original = run.values.get("source_code") or data.read(data.ORIGINAL_SOURCE)
        self.fi, self.tab, self.top = 0, "changes", 0
        self.checked = set()     # (file name, check index)
        self.notes = {}          # file name -> note

    def guide(self, name):
        role, why, what, still, checks = GUIDE.get(name, OTHER_FILE)
        checks = list(checks)
        if name == "State.java":
            found = data.method_signatures(self.files[name])
            checks.append(("Exact signatures", "Found in this file: " + (", ".join(found) or "none") + "."))
        return role, why, what, still, checks

    def viewer_lines(self, name):
        """(lines as (number, text, style), title, kind, note) for the active tab."""
        source = self.files[name]
        had_original = name == "SeasonSwitch.java"
        if self.tab == "refactored":
            return [(i, line, "plain") for i, line in enumerate(source.expandtabs(4).splitlines(), 1)], name, "FULL FILE", None
        if self.tab == "original":
            note = None if had_original else f"No original {name} exists. Showing the original SeasonSwitch.java instead."
            return ([(i, line, "plain") for i, line in enumerate(self.original.expandtabs(4).splitlines(), 1)],
                    "SeasonSwitch.java (original)", "FULL FILE", note)
        diff = data.unified_diff(self.original.expandtabs(4) if had_original else "", source.expandtabs(4),
                                 "original/SeasonSwitch.java", f"refactored/{name}")
        lines, number = [], 0
        for line in diff:
            if line.startswith(("---", "+++")):
                lines.append(("", line, "file"))
            elif line.startswith("@@"):
                lines.append(("", line, "hunk"))
            else:
                number += 0 if line.startswith("-") else 1
                lines.append(("" if line.startswith("-") else number, line,
                              "add" if line.startswith("+") else "del" if line.startswith("-") else "plain"))
        return lines, name, "FULL DIFF", None

    def render(self, app):
        name = self.names[self.fi]
        role, why, what, still, checks = self.guide(name)
        out = T.header("HUMAN REVIEW #2", "State-Pattern Refactoring Review",
                       "Plain-language explanations + precise expected behaviors + one full-file code viewer. Review "
                       "before approving generated Java.", "AWAITING HUMAN APPROVAL")
        out.append(T.stage_strip(9))
        chips = Text()
        for i, file_name in enumerate(self.names):
            mark = " ✎" if file_name in self.notes else ""
            chips.append_text(Text.assemble((f" ▶ {file_name}{mark} ", T.SELECTED)) if i == self.fi
                              else Text.assemble((f" {file_name}{mark} ", "#afc0d6 on #16283a")))
            chips.append("  ")
        out.append(T.pad(T.pnl(Text.assemble(("SELECT GENERATED JAVA FILE", f"bold {T.TITLE}"),
                                             (f"   file {self.fi + 1} of {len(self.names)}", T.MUTED)), Text(""), chips)))

        def field(question, answer, green=False):
            return Text.assemble((question + "\n", f"bold {T.GREEN if green else T.TITLE}"), (answer, T.BODY if green else T.MUTED))

        added = sum(1 for _, line, kind in self.viewer_lines_for("changes", name) if kind == "add")
        removed = sum(1 for _, line, kind in self.viewer_lines_for("changes", name) if kind == "del")
        measured = (f" In this run: new file, {added} lines." if name != "SeasonSwitch.java"
                    else f" In this run: {added} lines added, {removed} removed.")
        out.append(T.pad(T.pnl(Text.assemble((name, f"bold {T.TITLE}"), (f" · {role}", "bold #a9bbce")), Text(""),
                               field("1. Why change it?", why), Rule(style="#324052"),
                               field("2. What changed?", what + measured), Rule(style="#324052"),
                               field("3. What should still work?", still, True))))
        rows = [T.head("4. WHAT SHOULD I CHECK?"),
                Text("Review each expected behavior against the complete Java source below. Each checkbox belongs to "
                     "the selected file.", style=T.MUTED)]
        for i, (method, what_to_check) in enumerate(checks, 1):
            rows.append(Rule(style="#2d3d52"))
            done = (name, i) in self.checked
            line = Table.grid(expand=True, padding=(0, 1))
            line.add_column(width=3)
            line.add_column(width=2)
            line.add_column(ratio=1)
            line.add_row(Text(f" {i} ", style=T.KB), Text("☑" if done else "☐", style=T.GREEN if done else T.INTRO),
                         Text.assemble((method + "\n", "bold #9dc6fb"), (what_to_check, T.SOFT)))
            rows.append(line)
        rows += [Text(""), Text("Press a number to check or uncheck that line.", style=T.FOOT)]
        out.append(T.pad(T.pnl(*rows, bg="#101d2f")))

        lines, title, kind, note = self.viewer_lines(name)
        shown = lines
        styles = {"plain": ("#61738c", "#dbe8ef"), "add": ("#61738c on #12281f", "#91ebbe on #12281f"),
                  "del": ("#61738c on #2a1620", "#f3a3ad on #2a1620"), "file": ("#e8d091", "#e8d091"), "hunk": ("#91bdfa", "#91bdfa")}
        code = Text()
        for n, (number, text, style) in enumerate(shown):
            gutter, body = styles[style]
            code.append(f" {number:>3}  ", style=gutter)
            code.append(text[:app.width - 22].ljust(app.width - 22) if style in ("add", "del") else text[:app.width - 22], style=body)
            if n < len(shown) - 1:
                code.append("\n")
        right = f"{kind} · {len(lines)} lines"
        viewer = [T.head("5. INSPECT JAVA IMPLEMENTATION"),
                  Text("See the complete source. Do not switch to small per-method code fragments.", style=T.MUTED),
                  T.tabs([("changes", "Changes · C"), ("refactored", "Refactored · F"), ("original", "Original · O")], self.tab)]
        if note:
            viewer.append(T.amber_note(note))
        viewer += [T.code_box(title, right, code),
                   Text("This is the Java the refactoring agent generated in this run.", style=T.FOOT)]
        out.append(T.pad(T.pnl(*viewer)))

        if name in self.notes:
            mark = Text.assemble(("☑ ", T.AMBER), ("This file needs changes: ", T.BODY), (self.notes[name] or "(no notes)", T.SOFT),
                                 ("   · press N to remove the mark", T.FOOT))
        else:
            mark = Text.assemble(("☐ ", T.INTRO), ("This file needs changes · press N to mark it and write notes", T.BODY))
        review = [T.head("6. YOUR REVIEW"), Text(""), mark, Rule(style="#324052"),
                  T.btnrow(T.btn("Approve Complete Refactoring", "A", T.BTN_PRIMARY)),
                  T.btnrow(T.btn("Preview Revision Batch", "R", T.BTN_AMBER), T.btn("Reject", "X", T.BTN_RED)), Text("")]
        if self.payload.get("prior_feedback"):
            review.append(Text("Your previous feedback: " + self.payload["prior_feedback"][:400], style=T.SOFT))
        review.append(Text("One overall implementation approval. File-specific revision feedback persists as the reviewer "
                           "navigates.", style=T.FOOT))
        out.append(T.pad(T.pnl(*review)))
        out += [T.keyrow("Navigation: ", [("← →", "change file"), ("↑ ↓", "scroll the page"), ("C F O", "change code view"), ("Esc", "back")]),
                T.keyrow("This file:  ", [(f"1-{len(checks)}", "tick a check"), ("N", "mark this file for changes")]),
                T.keyrow("Decide:     ", [("A", "approve all files"), ("R", "preview revision batch"), ("X", "reject")])]
        return out

    def viewer_lines_for(self, tab, name):
        saved, self.tab = self.tab, tab
        try:
            return self.viewer_lines(name)[0]
        finally:
            self.tab = saved

    def send(self, app):
        feedback = "\n".join(f"{name}: {note or 'needs changes'}" for name, note in self.notes.items())
        app.workflow.answer({"approved": False, "feedback": feedback})

    def on_key(self, key, app):
        run, name = app.workflow, self.names[self.fi]
        armed, self.approve_armed = getattr(self, "approve_armed", False), False
        if key == "esc":
            app.pop()
        elif key in ("left", "right"):
            self.fi = (self.fi + (1 if key == "right" else -1)) % len(self.names)
            self.top = 0
            app.scroll = 0   # the file list and the four answers change, so show them
        elif key in ("c", "f", "o"):
            self.tab, self.top = {"c": "changes", "f": "refactored", "o": "original"}[key], 0
        elif key.isdigit() and 1 <= int(key) <= len(self.guide(name)[4]):
            self.checked ^= {(name, int(key))}
        elif key == "n":
            if name in self.notes:
                del self.notes[name]
            else:
                note = app.ask_text(f"What needs to change in {name}?")
                if note is not None:
                    self.notes[name] = note
        elif key == "r":
            if self.notes:
                app.push(RevisionBatchScreen(self, files=True))
            else:
                app.message = "No files are marked yet. Press N on a file to mark it and write notes."
        elif key == "x":
            reason = app.ask_text("Reject the refactoring: what must change? (required)")
            if reason:
                run.answer({"approved": False, "feedback": reason})
                app.pop()
            elif reason == "":
                app.message = "A reason is required to reject. Nothing was sent."
        elif key == "a":
            if self.notes and not armed:
                self.approve_armed = True
                app.message = (f"You marked {len(self.notes)} file(s) for changes. Press A again to approve anyway, "
                               "or R to preview the revision batch.")
                return
            run.answer({"approved": True, "feedback": ""})
            app.pop()


# =========================================================================== 11 Final Results
class ResultsScreen(Screen):
    focus_marker = ""

    def __init__(self):
        self.junit = {p: data.junit_report(p) for p in ("original", "refactored")}
        self.cov = {p: data.coverage_report(p) for p in ("original", "refactored")}
        self.rerun_armed = False
        self.live = None   # the running workflow's state, set at each draw
        self.since = 0     # start time of this session's run; older reports do not count for it

    def rows(self):
        rows = []
        for phase in ("original", "refactored"):
            name, junit, cov = phase.capitalize(), self.junit[phase], self.cov[phase]
            if junit["reports_found"] and junit["written"] < self.since:
                rows.append((f"{name} JUnit", f"{junit['passed']}/{junit['total']} passed, but from an earlier run",
                             "OLD REPORT", T.CHIP_RED, False))
            elif junit["reports_found"]:
                ok = junit["all_passed"]
                rows.append((f"{name} JUnit", f"{junit['passed']}/{junit['total']} passed", "PASS" if ok else "FAIL",
                             T.CHIP_GREEN if ok else T.CHIP_RED, ok))
            else:
                rows.append((f"{name} JUnit", "No report on disk", "NO REPORT", T.CHIP_RED, False))
            if cov["found"] and cov["written"] < self.since:
                full = cov["full"]
                rows.append((f"{name} full-program coverage",
                             f"{full['covered']}/{full['total']} · {full['percent']:.2f}%, but from an earlier run",
                             "OLD REPORT", T.CHIP_RED, False))
            elif cov["found"]:
                full, scoped = cov["full"], cov["scoped"]
                done = full["missed"] == 0
                rows.append((f"{name} full-program coverage", f"{full['covered']}/{full['total']} · {full['percent']:.2f}%",
                             "COMPLETE" if done else "INCOMPLETE", T.CHIP_GREEN if done else T.CHIP_RED, done))
                if cov["same_scope"]:
                    continue
                if scoped["missed"]:
                    label, style = "INCOMPLETE", T.CHIP_RED
                elif done:
                    label, style = "COMPLETE", T.CHIP_GREEN
                else:
                    label, style = "SCOPE ONLY", T.CHIP_PLAIN
                extra = " (exclusions)" if not scoped["missed"] and not done else ""
                rows.append((f"{name} configured scope", f"{scoped['covered']}/{scoped['total']} · {scoped['percent']:.2f}%{extra}",
                             label, style, None))
            else:
                rows.append((f"{name} full-program coverage", "No JaCoCo report on disk", "NO REPORT", T.CHIP_RED, False))
        for kind, title in (("repair", "Automated repair"), ("gap", "Automated gap-test generation")):
            found = {phase: data.repair_rows(kind, phase, self.live) for phase in ("original", "refactored")}
            used = [row for rows_, _, _ in found.values() for row in rows_]
            where = next((w for _, w, _ in found.values() if w), "")
            if not where:
                rows.append((title, "No workflow run with a repair list saved yet", "NO RECORD", T.CHIP_PLAIN, None))
            elif not used:
                rows.append((title, f"Not needed ({where})", "NOT NEEDED", T.CHIP_GREEN, None))
            else:
                count = {}
                for row in used:
                    words = data.REPAIR_OUTCOME.get(row.get("outcome"), str(row.get("outcome")))
                    count[words] = count.get(words, 0) + 1
                last = used[-1].get("outcome")
                bad = last in ("exhausted", "rerun_failed", "ai_error", "human_rejected")
                rows.append((title, " · ".join(f"{words}: {n}" for words, n in count.items()) + f" ({where})",
                             "STOPPED" if bad else "USED", T.CHIP_RED if bad else T.CHIP_GREEN, None))
        return rows

    def render(self, app):
        run = app.workflow
        self.live = run.values if run else None
        self.since = run.started - 2 if run else 0
        rows = self.rows()
        required = [ok for *_, ok in rows if ok is not None]
        stopped = bool(run and (run.stopped or str(run.values.get("workflow_status", "")).endswith(("exhausted", "failed", "blocked"))))
        complete = all(required) and len(required) == 4 and not stopped
        out = T.header("RESULTS & NEXT ACTIONS", "Automated Workflow Results",
                       "No manual submission checklist. The screen stays visible until the user chooses an action.",
                       "WORKFLOW COMPLETE" if complete else "WORKFLOW INCOMPLETE", T.CHIP_GREEN if complete else None)
        out.append(T.stage_strip(11, in_run=bool(app.workflow)))
        line = Table.grid(expand=True, padding=(0, 1))
        line.add_column(width=2)
        line.add_column(ratio=1)
        if complete:
            line.add_row(Text("●", style=T.GREEN),
                         Text.assemble(("COMPLETE — tests pass and full-program branch coverage is 100%\n", f"bold {T.GREEN}"),
                                       ("Both the original and the refactored program meet the automated checks.", T.SOFT)))
        else:
            tests_ok = all(j["reports_found"] and j["all_passed"] for j in self.junit.values())
            reason = ("the workflow stopped before finishing" if stopped else
                      "coverage requirements not satisfied" if tests_ok else "tests are failing or were not run")
            line.add_row(Text("●", style=T.RED),
                         Text.assemble((f"INCOMPLETE — {reason}\n", f"bold {T.AMBER}"),
                                       ("Test success is not sufficient to mark the complete workflow as passed.", T.SOFT)))
        status = [T.head("OVERALL STATUS"), Text(""), line]
        if run and run.auto:
            status.append(T.amber_note("This was an AUTO-APPROVE test run: no person reviewed the tests or the Java. "
                                       "Not valid as final evidence."))
        if run and run.status in ("finished", "failed"):
            status.append(Text(f"Last run in this session ended with status: {run.values.get('workflow_status') or run.error}", style=T.FOOT))
        out.append(T.pad(T.pnl(*status) if complete else T.warn_pnl(*status)))
        table = Table(box=box.HORIZONTALS, expand=True, border_style="#304055", header_style="bold #a3b5c8",
                      padding=(0, 1), show_edge=False, show_lines=True)
        table.add_column("AUTOMATED RESULT", ratio=5)
        table.add_column("EVIDENCE", ratio=4)
        table.add_column("STATUS", ratio=2)
        for name, evidence, label, style, _ in rows:
            table.add_row(Text(name, style=T.BODY), Text(evidence, style=T.SOFT), T.chip(label, style))
        notes = " · ".join(f"{p}: {self.cov[p]['source_note'] or 'no JaCoCo report'}" for p in ("original", "refactored"))
        out.append(T.pad(T.pnl(T.head("VERIFICATION SUMMARY"), Text(""), table, Text(""),
                               Text("Read from the reports on disk. " + notes, style=T.FOOT))))
        out.append(T.pad(T.pnl(T.head("RESULTS & NEXT ACTIONS"), Text(""),
                               T.btnrow(T.btn("View Test Results", "T"), T.btn("Inspect Coverage", "C"), T.btn("Rerun", "R", T.BTN_AMBER)),
                               T.btnrow(T.btn("Main Menu", "M"), T.btn("Exit", "Q")), Text(""),
                               Text("Rerun starts only when you press R.", style=T.FOOT))))
        out.append(Text(""))
        return out

    def on_key(self, key, app):
        latest = "refactored" if self.junit["refactored"]["reports_found"] else "original"
        armed, self.rerun_armed = self.rerun_armed, False
        if key == "t":
            app.push(JUnitScreen(latest))
        elif key == "c":
            app.push(CoverageScreen(latest))
        elif key == "r":
            if app.workflow and app.workflow.status in ("running", "waiting", "starting"):
                app.message = "A run is already in progress. Press M, then 1, to return to it."
            elif not armed:
                self.rerun_armed = True
                app.message = "Rerun starts the complete workflow again and calls the AI models. Press R again to start."
            else:
                app.home()
                app.open_workflow(fresh=True, auto=bool(app.workflow and app.workflow.auto))
        elif key == "m":
            app.home()
        elif key == "esc":
            app.pop()
        elif key == "q":
            quit_or_warn(app)


# =========================================================================== 12 Tools
class ToolsScreen(Screen):
    focus_marker = ""

    def __init__(self):
        self.target = "clean"
        self.ticked = False

    def render(self, app):
        def card(command, what, key, color=T.TITLE, focus=False):
            return Panel(Text.assemble((command, f"bold {color}"), (f"  ·  press {key}\n", T.MUTED), (what, T.MUTED)),
                         title=Text.assemble((" SELECTED ", T.SELECTED)) if focus else None, title_align="left",
                         box=box.HEAVY if focus else box.ROUNDED, border_style=T.CY if focus else "#33455c",
                         style=f"on {'#1a3c50' if focus else '#15243a'}", padding=(0, 1))

        def two(left, right):
            grid = Table.grid(expand=True, padding=(0, 1))
            grid.add_column(ratio=1)
            grid.add_column(ratio=1)
            grid.add_row(left, right)
            return grid

        out = T.header("TOOLS & MAINTENANCE", "Command Tools & Safe Cleanup",
                       "All Makefile operations share this UI. Cleanup previews actual deletion targets before confirmation.",
                       "SAFETY PREVIEW")
        out.append(T.pad(T.pnl(T.head("SAFE TOOLS"), Text(""),
                               two(card("make help", "Show supported targets and explanations", "H"),
                                   card("make build-merger", "Build JavaParser JUnit merger", "B")))))
        found = data.cleanup_targets(self.target)
        listing = Text.assemble(("Would delete for ", T.SOFT), (f"make {self.target}", f"bold {T.AMBER}"), (":\n", T.SOFT))
        if found:
            listing.append("\n".join(f"  {path}   ({count} files, {data.human_size(size)})" for path, count, size in found), style="#dbe8ef")
        else:
            listing.append("  Nothing. No build output folders exist right now.", style="#dbe8ef")
        targets = Panel(Group(listing, Text(""), Text("Listed from disk just now. Only these folders inside the project are removed.", style=T.FOOT)),
                        box=box.ROUNDED, border_style="#32435a", style="on #0d1726", padding=(0, 1))
        confirm = (T.btn("Confirm Cleanup", "Enter", T.BTN_RED) if self.ticked
                   else T.btn("Confirm Cleanup", "Enter (off until the box is ticked)", T.BTN_OFF))
        out.append(T.pad(T.warn_pnl(
            T.head("CLEANUP — CONFIRMATION REQUIRED"), Text(""),
            two(card("make clean", "Preview actual generated/build paths", "1", T.AMBER, self.target == "clean"),
                card("make clean-all", "Preview broader generated paths; never remove outside project", "2", T.RED, self.target == "clean-all")),
            Text(""), targets, Text(""), T.amber_note("Nothing is deleted until you tick the box and confirm."), Text(""),
            Text.assemble(("☑ " if self.ticked else "☐ ", T.GREEN if self.ticked else T.INTRO),
                          ("I have reviewed the exact deletion targets · press Y", T.BODY)), Text(""), T.btnrow(confirm))))
        out += [Text(""), T.keyrow("Navigation: ", [("Esc", "main menu"), ("q", "quit")]), Text("")]
        return out

    def on_key(self, key, app):
        if key == "h":
            app.push(CommandScreen("help"))
        elif key == "b":
            app.push(CommandScreen("build-merger"))
        elif key in ("1", "2"):
            self.target, self.ticked = ("clean" if key == "1" else "clean-all"), False
        elif key == "y":
            self.ticked = not self.ticked
        elif key == "enter":
            if not self.ticked:
                app.message = "Tick the box with Y first. Nothing was deleted."
            elif app.workflow and app.workflow.status in ("running", "waiting", "starting"):
                app.message = "A workflow run is in progress. Cleanup is off until it ends."
            else:
                self.ticked = False
                app.push(CommandScreen(self.target))
        elif key == "esc":
            app.home()
        elif key == "q":
            quit_or_warn(app)
