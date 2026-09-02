#!/usr/bin/env python3
"""
validate_orchestrator_setup.py

Validates that the external orchestrator is properly configured and ready to run.
Checks for required dependencies, environment variables, config files, and API access.

USAGE:
  ./scripts/validate_orchestrator_setup.py [--verbose]
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Tuple, List

REPO_DIR = Path(__file__).parent.parent
DATA_DIR = REPO_DIR / "data"
SCRIPTS_DIR = REPO_DIR / "scripts"

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_check(name: str, passed: bool, details: str = ""):
    """Print a check result."""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    message = f"{status} {name}"
    if details:
        message += f" — {details}"
    print(message)


def check_system_dependencies() -> Tuple[bool, List[str]]:
    """Check if required system binaries are available."""
    print(f"\n{BOLD}System Dependencies{RESET}")

    passed = True
    issues = []

    # Check FFmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5,
            text=True
        )
        if result.returncode == 0:
            version_line = result.stdout.split("\n")[0]
            print_check("FFmpeg", True, version_line)
        else:
            print_check("FFmpeg", False, "Exit code non-zero")
            passed = False
            issues.append("FFmpeg check failed")
    except FileNotFoundError:
        print_check("FFmpeg", False, "Not found in PATH")
        passed = False
        issues.append("FFmpeg not installed (sudo apt-get install ffmpeg)")
    except Exception as e:
        print_check("FFmpeg", False, str(e))
        passed = False
        issues.append(f"FFmpeg error: {e}")

    return passed, issues


def check_python_dependencies() -> Tuple[bool, List[str]]:
    """Check if required Python packages are available."""
    print(f"\n{BOLD}Python Dependencies{RESET}")

    passed = True
    issues = []
    required_packages = ["requests"]

    for package in required_packages:
        try:
            __import__(package)
            print_check(f"Python: {package}", True)
        except ImportError:
            print_check(f"Python: {package}", False, "Not installed")
            passed = False
            issues.append(f"Install with: pip install {package}")

    return passed, issues


def check_config_files() -> Tuple[bool, List[str]]:
    """Check if required config files exist and are valid JSON."""
    print(f"\n{BOLD}Configuration Files{RESET}")

    passed = True
    issues = []
    config_files = {
        "Brand Config": DATA_DIR / "brand-config.json",
        "Orchestrator Config": DATA_DIR / "orchestrator-config.json",
    }

    for name, path in config_files.items():
        if not path.exists():
            print_check(name, False, f"Not found at {path}")
            passed = False
            issues.append(f"Missing: {path}")
        else:
            try:
                with open(path) as f:
                    json.load(f)
                print_check(name, True, f"Valid JSON ({path.stat().st_size:,} bytes)")
            except json.JSONDecodeError as e:
                print_check(name, False, f"Invalid JSON: {e}")
                passed = False
                issues.append(f"Fix JSON in {path}")

    return passed, issues


def check_orchestrator_script() -> Tuple[bool, List[str]]:
    """Check if orchestrator script exists and is executable."""
    print(f"\n{BOLD}Orchestrator Script{RESET}")

    passed = True
    issues = []
    script_path = SCRIPTS_DIR / "external_youtube_orchestrator.py"

    if not script_path.exists():
        print_check("Script exists", False, f"Not found at {script_path}")
        passed = False
        issues.append(f"Missing script: {script_path}")
        return passed, issues

    print_check("Script exists", True, str(script_path))

    # Check if executable
    if os.access(script_path, os.X_OK):
        print_check("Script executable", True)
    else:
        print_check("Script executable", False, "Not marked as executable")
        issues.append(f"Run: chmod +x {script_path}")

    # Check syntax
    try:
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(script_path)],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print_check("Script syntax", True, "Valid Python 3")
        else:
            print_check("Script syntax", False, result.stderr.decode())
            passed = False
            issues.append("Fix syntax errors in orchestrator script")
    except Exception as e:
        print_check("Script syntax", False, str(e))
        passed = False

    return passed, issues


def check_environment_variables() -> Tuple[bool, List[str]]:
    """Check if required environment variables are set."""
    print(f"\n{BOLD}Environment Variables{RESET}")

    passed = True
    issues = []

    # Higgsfield API Key (required)
    if os.getenv("HIGGSFIELD_API_KEY"):
        key = os.getenv("HIGGSFIELD_API_KEY")
        masked_key = f"{key[:20]}..." if len(key) > 20 else key
        print_check("HIGGSFIELD_API_KEY", True, f"Set to: {masked_key}")
    else:
        print_check("HIGGSFIELD_API_KEY", False, "Not set")
        issues.append("Set: export HIGGSFIELD_API_KEY='your-api-key'")

    # YouTube Credentials (optional for now)
    if os.getenv("YOUTUBE_CREDENTIALS"):
        creds_path = os.getenv("YOUTUBE_CREDENTIALS")
        if Path(creds_path).exists():
            print_check("YOUTUBE_CREDENTIALS", True, f"File exists: {creds_path}")
        else:
            print_check("YOUTUBE_CREDENTIALS", False, f"File not found: {creds_path}")
            issues.append(f"Create or fix path: {creds_path}")
    else:
        print_check("YOUTUBE_CREDENTIALS", False, "Not set (optional for testing)")
        issues.append("Set for YouTube uploads: export YOUTUBE_CREDENTIALS='/path/to/service-account.json'")

    if os.getenv("HIGGSFIELD_API_KEY"):
        passed = True  # Only require Higgsfield key
    else:
        passed = False

    return passed, issues


def check_config_structure() -> Tuple[bool, List[str]]:
    """Verify config files have required sections."""
    print(f"\n{BOLD}Configuration Structure{RESET}")

    passed = True
    issues = []

    try:
        with open(DATA_DIR / "orchestrator-config.json") as f:
            orch_cfg = json.load(f)

        # Check required sections
        required_sections = {
            "schedule": "Time slot definitions",
            "revitalize_rotation": "Revitalize daily rotation",
            "reclaim_rotation": "Reclaim daily rotation",
            "higgsfield": "Higgsfield image prompts",
            "composio": "YouTube channel config",
        }

        for section, description in required_sections.items():
            if section in orch_cfg:
                print_check(f"Config: {section}", True, description)
            else:
                print_check(f"Config: {section}", False, f"Missing from orchestrator-config.json")
                passed = False
                issues.append(f"Add '{section}' section to orchestrator-config.json")

        # Check YouTube channel IDs
        try:
            rev_yt_id = orch_cfg["composio"]["revitalize"]["yt_channel_id"]
            rec_yt_id = orch_cfg["composio"]["reclaim"]["yt_channel_id"]
            print_check("YouTube channels", True, f"Revitalize: {rev_yt_id}, Reclaim: {rec_yt_id}")
        except KeyError as e:
            print_check("YouTube channels", False, f"Missing: {e}")
            passed = False
            issues.append("Configure YouTube channel IDs in orchestrator-config.json")

    except Exception as e:
        print_check("Config structure", False, str(e))
        passed = False
        issues.append("Fix orchestrator-config.json")

    return passed, issues


def check_log_file() -> Tuple[bool, List[str]]:
    """Check if log file exists and is valid."""
    print(f"\n{BOLD}Orchestrator Log{RESET}")

    passed = True
    issues = []
    log_path = DATA_DIR / "orchestrator-log.json"

    if log_path.exists():
        try:
            with open(log_path) as f:
                log = json.load(f)
            num_entries = len(log)
            print_check("Log file", True, f"{num_entries} entries")
        except json.JSONDecodeError as e:
            print_check("Log file", False, f"Invalid JSON: {e}")
            passed = False
            issues.append(f"Repair or delete: {log_path}")
    else:
        print_check("Log file", False, "Not found (will be created on first run)")
        # Not a hard requirement — will be created

    return passed, issues


def print_summary(all_checks: List[Tuple[bool, List[str]]]):
    """Print summary of all checks."""
    print(f"\n{BOLD}{'='*70}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*70}{RESET}\n")

    all_passed = all(passed for passed, _ in all_checks)
    total_issues = sum(len(issues) for _, issues in all_checks)

    if all_passed:
        print(f"{GREEN}{BOLD}✓ All checks passed!{RESET}")
        print(f"The orchestrator is ready to run.\n")
        print("Quick start:")
        print("  1. Set HIGGSFIELD_API_KEY: export HIGGSFIELD_API_KEY='your-key'")
        print("  2. Test: ./scripts/external_youtube_orchestrator.py morning")
        print("  3. Deploy via cron (see ORCHESTRATOR_SETUP.md)\n")
    else:
        print(f"{RED}{BOLD}✗ {total_issues} issue(s) found{RESET}\n")
        print("Issues to fix:")
        for _, issues in all_checks:
            for issue in issues:
                print(f"  • {issue}")
        print()


def main():
    verbose = "--verbose" in sys.argv

    print(f"\n{BOLD}ORCHESTRATOR SETUP VALIDATOR{RESET}")
    print("Checking configuration and dependencies...\n")

    checks = [
        check_system_dependencies(),
        check_python_dependencies(),
        check_config_files(),
        check_orchestrator_script(),
        check_environment_variables(),
        check_config_structure(),
        check_log_file(),
    ]

    print_summary(checks)

    # Exit with error if any critical checks failed
    if not all(passed for passed, _ in checks):
        sys.exit(1)


if __name__ == "__main__":
    main()
