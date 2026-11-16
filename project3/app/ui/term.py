"""Terminal plumbing: read single keys, draw one screen at a time, scroll tall screens."""
import os
import select
import sys
import termios
import time
import tty

from rich.console import Console, Group
from rich.segment import Segment
from rich.style import Style
from rich.text import Text

from . import theme as T

MIN_COLUMNS, MIN_ROWS = 80, 20

ESCAPES = {
    "[A": "up", "[B": "down", "[C": "right", "[D": "left", "OA": "up", "OB": "down", "OC": "right",
    "OD": "left", "[5~": "pgup", "[6~": "pgdn", "[H": "home", "[F": "end", "[1~": "home", "[4~": "end",
    "OH": "home", "OF": "end", "[3~": "delete",
}


class Keyboard:
    """Single-key input from the terminal, without waiting for Enter."""

    def __init__(self, fd):
        self.fd = fd
        self.saved = None

    def __enter__(self):
        self.saved = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)
        return self

    def __exit__(self, *exc):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.saved)

    def _ready(self, timeout):
        return bool(select.select([self.fd], [], [], timeout)[0])

    def read(self, timeout=0.25):
        """Return a key name ('up', 'enter', 'esc', 'a', ...) or None after `timeout` seconds."""
        if not self._ready(timeout):
            return None
        data = os.read(self.fd, 1)
        if data == b"\x1b":
            seq = b""
            while self._ready(0.03) and len(seq) < 6:
                seq += os.read(self.fd, 1)
                if seq[-1:].isalpha() or seq[-1:] == b"~":
                    break
            return ESCAPES.get(seq.decode("ascii", "ignore"), "esc" if not seq else None)
        if data in (b"\r", b"\n"):
            return "enter"
        if data in (b"\x7f", b"\x08"):
            return "backspace"
        if data == b"\t":
            return "tab"
        if data == b"\x03":
            raise KeyboardInterrupt
        if data[0] >= 0x80:  # finish a multi-byte UTF-8 character
            need = 3 if data[0] >= 0xF0 else 2 if data[0] >= 0xE0 else 1
            data += os.read(self.fd, need)
        text = data.decode("utf-8", "ignore")
        if text == " ":
            return "space"
        return text if text.isprintable() else None


class Screen:
    """One full page. Subclasses return renderables and react to keys."""

    focus_marker = "SELECTED ·"   # the page scrolls to keep the first line with this text visible
    refresh = False               # True while the screen shows something that changes by itself
    page_arrows = True            # ↑ ↓ scroll the page; False on screens where they move a selection
    stick_bottom = False          # True while new lines keep arriving at the end of the page
    back_label = "Back"           # words on the Esc button at the top of the page ("" = no button)

    def render(self, app):
        raise NotImplementedError

    def on_key(self, key, app):
        pass

    def focus_edge(self):
        """'first' or 'last' when the selected item is the first or last one, so the page can
        return to its very top or very bottom; None for anything in between."""
        return None


