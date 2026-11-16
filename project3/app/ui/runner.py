"""Runs the real LangGraph workflow on a background thread and records what happens,
so the dashboard can redraw after every step and hand the human reviews to the reviewer."""
import io
import logging
import re
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime

from . import data

# Which workflow step (1-11, see theme.STEPS) each graph node belongs to.
NODE_STEP = {
    "load_source": 1, "ep_agent": 2, "bva_agent": 2,
    "review_ep": 3, "review_bva": 3, "ep_done": 3, "bva_done": 3, "merge_tests": 3,
    "review_tests": 4, "refactor_agent": 8, "review_refactor": 9,
}
PHASE_STEP = {  # nodes that run in both phases
    "run_tests": {"original": 5, "refactored": 10},
    "check_coverage": {"original": 6, "refactored": 10},
    "save_results": {"original": 6, "refactored": 10},
    "save_change_log": {"original": 6, "refactored": 10},
    "repair_agent": {"original": 5, "refactored": 10},
    "apply_code_repair": {"original": 5, "refactored": 10},
    "generate_gap_tests": {"original": 7, "refactored": 10},
}
REVIEW_KIND = {"repair": "Human review of a proposed repair", "gap": "Human review of coverage-gap tests"}
NODE_LABEL = {
    "load_source": "Load Java source", "ep_agent": "EP Test Generation Agent",
    "bva_agent": "BVA Test Generation Agent", "review_ep": "AI Test Review (EP)",
    "review_bva": "AI Test Review (BVA)", "ep_done": "EP tests ready to merge",
    "bva_done": "BVA tests ready to merge", "merge_tests": "Test Merge & Deduplication",
    "review_tests": "Human Test Review", "run_tests": "JUnit run (Maven)",
    "repair_agent": "Repair Agent", "apply_code_repair": "Write approved code fix", "check_coverage": "JaCoCo branch coverage",
    "save_results": "Save evidence", "save_change_log": "Save change log",
    "generate_gap_tests": "Coverage-gap test generation", "refactor_agent": "State-pattern Refactoring Agent",
    "review_refactor": "Human Refactoring Review",
    "escalate_review": "Stopped: a limit was reached or a step was blocked",
}
# Which model object of app/main.py each AI node calls (read from main.py: the EP/BVA agents use
# generator_model, the AI reviews use review_model, and the refactoring, repair and gap-test agents are
# built with refactor_model). The model's name is read from that object when the run starts; it is never typed here.
NODE_MODEL = {
    "ep_agent": "generator_model", "bva_agent": "generator_model",
    "review_ep": "review_model", "review_bva": "review_model",
    "refactor_agent": "refactor_model", "repair_agent": "refactor_model", "generate_gap_tests": "refactor_model",
}
# The AI nodes of each workflow step, and when a step calls its model only sometimes.
STEP_AI = {2: ["ep_agent", "bva_agent"], 3: ["review_ep", "review_bva"], 5: ["repair_agent"],
           7: ["generate_gap_tests"], 8: ["refactor_agent"], 10: ["repair_agent", "generate_gap_tests"]}
STEP_AI_WHEN = {5: "used only when a test fails", 7: "used only when coverage is below 100%",
                10: "used only when a test fails or coverage is below 100%"}
SECRET = re.compile(r"(AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|(?i:secret|token|password|credential)\S*\s*[=:]\s*\S+)")


def redact(text):
    """Never show credentials in the event history."""
    return SECRET.sub("[redacted]", str(text))


class _Capture(io.TextIOBase):
    """Collects print() output from the workflow so it lands in the event history, not on the screen."""

    def __init__(self, run):
        self.run, self.buffer = run, ""

    def write(self, text):
        self.buffer += text
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            if line.strip():
                self.run.add_event("output", line.strip())
        return len(text)


class _LogHandler(logging.Handler):
    def __init__(self, run):
        super().__init__()
        self.run = run

    def emit(self, record):
        self.run.add_event("log", record.getMessage())


