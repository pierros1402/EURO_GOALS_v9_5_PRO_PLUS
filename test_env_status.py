# ============================================================
# EURO_GOALS PRO+ — ENVIRONMENT STATUS TEST (v9.6.8)
# ============================================================

import os
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# ------------------------------------------------------------
# Φόρτωση .env
# ------------------------------------------------------------
load_dotenv()
console = Console()

# ------------------------------------------------------------
# Λίστα σημαντικών μεταβλητών
# ------------------------------------------------------------
REQUIRED_VARS = [
    "SPORTMONKS_API_KEY",
    "THESPORTSDB_API_KEY",
    "LIVE_PROXY_URL",
    "IS_DEV",
    "TIMEZONE",
    "APP_NAME",
    "APP_VERSION",
]

OPTIONAL_VARS = [
    "SOFASCORE_API_KEY",
    "DATABASE_URL",
    "CACHE_TTL",
    "AUTO_REFRESH_INTERVAL",
    "THEME_COLOR"
]

# ------------------------------------------------------------
# Συνάρτηση ελέγχου
# ------------------------------------------------------------
def check_env_vars(var_list, required=True):
    missing = []
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Variable")
    table.add_column("Status")
    table.add_column("Value", overflow="fold")

    for var in var_list:
        val = os.getenv(var)
        if val is None or val.strip() == "":
            table.add_row(var, "[red]❌ Missing[/red]", "-")
            missing.append(var)
        else:
            preview = val if len(val) < 40 else val[:37] + "..."
            table.add_row(var, "[green]✅ OK[/green]", preview)

    console.print(table)
    if missing:
        kind = "REQUIRED" if required else "OPTIONAL"
        console.print(f"[bold red]⚠ {len(missing)} {kind} variables missing: {missing}[/bold red]")
    else:
        console.print("[bold green]✅ All variables present.[/bold green]")
    console.print()

# ------------------------------------------------------------
# Εκτέλεση
# ------------------------------------------------------------
console.print("\n[bold cyan]=== EURO_GOALS PRO+ ENVIRONMENT CHECK ===[/bold cyan]\n")

console.print("[yellow]Checking required environment variables...[/yellow]")
check_env_vars(REQUIRED_VARS, required=True)

console.print("[yellow]Checking optional environment variables...[/yellow]")
check_env_vars(OPTIONAL_VARS, required=False)

console.print("[bold cyan]=== ENV CHECK COMPLETE ===[/bold cyan]\n")
