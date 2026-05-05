"""Epsimo TUI — interactive terminal dashboard (no curses dependency)."""
import json
import sys
import os

# ANSI colors
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CLEAR = "\033[2J\033[H"

# ── Animated spinners ───────────────────────────────────────────────
import threading, time, itertools

SPINNERS = {
    "connecting": {"frames": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"], "color": CYAN},
    "thinking":   {"frames": ["🧠", "💭", "🧠", "💭", "🧠", "✨"], "color": YELLOW},
    "searching":  {"frames": ["🔍", "🔎", "🔍", "🔎"], "color": CYAN},
    "writing":    {"frames": ["✍️ ", "📝", "✍️ ", "📝"], "color": GREEN},
    "tool":       {"frames": ["🔧", "⚙️ ", "🔧", "⚙️ "], "color": YELLOW},
    "loading":    {"frames": ["◐", "◓", "◑", "◒"], "color": CYAN},
    "success":    {"frames": ["✅"], "color": GREEN},
    "streaming":  {"frames": ["▌", "▐", "▌", "▐"], "color": CYAN},
}

SLASH_CMDS = [
    ("/help",        "Show all commands"),
    ("/status",      "Account info"),
    ("/credits",     "Thread balance"),
    ("/db",          "View Virtual DB"),
    ("/db set",      "Set a DB key"),
    ("/tools",       "List tools"),
    ("/threads",     "List threads"),
    ("/assistants",  "List assistants"),
    ("/switch",      "Switch assistant"),
    ("/create",      "New assistant wizard"),
    ("/buy",         "Purchase threads"),
    ("/clear",       "Clear screen"),
    ("/info",        "Session info"),
]

def _raw_input(prompt, slash_hints=True):
    """Reactive input: shows slash command hints as you type."""
    try:
        import tty, termios
    except ImportError:
        return input(prompt)
    if not sys.stdin.isatty():
        return input(prompt)
    sys.stdout.write(prompt)
    sys.stdout.flush()
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = []
    hint_shown = False
    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch in ('\x03', '\x04'):
                if hint_shown:
                    sys.stdout.write(f'\x1b[B\r\x1b[2K\x1b[A')
                sys.stdout.write('\r\n')
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
                raise EOFError
            if ch in ('\r', '\n'):
                if hint_shown:
                    sys.stdout.write(f'\x1b[B\r\x1b[2K\x1b[A')
                sys.stdout.write('\r\n')
                break
            if ch in ('\x7f', '\x08'):
                if buf:
                    buf.pop()
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            elif ch == '\t':
                text = ''.join(buf)
                if text.startswith('/'):
                    matches = [c for c, _ in SLASH_CMDS if c.startswith(text) and c != text]
                    if matches:
                        rest = matches[0][len(text):]
                        for c2 in rest:
                            buf.append(c2)
                        sys.stdout.write(rest)
                        sys.stdout.flush()
            elif 32 <= ord(ch) < 127:
                buf.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
            else:
                continue
            text = ''.join(buf)
            if slash_hints and text.startswith('/') and len(text) >= 1:
                matches = [(c, d) for c, d in SLASH_CMDS if c.startswith(text)]
                if matches and text not in [c for c, _ in SLASH_CMDS]:
                    hint = "  ".join(f"\x1b[2m{c} {d}\x1b[0m" for c, d in matches[:3])
                    sys.stdout.write(f'\x1b[s\n\r\x1b[2K  {hint}\x1b[u')
                    sys.stdout.flush()
                    hint_shown = True
                elif hint_shown:
                    sys.stdout.write(f'\x1b[s\n\r\x1b[2K\x1b[u')
                    sys.stdout.flush()
                    hint_shown = False
            elif hint_shown:
                sys.stdout.write(f'\x1b[s\n\r\x1b[2K\x1b[u')
                sys.stdout.flush()
                hint_shown = False
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ''.join(buf)

class Spinner:
    """Animated spinner for async operations."""
    def __init__(self, label, style="connecting"):
        s = SPINNERS.get(style, SPINNERS["connecting"])
        self.frames = s["frames"]
        self.color = s["color"]
        self.label = label
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def _spin(self):
        cycle = itertools.cycle(self.frames)
        while not self._stop.is_set():
            frame = next(cycle)
            sys.stdout.write(f"\r  {self.color}{frame}{RESET} {self.label}")
            sys.stdout.flush()
            self._stop.wait(0.15)

    def stop(self, final=""):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        sys.stdout.write(f"\r  {' ' * (len(self.label) + 6)}\r")
        if final:
            sys.stdout.write(f"  {final}\n")
        sys.stdout.flush()

    def __enter__(self):
        return self.start()

    def __exit__(self, *args):
        self.stop()

def _client():
    from .client import EpsimoClient
    from .auth import get_token
    token = get_token()
    if not token:
        return None
    return EpsimoClient(api_key=token)

def _safe(fn, default=None):
    try:
        return fn()
    except Exception as e:
        return default if default is not None else str(e)

class TUI:
    def __init__(self):
        self.client = None
        self.projects = []
        self.proj_idx = 0
        self.cache = {}

    def _clear(self):
        print(CLEAR, end="")

    def _header(self, title):
        self._clear()
        print(f"{CYAN}{BOLD}╔══════════════════════════════════════════════════════╗{RESET}")
        print(f"{CYAN}{BOLD}║  ⚡ Epsimo Dashboard — {title:<30}║{RESET}")
        print(f"{CYAN}{BOLD}╚══════════════════════════════════════════════════════╝{RESET}")
        print()

    def _menu(self, items):
        for i, label in enumerate(items, 1):
            print(f"  {YELLOW}{i}{RESET}) {label}")
        print()

    def _prompt(self, text="Choice"):
        try:
            return input(f"  {GREEN}>{RESET} {text}: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "q"

    def _table(self, headers, rows, max_col=36):
        if not rows:
            print(f"  {DIM}(empty){RESET}")
            return
        widths = [max(len(h), max_col) for h in headers]
        hdr = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
        print(f"  {BOLD}{hdr}{RESET}")
        print(f"  {DIM}{'─' * len(hdr)}{RESET}")
        for row in rows:
            line = "  ".join(str(v)[:w].ljust(w) for v, w in zip(row, widths))
            print(f"  {line}")

    def _pause(self):
        try:
            input(f"\n  {DIM}Press Enter to continue...{RESET}")
        except (EOFError, KeyboardInterrupt):
            pass

    def _cur_pid(self):
        if self.projects:
            return self.projects[self.proj_idx].get("project_id")
        return None

    def _cur_pname(self):
        if self.projects:
            return self.projects[self.proj_idx].get("name", "?")
        return "None"

    def _ensure_project(self):
        """Make sure a project is selected. Returns True if ready, False if user cancelled."""
        if not self.projects:
            self.projects = _safe(lambda: self.client.projects.list(), []) or []
        if not self.projects:
            print(f"  {RED}No projects found. Create one with 'epsimo init'.{RESET}")
            self._pause()
            return False
        if len(self.projects) == 1:
            self.proj_idx = 0
            return True
        # Multiple projects — show picker
        print(f"  {BOLD}Select a project:{RESET}")
        for i, p in enumerate(self.projects, 1):
            marker = f" {GREEN}◀{RESET}" if i - 1 == self.proj_idx else ""
            print(f"  {YELLOW}{i}{RESET}) {p.get('name', '?')}{marker}")
        print()
        c = self._prompt(f"Project # [default={self.proj_idx+1}]")
        if c.isdigit() and 1 <= int(c) <= len(self.projects):
            self.proj_idx = int(c) - 1
        elif c in ("q", "back"):
            return False
        # Clear project-scoped cache on switch
        self.cache.pop("assistants", None)
        self.cache.pop("threads", None)
        return True

    # ── Screens ─────────────────────────────────────────────────────
    def show_status(self):
        self._header("Status")
        sp = Spinner("Fetching account info...", "loading").start()
        info = _safe(lambda: self.client.request("GET", "/auth/thread-info"), {})
        sp.stop(f"{GREEN}✓ Done{RESET}")
        if not isinstance(info, dict):
            info = {}
        email = info.get("email", "Unknown")
        used = info.get("thread_counter", "?")
        total = info.get("thread_max", "?")
        remaining = total - used if isinstance(used, int) and isinstance(total, int) else "?"

        print(f"  {BOLD}Account:{RESET}       {email}")
        print(f"  {BOLD}Threads Used:{RESET}  {used} / {total}")
        print(f"  {BOLD}Remaining:{RESET}     {GREEN}{remaining}{RESET}")
        print(f"  {BOLD}Projects:{RESET}      {len(self.projects)}")
        print(f"  {BOLD}Active:{RESET}        {self._cur_pname()}")
        print(f"  {BOLD}API:{RESET}           {self.client.base_url}")

        print(f"\n  {DIM}Press Enter to go back, or 'b' to buy more threads{RESET}")
        c = self._prompt("Action")
        if c == "b":
            self.buy_credits()

    def buy_credits(self):
        self._header("Buy Threads")
        # Show current balance
        sp = Spinner("Checking balance...", "loading").start()
        bal = _safe(lambda: self.client.credits.get_balance(), {})
        sp.stop(f"{GREEN}✓ Done{RESET}")
        if isinstance(bal, dict):
            used = bal.get("thread_counter", 0)
            total = bal.get("thread_max", 0)
            print(f"  {BOLD}Current:{RESET} {used}/{total}  {BOLD}Remaining:{RESET} {GREEN}{total - used}{RESET}\n")

        # Pricing tiers
        print(f"  {BOLD}Pricing:{RESET}")
        print(f"  {DIM}< 500 threads:    €0.10/thread{RESET}")
        print(f"  {DIM}500-999 threads:  €0.09/thread{RESET}")
        print(f"  {DIM}1000+ threads:    €0.08/thread{RESET}")

        # Quick picks
        print(f"\n  {BOLD}Quick picks:{RESET}")
        picks = [
            (100,  "€10.00"),
            (500,  "€45.00"),
            (1000, "€80.00"),
            (5000, "€400.00"),
        ]
        for i, (qty, price) in enumerate(picks, 1):
            print(f"  {YELLOW}{i}{RESET}) {qty} threads — {price}")
        print(f"  {YELLOW}5{RESET}) Custom amount")
        print()

        c = self._prompt("Choice [1-5]")
        quantity = None
        if c in ("1", "2", "3", "4"):
            quantity = picks[int(c) - 1][0]
        elif c == "5":
            amt = self._prompt("Number of threads")
            if amt.isdigit() and int(amt) > 0:
                quantity = int(amt)

        if not quantity:
            print(f"  {DIM}Cancelled.{RESET}")
            self._pause()
            return

        # Calculate estimated cost
        if quantity >= 1000:
            cost = quantity * 0.08
        elif quantity >= 500:
            cost = quantity * 0.09
        else:
            cost = quantity * 0.10

        print(f"\n  {BOLD}Purchase:{RESET} {quantity} threads")
        print(f"  {BOLD}Estimated:{RESET} €{cost:.2f}")
        try:
            confirm = input(f"\n  {GREEN}>{RESET} Proceed to checkout? (y/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if confirm != "y":
            print(f"  {DIM}Cancelled.{RESET}")
            self._pause()
            return

        sp = Spinner("Creating checkout session...", "connecting").start()
        try:
            result = self.client.credits.create_checkout_session(quantity)
            url = result.get("url", "") if isinstance(result, dict) else ""
            if url:
                sp.stop(f"{GREEN}✓ Checkout ready{RESET}")
                print(f"\n  {BOLD}Complete your purchase here:{RESET}")
                print(f"  {CYAN}{url}{RESET}\n")
            else:
                sp.stop(f"{RED}✗ No checkout URL returned{RESET}")
        except Exception as e:
            sp.stop(f"{RED}✗ Failed: {e}{RESET}")
        self._pause()

    def show_projects(self):
        self._header("Projects")
        self.projects = _safe(lambda: self.client.projects.list(), []) or []
        rows = [[p.get("project_id", "?"), p.get("name", "?")] for p in self.projects]
        self._table(["ID", "Name"], rows)

        if self.projects:
            print(f"\n  {DIM}Enter row number to set as active project, or Enter to go back{RESET}")
            c = self._prompt("Select project #")
            if c.isdigit() and 1 <= int(c) <= len(self.projects):
                self.proj_idx = int(c) - 1
                print(f"\n  {GREEN}✓ Active project: {self._cur_pname()}{RESET}")
                self._pause()

    def show_assistants(self):
        if not self._ensure_project():
            return
        pid = self._cur_pid()
        self._header(f"Assistants — {self._cur_pname()}")
        sp = Spinner("Loading assistants...", "loading").start()
        items = _safe(lambda: self.client.assistants.list(pid), []) or []
        sp.stop(f"{GREEN}✓ {len(items)} assistant(s){RESET}")
        self.cache["assistants"] = items
        rows = [[a.get("assistant_id", "?"), a.get("name", "?")] for a in items]
        self._table(["ID", "Name"], rows)
        if items:
            print(f"\n  {DIM}Press Enter to go back, or 'c' to create a new assistant{RESET}")
            c = self._prompt("Action")
            if c == "c":
                self.create_assistant()
                return
        self._pause()

    # ── Available tool catalog ──────────────────────────────────────
    TOOL_CATALOG = [
        ("search_tavily",              "Search (Tavily)",           "Web search with source attribution"),
        ("search_tavily_answer",       "Search (short answer)",     "Tavily short answer mode"),
        ("ddg_search",                 "DuckDuckGo Search",         "Fast web search via DuckDuckGo"),
        ("arxiv",                      "Arxiv",                     "Search academic papers on Arxiv"),
        ("pubmed",                     "PubMed",                    "Search medical literature"),
        ("wikipedia",                  "Wikipedia",                 "Search Wikipedia articles"),
        ("retrieval",                  "Retrieval",                 "Search uploaded documents"),
        ("dall_e",                     "DALL-E",                    "Generate images from text"),
        ("lead_analysis",              "Lead Analysis",             "Analyze conversation threads"),
        ("custom_search_database",     "Search Database",           "Search customer database"),
        ("custom_web_search",          "Web Search",                "General web search"),
        ("custom_calculator",          "Calculator",                "Arithmetic calculations"),
        ("custom_get_weather",         "Weather",                   "Get current weather & forecast"),
        ("custom_run_code",            "Code Runner",               "Execute code in sandbox"),
        ("custom_summarize_conversation", "Summarize",              "Summarize conversation"),
        ("custom_get_user_preference", "User Preferences",          "Get user preference values"),
        ("custom_update_user_name",    "Update User Name",          "Update user's display name"),
        ("custom_get_account_info",    "Account Info",              "Get account information"),
        ("custom_get_user_info",       "Get User Info",             "Look up user info from storage"),
        ("custom_save_user_info",      "Save User Info",            "Save user info to storage"),
        ("custom_get_weather_with_stream", "Weather (streaming)",   "Weather with streaming output"),
        ("custom_clear_conversation",  "Clear Conversation",        "Clear conversation history"),
        ("custom_create_or_update_crm_contact", "CRM Contact",     "Create/update CRM contacts"),
    ]

    TOOL_PRESETS = {
        "research":  ["search_tavily", "arxiv", "pubmed", "wikipedia", "retrieval"],
        "support":   ["retrieval", "custom_search_database", "custom_get_user_info", "custom_save_user_info", "custom_get_account_info"],
        "creative":  ["dall_e", "search_tavily", "custom_run_code"],
        "sales":     ["search_tavily", "lead_analysis", "custom_create_or_update_crm_contact", "custom_search_database"],
        "code":      ["custom_run_code", "custom_calculator", "search_tavily", "ddg_search"],
        "all":       None,  # handled specially
        "minimal":   ["search_tavily", "retrieval"],
    }

    def create_assistant(self):
        self._header("Create Assistant")
        if not self._ensure_project():
            return
        pid = self._cur_pid()
        print(f"  {DIM}Project: {self._cur_pname()}{RESET}\n")

        # ── Step 1: Name ────────────────────────────────────────────
        print(f"  {BOLD}Step 1/4 — Name{RESET}")
        name = ""
        while not name:
            try:
                name = input(f"  {GREEN}>{RESET} Assistant name: ").strip()
            except (EOFError, KeyboardInterrupt):
                return
            if not name:
                print(f"  {RED}Name is required{RESET}")

        # ── Step 2: Instructions ────────────────────────────────────
        print(f"\n  {BOLD}Step 2/4 — System Instructions{RESET}")
        print(f"  {DIM}Describe the assistant's role and behavior.{RESET}")
        print(f"  {DIM}Enter a single line, or type 'multi' for multi-line (end with empty line).{RESET}")
        try:
            first = input(f"  {GREEN}>{RESET} Instructions: ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if first.lower() == "multi":
            print(f"  {DIM}Enter instructions (empty line to finish):{RESET}")
            lines = []
            while True:
                try:
                    line = input(f"  {DIM}...{RESET} ")
                except (EOFError, KeyboardInterrupt):
                    break
                if not line:
                    break
                lines.append(line)
            instructions = "\n".join(lines)
        else:
            instructions = first
        if not instructions:
            instructions = f"You are {name}, a helpful AI assistant."
            print(f"  {DIM}Using default: \"{instructions}\"{RESET}")

        # ── Step 3: Model ───────────────────────────────────────────
        print(f"\n  {BOLD}Step 3/4 — Model{RESET}")
        model_groups = [
            ("Epsimo", [
                ("Epsimo LLM AI",           "Epsimo default model"),
                ("Epsimo LLM AI (JSON)",    "Structured JSON output"),
                ("Epsimo LLM AI (Small)",   "Fast & lightweight"),
                ("Epsimo LLM AI (Big)",     "Most capable Epsimo model"),
            ]),
            ("OpenAI", [
                ("GPT-5.5",                 "Most capable — agentic coding & professional work"),
                ("GPT-5.4",                 "Frontier model for coding & reasoning"),
                ("GPT-5.4 Mini",            "Fast mini for coding, subagents & computer use"),
                ("GPT-5.4 Nano",            "Cheapest — classification, extraction & subagents"),
                ("GPT-5.1 Reasoning",       "GPT-5.1 with deep reasoning"),
                ("GPT-5.1",                 "GPT-5.1 flagship"),
                ("GPT-5 Mini",              "GPT-5 balanced speed & quality"),
                ("GPT-5 Nano",              "GPT-5 nano — fast & cheap"),
                ("GPT 4o",                  "GPT-4o (default)"),
                ("GPT 4o mini",             "GPT-4o mini — fast & affordable"),
                ("GPT-4.1",                 "GPT-4 Turbo"),
                ("OpenAI GPT-4o Vision",    "GPT-4o with image understanding"),
            ]),
            ("Anthropic", [
                ("Claude 3.7 (Sonnet)",     "Best balance of speed & quality"),
                ("Claude 3.5 (Haiku)",      "Fast & affordable"),
                ("Claude 3 (Opus)",         "Most capable Claude"),
            ]),
            ("Groq", [
                ("Groq Llama 4 Maverick 17B",       "Llama 4 Maverick"),
                ("Groq Llama 4 Scout 17B",          "Llama 4 Scout"),
                ("Groq Qwen3 32B",                  "Qwen3 32B"),
                ("Groq Llama 3.3 70B Versatile",    "Llama 3.3 70B"),
                ("Groq Llama 3.1 8B Instant",       "Ultra-fast 8B"),
                ("Groq Gemma2 9B",                  "Google Gemma2 9B"),
            ]),
            ("DeepSeek", [
                ("DeepSeek",                "DeepSeek V3"),
                ("DeepSeek Reasoner",       "DeepSeek R1 reasoning"),
            ]),
            ("xAI", [
                ("GROK 2",                  "Grok 2"),
                ("GROK 4",                  "Grok 4"),
            ]),
            ("Fireworks", [
                ("Fireworks Llama 4 Maverick Instruct", "Llama 4 Maverick"),
                ("Fireworks Qwen3 235B-A22B",           "Qwen3 235B MoE"),
                ("Fireworks Mistral Small 24B Instruct", "Mistral Small"),
                ("Fireworks FLUX.1 Kontext Pro",         "Image generation"),
            ]),
            ("Other", [
                ("Mixtral",                 "Mixtral MoE"),
            ]),
        ]
        # Flatten for selection
        all_models = []
        idx = 1
        for group_name, group_models in model_groups:
            print(f"\n  {CYAN}{group_name}{RESET}")
            for mname, mdesc in group_models:
                default = " ◀ default" if mname == "GPT 4o" else ""
                print(f"  {YELLOW}{idx:2}{RESET}) {mname:<40} {DIM}{mdesc}{default}{RESET}")
                all_models.append(mname)
                idx += 1
        try:
            default_idx = all_models.index("GPT 4o") + 1 if "GPT 4o" in all_models else 1
            mc = input(f"\n  {GREEN}>{RESET} Model [1-{len(all_models)}, default={default_idx} GPT 4o]: ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if mc.isdigit() and 1 <= int(mc) <= len(all_models):
            model = all_models[int(mc) - 1]
        else:
            model = "GPT 4o"
        print(f"  {DIM}Selected: {model}{RESET}")

        # ── Step 4: Tools ───────────────────────────────────────────
        print(f"\n  {BOLD}Step 4/4 — Tools{RESET}")
        print(f"\n  {BOLD}Presets:{RESET}")
        preset_names = list(self.TOOL_PRESETS.keys())
        for i, p in enumerate(preset_names, 1):
            tools_in = self.TOOL_PRESETS[p]
            desc = ", ".join(tools_in[:3]) + "..." if tools_in and len(tools_in) > 3 else (", ".join(tools_in) if tools_in else "all tools")
            print(f"  {YELLOW}{i}{RESET}) {BOLD}{p}{RESET} — {DIM}{desc}{RESET}")
        print(f"  {YELLOW}{len(preset_names)+1}{RESET}) {BOLD}custom{RESET} — {DIM}pick individual tools{RESET}")
        print(f"  {YELLOW}{len(preset_names)+2}{RESET}) {BOLD}none{RESET} — {DIM}no tools{RESET}")

        try:
            tc = input(f"\n  {GREEN}>{RESET} Tool selection [1-{len(preset_names)+2}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            return

        selected_tools = []
        if tc.isdigit():
            idx = int(tc)
            if 1 <= idx <= len(preset_names):
                preset = preset_names[idx - 1]
                if preset == "all":
                    selected_tools = [t[0] for t in self.TOOL_CATALOG]
                else:
                    selected_tools = self.TOOL_PRESETS[preset]
            elif idx == len(preset_names) + 1:
                # Custom selection
                print(f"\n  {BOLD}Available tools:{RESET} (enter numbers separated by commas)")
                for i, (ttype, tname, tdesc) in enumerate(self.TOOL_CATALOG, 1):
                    print(f"  {YELLOW}{i:2}{RESET}) {tname:<28} {DIM}{tdesc}{RESET}")
                try:
                    picks = input(f"\n  {GREEN}>{RESET} Tools (e.g. 1,3,7): ").strip()
                except (EOFError, KeyboardInterrupt):
                    return
                for p in picks.split(","):
                    p = p.strip()
                    if p.isdigit() and 1 <= int(p) <= len(self.TOOL_CATALOG):
                        selected_tools.append(self.TOOL_CATALOG[int(p) - 1][0])
            # else: none — empty list

        # ── Confirmation ────────────────────────────────────────────
        print(f"\n  {CYAN}{'─' * 50}{RESET}")
        print(f"  {BOLD}Summary:{RESET}")
        print(f"  {BOLD}Name:{RESET}          {name}")
        print(f"  {BOLD}Model:{RESET}         {model}")
        print(f"  {BOLD}Instructions:{RESET}  {instructions[:80]}{'...' if len(instructions) > 80 else ''}")
        print(f"  {BOLD}Tools ({len(selected_tools)}):{RESET}    {', '.join(selected_tools[:5])}{'...' if len(selected_tools) > 5 else ''}")
        print(f"  {CYAN}{'─' * 50}{RESET}")

        try:
            confirm = input(f"\n  {GREEN}>{RESET} Create this assistant? (y/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if confirm != "y":
            print(f"  {DIM}Cancelled.{RESET}")
            self._pause()
            return

        # ── Create ──────────────────────────────────────────────────
        sp = Spinner("Creating assistant...", "connecting").start()
        try:
            result = self.client.assistants.create(
                project_id=pid,
                name=name,
                model=model,
                instructions=instructions,
                tools=selected_tools
            )
            aid = result.get("assistant_id", "?")
            sp.stop(f"{GREEN}✓ Created: {name} ({aid}){RESET}")
            # Refresh cache
            self.cache["assistants"] = _safe(lambda: self.client.assistants.list(pid), []) or []
        except Exception as e:
            sp.stop(f"{RED}✗ Failed: {e}{RESET}")
        self._pause()

    def show_threads(self):
        if not self._ensure_project():
            return
        pid = self._cur_pid()
        self._header(f"Threads — {self._cur_pname()}")
        sp = Spinner("Loading threads...", "loading").start()
        items = _safe(lambda: self.client.threads.list(pid), []) or []
        sp.stop(f"{GREEN}✓ {len(items)} thread(s){RESET}")
        self.cache["threads"] = items
        rows = [[t.get("thread_id", "?"), t.get("name", "?")] for t in items]
        self._table(["ID", "Name"], rows)

        if items:
            print(f"\n  {DIM}Enter row number to view its Virtual Database, or Enter to go back{RESET}")
            c = self._prompt("Select thread #")
            if c.isdigit() and 1 <= int(c) <= len(items):
                tid = items[int(c) - 1].get("thread_id")
                self._show_thread_db(tid)

    def _show_thread_db(self, thread_id):
        pid = self._cur_pid()
        self._header(f"Virtual DB — thread {thread_id[:16]}...")
        state = _safe(lambda: self.client.threads.get_state(pid, thread_id), {})
        values = state.get("values", state) if isinstance(state, dict) else {}
        if not values:
            print(f"  {DIM}(empty — no data stored){RESET}")
        elif isinstance(values, dict):
            for k, v in values.items():
                val = json.dumps(v, indent=2) if isinstance(v, (dict, list)) else str(v)
                print(f"  {YELLOW}{k}{RESET}: {val}")
        else:
            print(f"  {json.dumps(values, indent=2)}")
        self._pause()

    def show_db(self):
        if not self._ensure_project():
            return
        self._header(f"Virtual Database — {self._cur_pname()}")
        threads = self.cache.get("threads")
        if not threads:
            pid = self._cur_pid()
            if pid:
                threads = _safe(lambda: self.client.threads.list(pid), []) or []
                self.cache["threads"] = threads

        if not threads:
            print(f"  {DIM}No threads found. Create one first.{RESET}")
            self._pause()
            return

        rows = [[t.get("thread_id", "?"), t.get("name", "?")] for t in threads]
        self._table(["ID", "Name"], rows)
        print(f"\n  {DIM}Enter row number to query its database{RESET}")
        c = self._prompt("Select thread #")
        if c.isdigit() and 1 <= int(c) <= len(threads):
            tid = threads[int(c) - 1].get("thread_id")
            self._show_thread_db(tid)

    def show_tools(self):
        self._header("Tools")
        sp = Spinner("Loading tools...", "loading").start()
        try:
            tools = self.client.request("GET", "/tools/")
            if isinstance(tools, dict):
                tools = tools.get("tools", [])
            if not isinstance(tools, list):
                tools = []
        except Exception:
            tools = []
        sp.stop(f"{GREEN}✓ {len(tools)} tool(s){RESET}")

        rows = [[t.get("name", "?"), t.get("type", "?"), t.get("description", "?")[:50]] for t in tools]
        self._table(["Name", "Type", "Description"], rows, max_col=25)
        self._pause()

    def show_chat(self):
        if not self._ensure_project():
            return
        pid = self._cur_pid()
        self._header(f"Chat — {self._cur_pname()}")

        # Pick assistant
        assistants = self.cache.get("assistants")
        if not assistants:
            assistants = _safe(lambda: self.client.assistants.list(pid), []) or []
            self.cache["assistants"] = assistants
        if not assistants:
            print(f"  {RED}No assistants found in this project.{RESET}")
            self._pause()
            return

        print(f"  {BOLD}Select an assistant:{RESET}")
        for i, a in enumerate(assistants, 1):
            print(f"  {YELLOW}{i}{RESET}) {a.get('name', '?')}")
        print()
        c = self._prompt("Assistant #")
        if not c.isdigit() or not (1 <= int(c) <= len(assistants)):
            return
        assistant = assistants[int(c) - 1]
        aid = assistant.get("assistant_id")

        # Create thread
        sp = Spinner("Creating chat thread...", "connecting").start()
        try:
            thread = self.client.threads.create(pid, "TUI Chat", aid)
            tid = thread["thread_id"]
            sp.stop(f"{GREEN}✓ Thread ready{RESET}")
        except Exception as e:
            sp.stop(f"{RED}✗ Failed: {e}{RESET}")
            self._pause()
            return

        # Chat loop
        self._header(f"Chat — {assistant.get('name', '?')}")
        print(f"  {DIM}Thread: {tid[:16]}...{RESET}")
        print(f"  {DIM}Type /help for commands, 'exit' to return to menu{RESET}\n")

        while True:
            try:
                user_input = _raw_input(f"  {GREEN}You >{RESET} ")
            except (EOFError, KeyboardInterrupt):
                break
            stripped = user_input.strip()
            if stripped.lower() in ("exit", "quit", "back"):
                break
            if not stripped:
                continue

            # ── Slash commands ──────────────────────────────────────
            if stripped.startswith("/"):
                parts = stripped.split(None, 1)
                cmd = parts[0].lower()
                cmd_arg = parts[1] if len(parts) > 1 else ""

                if cmd == "/help":
                    print(f"\n  {BOLD}Slash Commands:{RESET}")
                    print(f"  {YELLOW}/help{RESET}              Show this help")
                    print(f"  {YELLOW}/status{RESET}            Account info & thread usage")
                    print(f"  {YELLOW}/credits{RESET}           Check thread balance")
                    print(f"  {YELLOW}/db{RESET}                Show Virtual DB for this thread")
                    print(f"  {YELLOW}/db set <k> <v>{RESET}   Set a key in the Virtual DB")
                    print(f"  {YELLOW}/tools{RESET}             List available tools")
                    print(f"  {YELLOW}/threads{RESET}           List threads in current project")
                    print(f"  {YELLOW}/assistants{RESET}        List assistants in current project")
                    print(f"  {YELLOW}/switch{RESET}            Switch to a different assistant")
                    print(f"  {YELLOW}/create{RESET}            Create a new assistant (guided wizard)")
                    print(f"  {YELLOW}/buy{RESET}               Purchase more threads")
                    print(f"  {YELLOW}/clear{RESET}             Clear screen")
                    print(f"  {YELLOW}/info{RESET}              Show current session info")
                    print()

                elif cmd == "/status":
                    info = _safe(lambda: self.client.request("GET", "/auth/thread-info"), {})
                    if isinstance(info, dict):
                        print(f"\n  {BOLD}Account:{RESET}  {info.get('email', 'Unknown')}")
                        print(f"  {BOLD}Threads:{RESET}  {info.get('thread_counter', '?')}/{info.get('thread_max', '?')}\n")

                elif cmd == "/credits":
                    bal = _safe(lambda: self.client.credits.get_balance(), {})
                    if isinstance(bal, dict):
                        used = bal.get("thread_counter", 0)
                        total = bal.get("thread_max", 0)
                        print(f"\n  {BOLD}Threads:{RESET} {used}/{total}  {BOLD}Remaining:{RESET} {GREEN}{total - used}{RESET}\n")

                elif cmd == "/db":
                    if cmd_arg.startswith("set "):
                        # /db set key value
                        kv = cmd_arg[4:].split(None, 1)
                        if len(kv) == 2:
                            key, val = kv
                            try:
                                val = json.loads(val)
                            except (json.JSONDecodeError, ValueError):
                                pass
                            try:
                                self.client.threads.set_state(pid, tid, {key: val})
                                print(f"\n  {GREEN}✓ Set {key}{RESET}\n")
                            except Exception as e:
                                print(f"\n  {RED}Error: {e}{RESET}\n")
                        else:
                            print(f"\n  {DIM}Usage: /db set <key> <value>{RESET}\n")
                    else:
                        state = _safe(lambda: self.client.threads.get_state(pid, tid), {})
                        values = state.get("values", state) if isinstance(state, dict) else {}
                        if not values:
                            print(f"\n  {DIM}(empty){RESET}\n")
                        else:
                            print()
                            for k, v in values.items():
                                val = json.dumps(v, indent=2) if isinstance(v, (dict, list)) else str(v)
                                print(f"  {YELLOW}{k}{RESET}: {val}")
                            print()

                elif cmd == "/tools":
                    try:
                        tools = self.client.request("GET", "/tools/")
                        if isinstance(tools, dict):
                            tools = tools.get("tools", [])
                        if isinstance(tools, list):
                            print()
                            for t in tools:
                                print(f"  {YELLOW}{t.get('name', '?')}{RESET} ({t.get('type', '?')})")
                            print()
                    except Exception:
                        print(f"\n  {RED}Failed to load tools{RESET}\n")

                elif cmd == "/threads":
                    threads = _safe(lambda: self.client.threads.list(pid), []) or []
                    print()
                    for t in threads:
                        marker = " ◀" if t.get("thread_id") == tid else ""
                        print(f"  {t.get('thread_id', '?')[:20]}  {t.get('name', '?')}{GREEN}{marker}{RESET}")
                    print()

                elif cmd == "/assistants":
                    assts = _safe(lambda: self.client.assistants.list(pid), []) or []
                    print()
                    for a in assts:
                        marker = " ◀" if a.get("assistant_id") == aid else ""
                        print(f"  {a.get('assistant_id', '?')[:20]}  {a.get('name', '?')}{GREEN}{marker}{RESET}")
                    print()

                elif cmd == "/switch":
                    assts = _safe(lambda: self.client.assistants.list(pid), []) or []
                    if not assts:
                        print(f"\n  {RED}No assistants found{RESET}\n")
                        continue
                    print()
                    for i, a in enumerate(assts, 1):
                        marker = " ◀" if a.get("assistant_id") == aid else ""
                        print(f"  {YELLOW}{i}{RESET}) {a.get('name', '?')}{GREEN}{marker}{RESET}")
                    print()
                    sc = self._prompt("Switch to #")
                    if sc.isdigit() and 1 <= int(sc) <= len(assts):
                        new_asst = assts[int(sc) - 1]
                        aid = new_asst.get("assistant_id")
                        assistant = new_asst
                        print(f"\n  {GREEN}✓ Switched to {new_asst.get('name', '?')}{RESET}\n")

                elif cmd == "/clear":
                    self._header(f"Chat — {assistant.get('name', '?')}")
                    print(f"  {DIM}Thread: {tid[:16]}... | /help for commands{RESET}\n")

                elif cmd == "/info":
                    print(f"\n  {BOLD}Project:{RESET}    {self._cur_pname()} ({pid[:16]}...)")
                    print(f"  {BOLD}Assistant:{RESET}  {assistant.get('name', '?')} ({aid[:16]}...)")
                    print(f"  {BOLD}Thread:{RESET}     {tid[:16]}...")
                    print(f"  {BOLD}API:{RESET}        {self.client.base_url}\n")

                elif cmd == "/create":
                    self.create_assistant()
                    # Refresh assistants cache
                    self.cache["assistants"] = _safe(lambda: self.client.assistants.list(pid), []) or []
                    print(f"  {DIM}Back to chat. Type /switch to use the new assistant.{RESET}\n")

                elif cmd == "/buy":
                    self.buy_credits()

                else:
                    print(f"\n  {DIM}Unknown command. Type /help for available commands.{RESET}\n")
                continue

            print(f"  {CYAN}Bot >{RESET} ", end="", flush=True)
            try:
                last_len = 0
                thinking_sp = Spinner("Thinking...", "thinking").start()
                first_content = True
                for chunk in self.client.threads.run_stream(
                    project_id=pid,
                    thread_id=tid,
                    assistant_id=aid,
                    message=user_input
                ):
                    if not isinstance(chunk, list):
                        # Single dict from SSE
                        if isinstance(chunk, dict):
                            event = chunk.get("_event", "")
                            # Handle messages stream
                            if isinstance(chunk, list) and len(chunk) == 1:
                                chunk = chunk[0]
                            if isinstance(chunk, dict):
                                content = chunk.get("content", "")
                                msg_type = chunk.get("type", "")
                                # Tool calls
                                tool_calls = chunk.get("tool_calls", [])
                                if tool_calls:
                                    if thinking_sp:
                                        thinking_sp.stop()
                                        thinking_sp = None
                                    for tc in tool_calls:
                                        name = tc.get("name", "")
                                        if name:
                                            sys.stdout.write(f"\r  {YELLOW}⚙️  Calling {name}...{RESET}\n")
                                            sys.stdout.flush()
                                    continue
                                if msg_type == "tool":
                                    continue
                                if content and isinstance(content, str) and msg_type in ("ai", "AIMessageChunk", ""):
                                    if first_content and thinking_sp:
                                        thinking_sp.stop()
                                        thinking_sp = None
                                        sys.stdout.write(f"  {CYAN}Bot >{RESET} ")
                                        first_content = False
                                    new = content[last_len:]
                                    if new:
                                        sys.stdout.write(new)
                                        sys.stdout.flush()
                                        last_len = len(content)
                        continue

                    # List format (legacy)
                    if len(chunk) == 1:
                        item = chunk[0]
                        if isinstance(item, dict):
                            content = item.get("content", "")
                            msg_type = item.get("type", "")
                            tool_calls = item.get("tool_calls", [])
                            if tool_calls:
                                if thinking_sp:
                                    thinking_sp.stop()
                                    thinking_sp = None
                                for tc in tool_calls:
                                    name = tc.get("name", "")
                                    if name:
                                        sys.stdout.write(f"\r  {YELLOW}⚙️  Calling {name}...{RESET}\n")
                                        sys.stdout.flush()
                                continue
                            if msg_type == "tool":
                                continue
                            if content and isinstance(content, str):
                                if first_content and thinking_sp:
                                    thinking_sp.stop()
                                    thinking_sp = None
                                    sys.stdout.write(f"  {CYAN}Bot >{RESET} ")
                                    first_content = False
                                new = content[last_len:]
                                if new:
                                    sys.stdout.write(new)
                                    sys.stdout.flush()
                                    last_len = len(content)
                print("\n")
            except Exception as e:
                if thinking_sp:
                    thinking_sp.stop()
                print(f"\n  {RED}Error: {e}{RESET}\n")

    # ── Main loop ───────────────────────────────────────────────────
    def run(self):
        print(f"\n  {CYAN}Connecting to Epsimo...{RESET}")
        self.client = _client()
        if not self.client:
            print(f"  {RED}❌ Not authenticated. Run 'epsimo auth' first.{RESET}")
            return

        sp = Spinner("Connecting to Epsimo...", "connecting").start()
        self.projects = _safe(lambda: self.client.projects.list(), []) or []
        if len(self.projects) == 1:
            self.proj_idx = 0
            sp.stop(f"{GREEN}✓ Connected — Project: {self._cur_pname()}{RESET}")
        elif len(self.projects) > 1:
            sp.stop(f"{GREEN}✓ Connected — {len(self.projects)} projects found{RESET}")
        else:
            sp.stop(f"{YELLOW}⚠ Connected — no projects found{RESET}")

        while True:
            self._header("Main Menu")
            print(f"  {DIM}Active project: {BOLD}{self._cur_pname()}{RESET}")
            print()
            self._menu([
                "Status        — Account info & thread usage",
                "Projects      — List & switch projects",
                "Assistants    — AI agents in current project",
                "Threads       — Conversations in current project",
                "Virtual DB    — Query thread state / data",
                "Tools         — Available backend tools",
                "Chat          — Start a conversation with an assistant",
                "New Assistant — Create an assistant (guided wizard)",
                "Buy Threads  — Purchase additional thread credits",
            ])
            print(f"  {DIM}q) Quit{RESET}")
            print()

            c = self._prompt("Choice [1-9, q]")

            if c in ("q", "quit", "exit"):
                print(f"\n  {CYAN}Goodbye! 👋{RESET}\n")
                break
            elif c == "1":
                self.show_status()
            elif c == "2":
                self.show_projects()
            elif c == "3":
                self.show_assistants()
            elif c == "4":
                self.show_threads()
            elif c == "5":
                self.show_db()
            elif c == "6":
                self.show_tools()
            elif c == "7":
                self.show_chat()
            elif c == "8":
                self.create_assistant()
            elif c == "9":
                self.buy_credits()


def cmd_tui(args):
    """Launch the Epsimo terminal dashboard."""
    try:
        TUI().run()
    except KeyboardInterrupt:
        print(f"\n\n  {CYAN}Goodbye! 👋{RESET}\n")
