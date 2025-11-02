# StudOn Auto-Downloader

Automated downloader for StudOn course materials at FAU (Friedrich-Alexander-Universität Erlangen-Nürnberg). Perfect for KI-Materialtechnologie students and anyone who wants to keep their course materials synchronized automatically.

## Features

- 🔄 **Automatic Updates**: Syncs all your StudOn courses automatically
- 📁 **Smart File Management**: Only downloads new files, never overwrites existing ones
- 🗂️ **Organized Structure**: Maintains the same folder structure as StudOn
- 📦 **Archive Extraction**: Automatically extracts `.zip`, `.7z`, `.tar`, `.tar.gz` files
- 🍪 **Browser Cookie Authentication**: Uses Firefox cookies for authentication
- ⏰ **Daily Auto-Sync**: Runs once per day on user login
- 🚀 **Firefox Detection**: Waits for Firefox to be available before syncing

## How It Works

```
User Login → Script Starts → Waits for Firefox → Syncs All Courses → Exits
                                    ↓
                          (Only if not synced today)
```

## Installation

### Platform Compatibility

**Tested on:** [Kubuntu Linux](https://kubuntu.org/) (Ubuntu with KDE Plasma desktop)

**Should work on:** Windows, macOS, other Linux distributions (untested but theoretically compatible)

**Note:** The automatic daily sync feature (cron-based) is designed for Linux/Unix systems. Windows users may need to use Task Scheduler or alternative scheduling methods.

**New to Linux?** Check out [Kubuntu](https://kubuntu.org/getkubuntu/) - it's open-source, user-friendly, and provides a well featured kde desktop environment!

### Prerequisites

1. **Firefox Browser** - Must be logged into StudOn
2. **Python 3.8+**
3. **Required Python packages**:

```bash
pip install requests beautifulsoup4 pyperclip browser-cookie3
```

Optional (for 7z support):
```bash
pip install py7zr
```

### Quick Setup

1. Clone or download this repository to your preferred location:
```bash
cd ~/Studium  # Or wherever you want to store course materials
git clone <repository-url> .
```

2. Run the setup script:
```bash
bash setup_daily_sync.sh
```

3. That's it! The script will now run automatically when you log in.

### Manual Setup

If you prefer to set up manually, add this to your crontab:

```bash
# Edit crontab
crontab -e

# Add this line:
@reboot cd /path/to/Studium && /usr/bin/python3 studon_auto_updater.py --daily-sync --interval 5 >> studon_sync.log 2>&1
```

**Important**: Replace `/path/to/Studium` with your actual path.

## Usage

### First Time Setup

1. Make sure you're logged into StudOn in Firefox
2. Run the scraper manually to download your first course:

```bash
python studon_scraper.py
```

Paste a StudOn course URL when prompted, or copy it to clipboard first.

### Automatic Daily Sync

Once you've run the setup script, the sync happens automatically:

1. Log in to your computer
2. Open Firefox (when convenient)
3. The script detects Firefox and syncs all courses
4. New files are downloaded automatically
5. The script exits until tomorrow

### Manual Operations

**Download a specific course:**
```bash
python studon_scraper.py "https://www.studon.fau.de/..."
```

**Update all courses now:**
```bash
python studon_scraper.py --update-all
```

**Force update (ignore time restrictions):**
```bash
python studon_auto_updater.py --once --force
```

**View sync logs:**
```bash
tail -f studon_sync.log
```

## File Structure

```
Studium/
├── studon_scraper.py              # Main scraper script
├── studon_auto_updater.py         # Auto-update scheduler
├── setup_daily_sync.sh            # Setup script for cron
├── .env.example                   # Example environment configuration
├── .env                           # Your local configuration (create from .env.example)
├── .studon_updater_state.json     # State file (synced across devices)
├── studon_sync.log                # Sync logs
├── studon_downloads/              # Downloaded course materials
│   ├── Course Name 1/
│   │   ├── METADATA.md            # Course info and source URL
│   │   ├── Lecture 1/
│   │   └── Lecture 2/
│   └── Course Name 2/
│       ├── METADATA.md
│       └── ...
└── README.md                      # This file
```

## Multi-Device Setup

If you store this folder in a cloud sync service (Syncthing, OneDrive, Dropbox, Google Drive, etc.), the state and downloaded files can sync across devices automatically.

### On Each Device:

1. Wait for your cloud service to sync the folder
2. Copy `.env.example` to `.env` and adjust paths if needed
3. Run `bash setup_daily_sync.sh` on each device
4. Each device will now sync independently

**Note**: The `.studon_updater_state.json` file syncs across devices, so if you sync on one device, other devices will know about it and won't re-download the same day.

## Configuration

### Customize Check Interval

Edit the cron job or run with custom interval:

```bash
# Check for Firefox every 10 minutes instead of 5
python studon_auto_updater.py --daily-sync --interval 10
```

### Change Download Location

```bash
# Download to custom location
python studon_scraper.py "URL" "/custom/path"
```

### Modify Settings

Edit `studon_auto_updater.py`:

```python
CHECK_INTERVAL_MINUTES = 60       # How often to check (daemon mode)
MIN_TIME_BETWEEN_UPDATES_HOURS = 6  # Min hours between updates
```

Edit `studon_scraper.py`:

```python
DOWNLOAD_FOLDER = "studon_downloads"  # Where to save files
CONFIRMATION_THRESHOLD = 50           # Ask before downloading this many files
```

## Command Reference

### studon_scraper.py

```bash
# Download from a URL
python studon_scraper.py [URL] [download_path]

# Update all existing courses
python studon_scraper.py --update-all

# Examples:
python studon_scraper.py "https://studon.fau.de/..."
python studon_scraper.py --update-all
python studon_scraper.py --update-all custom_folder
```

### studon_auto_updater.py

```bash
# Run daily sync (waits for Firefox, syncs once, exits)
python studon_auto_updater.py --daily-sync

# Run once now (if conditions met)
python studon_auto_updater.py --once

# Run as daemon (continuous background process)
python studon_auto_updater.py --daemon

# Force update regardless of time
python studon_auto_updater.py --once --force

# Custom intervals
python studon_auto_updater.py --daily-sync --interval 10
python studon_auto_updater.py --daemon --interval 30 --min-hours 3
```

## Troubleshooting

### No files are being downloaded

**Problem**: The script runs but finds 0 files.

**Solutions**:
1. Make sure you're logged into StudOn in Firefox
2. Try logging out and back in to refresh cookies
3. Check if the course URL is accessible in your browser

### "Could not load Firefox cookies"

**Problem**: Script can't access Firefox cookies.

**Solutions**:
1. Make sure Firefox is installed and you've logged into StudOn
2. On Linux, you might need to close Firefox first (it locks the cookie database)
3. Try using a different browser (modify the code to use Chrome/Edge)

### Cron job not running

**Problem**: Script doesn't start on login.

**Solutions**:
1. Check crontab: `crontab -l`
2. Check logs: `cat studon_sync.log`
3. Verify the path in the cron job is correct
4. Make sure Python 3 is at `/usr/bin/python3` (check with `which python3`)

### Files are being re-downloaded

**Problem**: Same files download again.

**Solution**: This shouldn't happen - the script checks for existing files. If it does:
1. Check file permissions
2. Verify the file paths match exactly
3. Check the logs for error messages

### Script keeps running forever

**Problem**: Daily sync doesn't exit.

**Solutions**:
1. Kill the process: `pkill -f studon_auto_updater`
2. Check if Firefox is actually running: `pgrep firefox`
3. Check the logs: `tail -f studon_sync.log`

## Advanced Usage

### Run in Background Manually

```bash
# Start daily sync in background
nohup python studon_auto_updater.py --daily-sync > studon_sync.log 2>&1 &

# Check if it's running
ps aux | grep studon_auto_updater

# Kill it
pkill -f studon_auto_updater
```

### Systemd Service (Alternative to Cron)

Create `/etc/systemd/user/studon-sync.service`:

```ini
[Unit]
Description=StudOn Daily Sync
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/path/to/Studium
ExecStart=/usr/bin/python3 /path/to/Studium/studon_auto_updater.py --daily-sync --interval 5
StandardOutput=append:/path/to/Studium/studon_sync.log
StandardError=append:/path/to/Studium/studon_sync.log

[Install]
WantedBy=default.target
```

Enable it:
```bash
systemctl --user enable studon-sync.service
systemctl --user start studon-sync.service
```

## Privacy & Security

- **Cookies**: This script uses your Firefox cookies to authenticate with StudOn
- **No Password Storage**: Your password is never stored or transmitted
- **Local Only**: All processing happens on your machine
- **No External Services**: Connects only to studon.fau.de

## Contributing

Found a bug? Want to add a feature? Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## For KI-Materialtechnologie Students

### New Semester Setup

At the start of each semester:
1. Log into StudOn in Firefox and enroll in your new courses
2. Download each new course once: `python studon_scraper.py "<course-url>"`
3. From then on, the daily sync will automatically check all courses for new files

**Note:** The scraper NEVER deletes old files. It only downloads new files that don't exist yet. Your old course materials from previous semesters stay untouched.

## License

MIT License - Feel free to use and modify as needed.

## Disclaimer

This tool is provided as-is for educational purposes. Please respect FAU's terms of service and use responsibly. Don't overload StudOn servers - the built-in rate limiting is intentional.

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the logs in `studon_sync.log`
- Open an issue on GitHub

---

**Made with ❤️ for FAU students**

Happy studying! 📚
