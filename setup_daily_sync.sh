#!/bin/bash
# Setup script for StudOn daily sync on user login

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Detect Python 3 location
if command -v python3 &> /dev/null; then
    PYTHON3_PATH=$(which python3)
else
    echo "❌ Python 3 not found! Please install Python 3 first."
    exit 1
fi

# Default settings
CHECK_INTERVAL=5  # minutes

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --interval)
            CHECK_INTERVAL="$2"
            shift 2
            ;;
        -h|--help)
            echo "StudOn Daily Sync Setup Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --interval N    Set check interval in minutes (default: 5)"
            echo "  -h, --help      Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

CRON_COMMAND="@reboot cd $SCRIPT_DIR && $PYTHON3_PATH $SCRIPT_DIR/studon_auto_updater.py --daily-sync --interval $CHECK_INTERVAL >> $SCRIPT_DIR/studon_sync.log 2>&1"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          StudOn Daily Sync Setup                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Configuration:"
echo "   Script directory: $SCRIPT_DIR"
echo "   Python 3 path:    $PYTHON3_PATH"
echo "   Check interval:   $CHECK_INTERVAL minutes"
echo ""
echo "📝 This will add a cron job that:"
echo "   • Runs automatically when you log in"
echo "   • Waits for Firefox to be available"
echo "   • Syncs all StudOn courses once per day"
echo "   • Exits after sync is complete (or if already done today)"
echo ""
echo "🔧 Cron entry to be added:"
echo "   $CRON_COMMAND"
echo ""

# Check Python dependencies
echo "🔍 Checking Python dependencies..."
MISSING_DEPS=()

$PYTHON3_PATH -c "import requests" 2>/dev/null || MISSING_DEPS+=("requests")
$PYTHON3_PATH -c "import bs4" 2>/dev/null || MISSING_DEPS+=("beautifulsoup4")
$PYTHON3_PATH -c "import pyperclip" 2>/dev/null || MISSING_DEPS+=("pyperclip")
$PYTHON3_PATH -c "import browser_cookie3" 2>/dev/null || MISSING_DEPS+=("browser-cookie3")

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  Missing required Python packages:"
    for dep in "${MISSING_DEPS[@]}"; do
        echo "   • $dep"
    done
    echo ""
    echo "Install them with:"
    echo "   pip install -r requirements.txt"
    echo ""
    echo "Or individually:"
    echo "   pip install ${MISSING_DEPS[*]}"
    echo ""
    read -p "Do you want to continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled. Please install dependencies first."
        exit 1
    fi
else
    echo "✅ All dependencies installed"
fi

echo ""

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -q "studon_auto_updater.py --daily-sync"; then
    echo "⚠️  A daily sync cron job already exists!"
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep "studon_auto_updater"
    echo ""
    read -p "Do you want to replace it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi

    # Remove old entry
    crontab -l | grep -v "studon_auto_updater.py --daily-sync" | crontab -
    echo "✓ Old entry removed."
    echo ""
fi

# Add new cron entry
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

if [ $? -eq 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║              ✅ Setup Completed Successfully!              ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📅 The sync will:"
    echo "   • Start automatically when you log in / reboot"
    echo "   • Check for Firefox every $CHECK_INTERVAL minutes"
    echo "   • Sync once per day when Firefox is available"
    echo "   • Log output to: studon_sync.log"
    echo ""
    echo "📊 Useful commands:"
    echo "   View live logs:       tail -f $SCRIPT_DIR/studon_sync.log"
    echo "   Check cron jobs:      crontab -l"
    echo "   Force sync now:       python3 studon_auto_updater.py --once --force"
    echo "   Update all courses:   python3 studon_scraper.py --update-all"
    echo ""
    echo "🔧 To modify or remove:"
    echo "   Edit cron jobs:       crontab -e"
    echo "   Remove this job:      crontab -e  # Then delete the @reboot line"
    echo ""
    echo "💡 Next steps:"
    echo "   1. Make sure you're logged into StudOn in Firefox"
    echo "   2. Download your first course: python3 studon_scraper.py <URL>"
    echo "   3. The daily sync will handle updates from now on!"
    echo ""
    echo "📖 For more information, see README.md"
    echo ""
else
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                  ❌ Setup Failed                           ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "You can add the cron job manually with:"
    echo "   crontab -e"
    echo ""
    echo "Then add this line:"
    echo "   $CRON_COMMAND"
    echo ""
fi
