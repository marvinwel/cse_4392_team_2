"""Entry point for the terminal dashboard.

    make ui                           the normal way in: opens the main menu
    python app/tui.py menu            the same
    python app/tui.py run             open the dashboard straight on a workflow run
    python app/tui.py <make target>   run that Makefile target inside the dashboard

The dashboard is optional. `make run`, `make auto` and every other Makefile target stay plain.
Without a terminal (a pipe, CI), with UI=0, with AUTO_APPROVE=1, or when `rich` is not
installed, nothing here draws a dashboard: the plain command runs instead.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from ui.term import plain_terminal  # noqa: E402
except ImportError as missing:   # the dashboard needs the `rich` package; everything else works without it
    print(f"Dashboard not available ({missing}). Running the plain command instead. "
          "To get the dashboard: pip install -r app/requirements.txt", file=sys.stderr)

    def plain_terminal():
        return True

TARGETS = ("help", "run", "test-original", "test-original-current", "test-refactored", "verify-original",
           "verify-refactored", "build-merger", "clean", "clean-all", "test-python", "check")


def run_plain(action):
    if action == "run":
        import main
        main.run_plain()
        return 0
    if action in ("menu", "ui"):
        action = "help"
    os.chdir(Path(__file__).resolve().parent.parent)
    os.execvp("make", ["make", "--no-print-directory", action])


def run_dashboard(action):
    from ui import screens
    from ui.runner import WorkflowRun
    from ui.term import Display

    class Dashboard(Display):
        workflow = None        # the WorkflowRun of this session, if one was started
        previous_tests = []    # tests as they were when changes were last requested

        def open_workflow(self, fresh=False, auto=False):
            """auto=True starts an AUTO_APPROVE test run: every human review is skipped."""
            if self.workflow is None or (fresh and self.workflow.status in ("finished", "failed")):
                self.workflow = WorkflowRun(auto=auto)
                self.previous_tests = []
                self.workflow.start()
            self.push(screens.WorkflowScreen())

    app = Dashboard()
    if action == "menu":
        return app.run(screens.MenuScreen())
    app.stack.append(screens.MenuScreen())   # Esc from a direct target leads to the main menu
    if action == "run":
        app.workflow = WorkflowRun()
        app.workflow.start()
        return app.run(screens.WorkflowScreen())
    if action in ("clean", "clean-all"):
        tools = screens.ToolsScreen()
        tools.target = action
        return app.run(tools)
    return app.run(screens.CommandScreen(action, direct=True))


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "menu"
    if action != "menu" and action not in TARGETS:
        sys.exit(f"Unknown action {action!r}. Use menu or one of: {', '.join(TARGETS)}")
    sys.exit(run_plain(action) if plain_terminal() else run_dashboard(action))
