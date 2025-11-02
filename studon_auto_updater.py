#!/usr/bin/env python3
"""
StudOn Auto-Updater
Periodically checks for Firefox and updates all StudOn courses when available.
"""

import os
import sys
import time
import subprocess
import datetime
import json
from pathlib import Path

# --- CONFIGURATION ---
CHECK_INTERVAL_MINUTES = 60  # How often to check (in minutes)
SCRAPER_SCRIPT = os.path.join(os.path.dirname(__file__), "studon_scraper.py")
STATE_FILE = os.path.join(os.path.dirname(__file__), ".studon_updater_state.json")
MIN_TIME_BETWEEN_UPDATES_HOURS = 6  # Don't update more frequently than this

def is_firefox_running() -> bool:
    """Check if Firefox is currently running."""
    try:
        # Use pgrep to check for firefox process
        result = subprocess.run(['pgrep', '-x', 'firefox'],
                              capture_output=True,
                              text=True)
        return result.returncode == 0
    except FileNotFoundError:
        # pgrep not available, try ps
        try:
            result = subprocess.run(['ps', 'aux'],
                                  capture_output=True,
                                  text=True)
            return 'firefox' in result.stdout.lower()
        except Exception as e:
            print(f"Warning: Could not check for Firefox process: {e}")
            return False

def load_state() -> dict:
    """Load the last update timestamp from state file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load state file: {e}")
    return {}

def save_state(state: dict) -> None:
    """Save the last update timestamp to state file."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save state file: {e}")

def should_update(state: dict) -> bool:
    """Check if enough time has passed since last update."""
    last_update = state.get('last_update')
    if not last_update:
        return True

    last_update_time = datetime.datetime.fromisoformat(last_update)
    time_since_update = datetime.datetime.now() - last_update_time
    min_interval = datetime.timedelta(hours=MIN_TIME_BETWEEN_UPDATES_HOURS)

    return time_since_update >= min_interval

def was_updated_today(state: dict) -> bool:
    """Check if an update was already performed today."""
    last_update = state.get('last_update')
    if not last_update:
        return False

    last_update_time = datetime.datetime.fromisoformat(last_update)
    today = datetime.datetime.now().date()
    last_update_date = last_update_time.date()

    return last_update_date == today

