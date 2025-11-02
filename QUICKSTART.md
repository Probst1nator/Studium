# Quick Start Guide

Get your StudOn materials syncing automatically in 5 minutes!

## Prerequisites

- Firefox browser (logged into StudOn)
- Python 3.8 or higher
- Linux or macOS (Windows users: use WSL)

## Installation (3 Steps)

### 1. Install Python Dependencies

```bash
pip install requests beautifulsoup4 pyperclip browser-cookie3
```

Optional (for 7z support):
```bash
pip install py7zr
```

### 2. Clone or Download This Repository

**If using git:**
```bash
cd ~/Studium  # Or wherever you want to store course materials
git clone <repository-url> .
```

**Or download manually:**
1. Download the ZIP file
2. Extract to your preferred location (e.g., ~/Studium)

### 3. Run Setup Script

```bash
cd ~/Studium  # Go to where you extracted/cloned the repo
bash setup_daily_sync.sh
```

Follow the prompts. That's it!

## First Sync

Download your first course:

```bash
# Copy a course URL from StudOn, then run:
python3 studon_scraper.py

# Or pass the URL directly:
python3 studon_scraper.py "https://www.studon.fau.de/..."
```

The course will be downloaded to `studon_downloads/Course Name/`

## What Happens Next?

1. **On Login**: Script starts in background
2. **Waits for Firefox**: Checks every 5 minutes
3. **Syncs Once Daily**: Downloads new files from all courses
4. **Exits**: Waits until tomorrow

## Viewing Logs

```bash
# See what's happening (run from the Studium folder)
tail -f studon_sync.log

# Or check the latest entries
tail -50 studon_sync.log
```

## Common Commands

```bash
# Update all courses now
python3 studon_scraper.py --update-all

# Force sync (ignore time restrictions)
python3 studon_auto_updater.py --once --force

# Add a new course
python3 studon_scraper.py "https://studon.fau.de/..."

# Check if cron job is installed
crontab -l | grep studon
```

## Troubleshooting

### No files downloading?

1. Make sure you're logged into StudOn in Firefox
2. Visit the course page in Firefox to verify access
3. Check logs: `tail -f studon_sync.log`

### Cron job not running?

```bash
# Check if it's installed
crontab -l

# Re-run setup
bash setup_daily_sync.sh
```

### Need to remove it?

```bash
# Remove cron job
crontab -e
# Delete the line starting with @reboot

# Or remove everything
crontab -r
```

## Multiple Devices

If you use a cloud sync service (OneDrive, Dropbox, Google Drive, etc.):

1. Set up on first device using steps above
2. Wait for the folder to sync to second device
3. On second device: copy `.env.example` to `.env` and run `bash setup_daily_sync.sh`
4. Each device syncs independently
5. State is shared via cloud sync (won't re-download on same day)

## For KI-Materialtechnologie Students

### Recommended First-Time Setup

```bash
# 1. Install everything
pip install requests beautifulsoup4 pyperclip browser-cookie3 py7zr

# 2. Run setup
bash setup_daily_sync.sh

# 3. Add all your courses (example)
python3 studon_scraper.py "https://www.studon.fau.de/.../Charakterisierung"
python3 studon_scraper.py "https://www.studon.fau.de/.../Simulationsverfahren"
python3 studon_scraper.py "https://www.studon.fau.de/.../Mechanische-Eigenschaften"
# etc...

# 4. From now on, updates happen automatically!
```

### Semester Start Checklist

- [ ] Log into StudOn and enroll in new courses
- [ ] Run: `python3 studon_scraper.py --update-all --force`
- [ ] Check that all courses downloaded
- [ ] Done! Daily sync handles the rest

## Need More Help?

- See full documentation: [README.md](README.md)
- Check logs for errors: `studon_sync.log`
- Open an issue on GitHub

---

**Happy studying!** 📚
