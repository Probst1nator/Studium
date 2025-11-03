# FAU Student Resources

> A personal project by a KI-Materialtechnologie student. Not affiliated with or endorsed by FAU.

Essential links and tools for FAU (Friedrich-Alexander-Universität Erlangen-Nürnberg) students.

## Essential FAU Links

A handpicked list of useful links for FAU students, specifically with KI-Materialtechnologie/NAT students in mind.

### Daily Essentials

**Südmensa Weekly Menu** (often changes spontaneously):

https://www.werkswelt.de/?id=sued

**Campo Timetable**:

https://www.campo.fau.de/qisserver/pages/plan/individualTimetable.xhtml?_flowId=individualTimetableSchedule-flow

### Long-Term Study Planning

**Module Planner**:

https://www.campo.fau.de/qisserver/pages/startFlow.xhtml?_flowId=studyPlanner-flow

**Grade Overview**:

https://www.campo.fau.de/qisserver/pages/sul/examAssessment/personExamsReadonly.xhtml?_flowId=examsOverviewForPerson-flow

**FAU personal data hub**:

https://www.idm.fau.de/go/profile/overview

**Opinionated recommendation: Subscribe to some interesting FAU mailinglists**:

https://www.idm.fau.de/go/mail/subscriptions

**Opinionated recommendation: Pick some sports course (best done at the start of a semester)**:

https://www.anmeldung.sport.uni-erlangen.de/hsp/sportarten/aktueller_zeitraum_0

---

## StudOn Auto-Downloader

Automated downloader for StudOn course materials. Created with KI-Materialtechnologie students in mind, but useful for anyone who wants to keep their course materials synchronized automatically.

> **⚠️ Platform Notice:** This tool has only been tested on **Kubuntu/Ubuntu Linux**. While manual download mode should work on most platforms, the automatic daily sync feature may require manual configuration on Windows, macOS, or other Linux distributions. See [SETUP.md](SETUP.md) for details.

### Features

- 🔄 **Automatic Updates**: Syncs all your StudOn courses automatically
- 📁 **Smart File Management**: Only downloads new files, never overwrites existing ones
- 🗂️ **Organized Structure**: Maintains the same folder structure as StudOn
- 📦 **Archive Extraction**: Automatically extracts `.zip`, `.7z`, `.tar`, `.tar.gz` files
- 🍪 **Browser Cookie Authentication**: Uses Firefox cookies for authentication
- 💤 **Optional Autonomous Fetching**: Can be run as background agent, terminating on daily fetch-success
- 📝 **Full Featured Logging**: All operations are logged. A local file history will be generated at `studon_sync.log`

### How It Works

```
User Login → Script Starts → Waits for Firefox → Syncs All Courses → Exits
                                    ↓
                          (Only if not synced today)
```

### Getting Started

See **[SETUP.md](SETUP.md)** for complete installation and usage instructions.

Quick start:
```bash
# Install dependencies
pip install requests beautifulsoup4 pyperclip browser-cookie3

# Make a directory for your study
mkdir Studium
# Change directory into it
cd Studium
# Clone the files from this git-url into the current local directory
git clone https://github.com/Probst1nator/Studium.git .

# Run setup for autonomous background startup of daily (fetch-only) sync via crontab.
# Add executing permissions to the script
chmod +x setup_daily_sync.sh
# Execute it
setup_daily_sync.sh
```

## Privacy & Security

- **Cookies**: This script uses your Firefox cookies to authenticate with StudOn
- **No Password Storage**: Your password is never stored or transmitted
- **Local Only**: All processing happens on your machine
- **No External Services**: Connects only to studon.fau.de

## Contributing

Found a bug? Want to add a feature? Contributions are welcome!

**Especially needed:**
- 🖥️ **Platform support** (Windows, macOS, Arch, Fedora, etc.)
- 🌐 **Browser compatibility** (Chrome, Edge, Brave cookie support)
- 🧪 **Testing** on different distributions

To contribute you have two options:

**A. You know these things**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on your platform and document the results
5. Submit a pull request

**B. Reach out**
1. Talk to me in-person (if you know me)
2. ???
3. Profit

## License

MIT License - Feel free to use and modify as needed.

## Disclaimer

This tool is provided as-is for educational purposes. Please respect FAU's terms of service and use responsibly. Don't overload StudOn servers - the built-in rate limiting is intentional.

## Support

For issues or questions:
- Check the troubleshooting section in [SETUP.md](SETUP.md)
- Review the logs in `studon_sync.log`
- Open an issue on GitHub

---

**Made with ❤️ for FAU students**

Happy studying! 📚