def run_updater() -> bool:
    """Run the StudOn scraper in update-all mode. Returns True if successful."""
    try:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running StudOn updater...")
        result = subprocess.run([sys.executable, SCRAPER_SCRIPT, '--update-all'],
                              capture_output=False,
                              text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running updater: {e}")
        return False

def run_once() -> None:
    """Run one update check cycle."""
    state = load_state()

    if not is_firefox_running():
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Firefox not running, skipping update.")
        return

    if not should_update(state):
        last_update = state.get('last_update', 'unknown')
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Updated recently (last: {last_update}), skipping.")
        return

    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Firefox is running and update is due.")

    if run_updater():
        state['last_update'] = datetime.datetime.now().isoformat()
        state['last_success'] = True
        save_state(state)
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Update completed successfully.")
    else:
        state['last_success'] = False
        save_state(state)
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Update failed.")

def run_daemon() -> None:
    """Run continuously, checking periodically."""
    print(f"StudOn Auto-Updater started")
    print(f"  Check interval: {CHECK_INTERVAL_MINUTES} minutes")
    print(f"  Min time between updates: {MIN_TIME_BETWEEN_UPDATES_HOURS} hours")
    print(f"  Scraper script: {SCRAPER_SCRIPT}")
    print()

    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            print("\nShutting down...")
            break
        except Exception as e:
            print(f"Error in update cycle: {e}")

        print(f"Next check in {CHECK_INTERVAL_MINUTES} minutes...")
        time.sleep(CHECK_INTERVAL_MINUTES * 60)

def run_daily_sync(check_interval_seconds: int = 300) -> None:
    """
    Run until a daily sync is performed, then exit.
    Waits for Firefox to be available and performs sync once per day.

    Args:
        check_interval_seconds: How often to check for Firefox (default: 5 minutes)
    """
    state = load_state()

    # Check if already updated today
    if was_updated_today(state):
        last_update = state.get('last_update', 'unknown')
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Already updated today at {last_update}")
        print("Exiting.")
        return

    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Daily sync mode started")
    print(f"  Will check for Firefox every {check_interval_seconds // 60} minutes")
    print(f"  Will exit after successful daily sync")
    print()

    while True:
        try:
            if not is_firefox_running():
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Waiting for Firefox...")
                time.sleep(check_interval_seconds)
                continue

            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Firefox detected, starting sync...")

            if run_updater():
                state['last_update'] = datetime.datetime.now().isoformat()
                state['last_success'] = True
                save_state(state)
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Daily sync completed successfully!")
                print("Exiting.")
                return
            else:
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sync failed, will retry when Firefox is available again...")
                # Wait a bit before retrying
                time.sleep(check_interval_seconds)

        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting.")
            return
        except Exception as e:
            print(f"Error during daily sync: {e}")
            time.sleep(check_interval_seconds)

def main():
    import argparse
    global CHECK_INTERVAL_MINUTES, MIN_TIME_BETWEEN_UPDATES_HOURS

    parser = argparse.ArgumentParser(description='StudOn Auto-Updater')
    parser.add_argument('--daemon', '-d', action='store_true',
                       help='Run as a daemon (continuous loop)')
    parser.add_argument('--once', '-1', action='store_true',
                       help='Run once and exit (useful for cron)')
    parser.add_argument('--daily-sync', action='store_true',
                       help='Wait for Firefox and perform daily sync, then exit (for @reboot cron)')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force update regardless of time since last update')
    parser.add_argument('--interval', '-i', type=int,
                       help=f'Check interval in minutes (default: {CHECK_INTERVAL_MINUTES})')
    parser.add_argument('--min-hours', '-m', type=int,
                       help=f'Minimum hours between updates (default: {MIN_TIME_BETWEEN_UPDATES_HOURS})')

    args = parser.parse_args()

    # Apply configuration
    if args.interval:
        CHECK_INTERVAL_MINUTES = args.interval
    if args.min_hours:
        MIN_TIME_BETWEEN_UPDATES_HOURS = args.min_hours

    # Force update by clearing last update time
    if args.force:
        state = load_state()
        state['last_update'] = None
        save_state(state)
        print("Forced update mode enabled.")

    if args.daily_sync:
        # Use interval setting for check frequency (convert to seconds)
        check_interval = CHECK_INTERVAL_MINUTES * 60
        run_daily_sync(check_interval_seconds=check_interval)
    elif args.once:
        run_once()
    elif args.daemon:
        run_daemon()
    else:
        # Default: show status and options
        print("StudOn Auto-Updater")
        print("\nUsage:")
        print("  --daily-sync     Run on login, wait for Firefox, sync once daily, then exit")
        print("  --daemon, -d     Run continuously in background")
        print("  --once, -1       Run once and exit (for cron)")
        print("  --force, -f      Force update ignoring time checks")
        print("  --interval, -i   Set check interval in minutes")
        print("  --min-hours, -m  Set minimum hours between updates")
        print("\nExamples:")
        print("  # Daily sync on user login (recommended):")
        print("  python studon_auto_updater.py --daily-sync")
        print()
        print("  # Run once now:")
        print("  python studon_auto_updater.py --once")
        print()
        print("  # Run as daemon checking every 30 minutes:")
        print("  python studon_auto_updater.py --daemon --interval 30")
        print()
        print("  # Add to crontab for daily sync on reboot/login:")
        print("  @reboot cd /path/to/your/studium/folder && python3 studon_auto_updater.py --daily-sync --interval 5")
        print()

        # Show current state
        state = load_state()
        if state.get('last_update'):
            print(f"\nLast update: {state['last_update']}")
            print(f"Last success: {state.get('last_success', 'unknown')}")
        else:
            print("\nNo updates recorded yet.")

        print(f"\nFirefox currently running: {'Yes' if is_firefox_running() else 'No'}")

if __name__ == "__main__":
    main()