class Display:
    """Draws screens on the alternate terminal buffer and keeps a stack of them."""

    def __init__(self):
        self.tty = open("/dev/tty", "w", encoding="utf-8", buffering=1)
        self.console = Console(file=self.tty, force_terminal=True, color_system="truecolor",
                               highlight=False, legacy_windows=False)
        self.keyboard = Keyboard(os.open("/dev/tty", os.O_RDONLY))
        self.stack = []
        self.scroll = 0
        self.follow = True     # scroll to the selected item on the next draw
        self.at_bottom = False # the last draw showed the end of the page
        self.message = ""      # one-line notice shown in the bottom row
        self.running = True
        self.exit_code = 0

    # ---- screen stack
    @property
    def screen(self):
        return self.stack[-1]

    def push(self, screen):
        self.stack.append(screen)
        self.scroll, self.follow, self.message, self.at_bottom = 0, True, "", True

    def pop(self):
        if len(self.stack) > 1:
            self.stack.pop()
            self.scroll, self.follow, self.message, self.at_bottom = 0, True, "", True

    def replace(self, screen):
        self.stack.pop()
        self.push(screen)

    def home(self):
        del self.stack[1:]
        self.scroll, self.follow, self.message, self.at_bottom = 0, True, "", True

    def quit(self, code=0):
        self.running, self.exit_code = False, code

    # ---- drawing
    @property
    def width(self):
        """The whole window is used. Below 80 columns the page asks for a larger window instead."""
        return max(MIN_COLUMNS, self.console.size.width)

    @property
    def height(self):
        return self.console.size.height

    def _follow_selection(self, lines, room, top_limit):
        """Scroll so the selected item is in view; the first item shows the top of the page
        and the last item shows the bottom."""
        marker = self.screen.focus_marker
        index = next((i for i, line in enumerate(lines) if marker in "".join(seg.text for seg in line)), None)
        if index is None:
            return
        edge = self.screen.focus_edge()
        below = min(14, room // 2)          # lines kept visible under the start of the selected item
        if edge == "first" and index <= room - 4:
            self.scroll = 0
        elif edge == "last" and index >= top_limit + 2:
            self.scroll = top_limit
        elif index < self.scroll + 3:
            self.scroll = index - 3
        elif index > self.scroll + room - below:
            self.scroll = index - (room - below)

    def _lines(self, renderables):
        options = self.console.options.update(width=self.width)
        return self.console.render_lines(Group(*renderables), options, style=Style(bgcolor=T.BG), pad=True)

    def draw(self, extra_bottom=None):
        self.drawn_live = self.screen.refresh   # was it still changing when this picture was taken?
        size = self.console.size
        if size.width < MIN_COLUMNS or size.height < MIN_ROWS:
            self._draw_too_small(size)
            return
        parts = self.screen.render(self)
        if len(self.stack) > 1 and self.screen.back_label:   # every page below the main menu can go back
            parts = [T.pad(T.btnrow(T.btn("◀ " + self.screen.back_label, "Esc")))] + list(parts)
        pinned = [part for part in parts if getattr(part, "pinned", False)]
        lines = self._lines([part for part in parts if not getattr(part, "pinned", False)])
        while lines and not "".join(seg.text for seg in lines[-1]).strip():
            lines.pop()                      # no empty rows under the last panel
        bottom = self._lines(pinned + list(extra_bottom or []))
        height = self.console.size.height
        room = max(3, height - 1 - len(bottom))
        top_limit = max(0, len(lines) - room)
        if self.screen.stick_bottom and self.at_bottom:
            self.scroll = top_limit          # keep showing the newest lines
        if self.follow and self.screen.focus_marker:
            self._follow_selection(lines, room, top_limit)
            self.follow = False
        self.scroll = max(0, min(self.scroll, top_limit))
        if top_limit:   # following the newest lines starts only when the reader is at the end of a long page
            self.at_bottom = self.scroll >= top_limit
        visible = lines[self.scroll:self.scroll + room]
        blank = [Segment(" " * self.width, Style(bgcolor=T.BG))]
        visible += [blank] * (room - len(visible))
        if top_limit:
            how = ("↑ ↓ scroll the page  ·  Space = next page" if self.screen.page_arrows
                   else "the page follows the selected item  ·  PgUp / PgDn scroll the page")
            more = "more below ↓" if self.scroll < top_limit else "end of page"
            status = f" Lines {self.scroll + 1}-{self.scroll + room} of {len(lines)}  ·  {more}  ·  {how}"
        else:
            status = ""
        if self.message:
            status = f" {self.message}"
        status_line = [Segment(status[:self.width].ljust(self.width),
                               Style(color="#0b1220", bgcolor=T.CY) if self.message
                               else Style(color=T.FOOT, bgcolor="#0b1220"))]
        out = ["\x1b[H"]
        for line in visible + bottom + [status_line]:
            out.append("".join(self._ansi(seg) for seg in line))
            out.append("\x1b[K\r\n")
        out[-1] = "\x1b[K"
        self.tty.write("".join(out))
        self.tty.flush()

    def _draw_too_small(self, size):
        """Never draw a broken page: say what size is needed and wait for the window to grow."""
        words = [f"This window is {size.width} x {size.height}.",
                 f"The dashboard needs at least {MIN_COLUMNS} x {MIN_ROWS}.",
                 "Make the window larger to continue."]
        out = ["\x1b[H\x1b[2J"] + [w[:max(1, size.width)] + "\r\n" for w in words]
        self.tty.write("".join(out))
        self.tty.flush()
        self.follow = True

    def _ansi(self, segment):
        if segment.style:
            return segment.style.render(segment.text, color_system=self.console.color_system)
        return segment.text

    # ---- main loop
    def run(self, first_screen):
        self.push(first_screen)
        self.tty.write("\x1b[?1049h\x1b[?25l\x1b[2J")
        try:
            with self.keyboard:
                self.draw()
                size = self.console.size
                while self.running:
                    key = self.keyboard.read(0.25)
                    if key is None:
                        # Redraw while a screen is live, and once more after it stops changing.
                        if self.screen.refresh or self.drawn_live or self.console.size != size:
                            if self.console.size != size:
                                self.follow = True
                                self.tty.write("\x1b[2J")
                            size = self.console.size
                            self.draw()
                        continue
                    if self.console.size.width < MIN_COLUMNS or self.console.size.height < MIN_ROWS:
                        continue   # keys do nothing while the page cannot be shown
                    self.message = ""
                    height = self.console.size.height
                    arrows = self.screen.page_arrows
                    if key in ("pgup", "home") or (arrows and key == "up"):
                        self.at_bottom = False   # the reader scrolled up: stop following new lines
                    if key == "pgdn" or (arrows and key == "space"):
                        self.scroll += height - 6
                    elif key == "pgup":
                        self.scroll -= height - 6
                    elif arrows and key in ("up", "down"):
                        self.scroll += 3 if key == "down" else -3
                    elif key == "home":
                        self.scroll = 0
                    elif key == "end":
                        self.scroll = 10 ** 6
                    else:
                        self.screen.on_key(key, self)
                    if self.running:
                        self.draw()
        finally:
            self.tty.write("\x1b[?25h\x1b[?1049l")
            self.tty.flush()
        return self.exit_code

    # ---- one line of typed text (reviewer feedback)
    def ask_text(self, title, initial=""):
        """Let the reviewer type a note. Enter saves it, Esc cancels (returns None)."""
        text = initial
        while True:
            box = T.pad(T.pnl(
                Text(title, style=f"bold {T.TITLE}"),
                Text.assemble((text, T.BODY), ("█", T.CY)),
                Text("Type your note.   Enter = save    Esc = cancel", style=T.FOOT),
                border=T.CY, bg="#142b3a", padding=(0, 2)))
            self.draw(extra_bottom=[box])
            key = self.keyboard.read(0.5)
            if key is None:
                continue
            if key == "enter":
                return text.strip()
            if key == "esc":
                return None
            if key == "backspace":
                text = text[:-1]
            elif key == "space" or len(key) == 1:
                text += " " if key == "space" else key


def plain_terminal():
    """True when a full-screen dashboard cannot be shown (no terminal, or it was turned off)."""
    if os.environ.get("UI") == "0" or os.environ.get("AUTO_APPROVE") == "1":
        return True
    return not (sys.stdin.isatty() and sys.stdout.isatty())