class WorkflowRun:
    """One `make run`. State is only what the graph reported; nothing is assumed."""

    def __init__(self, auto=False):
        self.auto = auto            # True: AUTO_APPROVE test run, every human review is skipped
        self.node_runs = {}         # graph node name -> how many times it finished
        self.events = []            # (clock time, tag, text)
        self.models = {}            # main.py model object name -> the model name it reports (set when main loads)
        self.values = {}            # latest graph state
        self.active = []            # node names running now
        self.step = 0               # current step, 1-11 (0 = not started)
        self.steps_run = set()      # steps that had at least one node finish
        self.steps_blocked = set()  # kept for the progress list; nothing sets it now
        self.stop_step = 0          # step at which the workflow gave up (0 = it did not)
        self.review_step = 4        # step shown while the test review is open (4, or 5/7/10 for a proposal)
        self.pending = None         # payload of the human review the graph is waiting on
        self.status = "starting"    # starting | running | waiting | finished | failed
        self.error = ""
        self.started = time.time()
        self.finished_at = None
        self._answer = None
        self._answered = threading.Event()
        self._lock = threading.Lock()
        self.thread = threading.Thread(target=self._work, daemon=True)

    def start(self):
        self.thread.start()

    def add_event(self, tag, text):
        with self._lock:
            self.events.append((datetime.now().strftime("%H:%M:%S"), tag, redact(text)))

    # ---- called by the dashboard
    def answer(self, decision):
        """Give the reviewer's decision to the paused graph."""
        self.pending = None
        self.status = "running"
        self._answer = decision
        self._answered.set()

    def elapsed(self):
        seconds = int((self.finished_at or time.time()) - self.started)
        return f"{seconds // 60}m {seconds % 60:02d}s"

    def model_of(self, node):
        """The AI model a graph node calls: None for a node with no AI model, "" before the workflow has loaded."""
        if node not in NODE_MODEL:
            return None
        return self.models.get(NODE_MODEL[node], "")

    def model_line(self, nodes):
        """One line naming the AI model(s) behind these nodes, e.g. for a workflow step."""
        nodes = [node for node in nodes if node in NODE_MODEL]
        if not nodes:
            return ""   # a step that needs no AI model says nothing about models
        if not self.models:
            return "AI model: shown when the run has loaded"
        names = list(dict.fromkeys(self.model_of(node) for node in nodes))
        if len(names) == 1:
            return "AI model: " + names[0]
        return "AI models: " + " · ".join(f"{NODE_LABEL.get(n, n)}: {self.model_of(n)}" for n in nodes)

    def _read_models(self, main):
        for name in set(NODE_MODEL.values()):
            model = getattr(main, name, None)
            found = getattr(model, "model_id", None) or getattr(model, "model", None)
            self.models[name] = found if isinstance(found, str) and found else "name not readable"

    # ---- worker thread
    def _step_of(self, node):
        if node == "review_tests":
            return self.review_step
        if node in PHASE_STEP:
            return PHASE_STEP[node].get(self.values.get("phase") or "original", 5)
        return NODE_STEP.get(node, self.step)

    def _on_event(self, kind, node, update, values):
        self.values = dict(values or self.values)
        if kind == "review":
            return
        # A finished step's own results are not in the saved state until the whole step ends.
        self.values.update({k: v for k, v in (update or {}).items() if k != "change_log"})
        label = NODE_LABEL.get(node, node)
        if kind == "start":
            self.active.append(node)
            if node == "escalate_review":
                self.stop_step = self.step      # the step that could not be finished
            if not self.stop_step:
                self.step = self._step_of(node)
            self.status = "running"
            model = self.model_of(node)
            self.add_event("component", label + (f" · AI model: {model}" if model else ""))
        else:
            if node in self.active:
                self.active.remove(node)
            status = (update or {}).get("workflow_status")
            self.node_runs[node] = self.node_runs.get(node, 0) + 1
            if not self.stop_step:
                self.steps_run.add(self._step_of(node))
            self.add_event("done", label + (f" → {status}" if status else ""))

    def _ask(self, payload):
        self.active = []
        kind = payload.get("review_context")
        if payload.get("node") == "review_refactor":
            self.step = 9
        elif kind in REVIEW_KIND:   # a repair or gap proposal belongs to the step that produced it
            self.step = PHASE_STEP["repair_agent" if kind == "repair" else "generate_gap_tests"].get(
                self.values.get("phase") or "original", 5)
        else:
            self.step = 4
        self.review_step = self.step
        if self.auto:
            # Same answer the plain `make auto` (AUTO_APPROVE=1) gives. Testing shortcut only.
            self.add_event("checkpoint", "AUTO_APPROVE=1: human review skipped at "
                           + (REVIEW_KIND.get(kind) or NODE_LABEL.get(payload.get("node"), "review")))
            for name in (payload.get("ai_review_notes") or {}):
                self.add_event("error", f"WARNING: the AI reviewer rejected the {name} tests 3 times; "
                                        "auto-approved without a person checking them.")
            return {"approved": True, "feedback": "", "auto": True}
        self.pending = payload
        self.status = "waiting"
        self.add_event("checkpoint", "awaiting human approval: "
                       + (REVIEW_KIND.get(kind) or NODE_LABEL.get(payload.get("node"), "review")))
        self._answered.clear()
        self._answered.wait()
        decision = self._answer
        self.add_event("checkpoint", "human approved" if decision.get("approved") else "human requested changes")
        return decision

    def _work(self):
        real_out, real_err = sys.stdout, sys.stderr
        capture = _Capture(self)
        sys.stdout = sys.stderr = capture
        try:
            self._ensure_merger()
            import main  # the real workflow (app/main.py); imported here so menus open instantly
            for handler in list(main.log.handlers):
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    main.log.removeHandler(handler)
            main.log.addHandler(_LogHandler(self))
            self._read_models(main)
            self.values = main.run_workflow(self._ask, self._on_event)
            if not self.stop_step:
                self.steps_run.add(self.step)
            self.step = 11
            self.status = "finished"
            self.add_event("done", "Workflow ended: " + str(self.values.get("workflow_status", "finished")))
        except Exception as exc:  # shown on the dashboard, never hidden
            self.status = "failed"
            self.error = f"{type(exc).__name__}: {redact(exc)}"
            self.add_event("error", self.error)
            for line in traceback.format_exc().splitlines()[-6:]:
                self.add_event("error", line)
        finally:
            self.active = []
            self.finished_at = time.time()
            sys.stdout, sys.stderr = real_out, real_err

    def _ensure_merger(self):
        """`make run` builds the merger JAR first when it is missing or stale; do the same."""
        self.add_event("component", "Check JUnit merger JAR (make)")
        proc = subprocess.run(["make", "--no-print-directory", "junit-merger/target/junit-merger-1.0.0.jar"],
                              cwd=data.ROOT, capture_output=True, text=True)
        for line in (proc.stdout + proc.stderr).splitlines()[-5:]:
            self.add_event("output", line)
        if proc.returncode != 0:
            raise RuntimeError("The JUnit merger JAR could not be built (make exit "
                               f"{proc.returncode}). See the event history.")

    @property
    def stopped(self):
        """True when the run ended without finishing: an error, or a limit or block in the workflow."""
        return self.status == "failed" or bool(self.stop_step)

    # ---- what the progress list shows
    def step_state(self, number):
        if self.stop_step:                       # the workflow stopped early at stop_step
            if number == self.stop_step:
                return "failed"
            if number > self.stop_step:
                return "skipped"
        if self.status == "finished" and number == 11:
            return "done"
        if number == self.step and self.status in ("running", "waiting", "starting"):
            return "active"
        if number == self.step and self.status == "failed":
            return "failed"
        if number in self.steps_blocked:
            return "blocked"
        if number in self.steps_run:
            return "done" if number < self.step or self.status == "finished" else "again"
        if number < self.step:
            return "skipped"
        return "pending"


class CommandRun:
    """One Makefile target run as a normal subprocess, with its real output and exit code."""

    def __init__(self, target):
        self.target = target
        self.lines = []
        self.exit_code = None
        self.started = time.time()
        self.finished_at = None
        self.thread = threading.Thread(target=self._work, daemon=True)
        self.thread.start()

    def _work(self):
        try:
            proc = subprocess.Popen(["make", "--no-print-directory", self.target], cwd=data.ROOT,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                    stdin=subprocess.DEVNULL)
            for line in proc.stdout:
                self.lines.append(redact(line.rstrip("\n")))
            self.exit_code = proc.wait()
        except OSError as exc:
            self.lines.append(f"Could not start make: {exc}")
            self.exit_code = 127
        self.finished_at = time.time()

    @property
    def running(self):
        return self.exit_code is None

    def elapsed(self):
        seconds = int((self.finished_at or time.time()) - self.started)
        return f"{seconds // 60}m {seconds % 60:02d}s"
