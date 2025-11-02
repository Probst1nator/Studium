import os
import re
import sys
import shutil
import requests
import pyperclip
import browser_cookie3
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import datetime
from typing import Dict, List, Optional, Tuple
import zipfile
import tarfile
import argparse
try:
    import py7zr
except ImportError:
    py7zr = None

# --- CONFIGURATION ---
DOWNLOAD_FOLDER = "studon_downloads"
STUDON_DOMAIN = 'studon.fau.de'
CONFIRMATION_THRESHOLD = 50 # Ask for confirmation if more than this many files are found

# --- HELPER FUNCTIONS ---

def is_valid_url(url_string: str) -> bool:
    """Checks if a string is a well-formed URL."""
    if not isinstance(url_string, str) or not url_string:
        return False
    try:
        result = urlparse(url_string)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except (ValueError, AttributeError):
        return False

def find_all_metadata_files(base_folder: str) -> List[Tuple[str, str, str]]:
    """
    Finds all METADATA.md files in the download folder.
    Returns a list of tuples: (metadata_file_path, source_url, course_folder_path)
    """
    metadata_files = []

    for root, dirs, files in os.walk(base_folder):
        if "METADATA.md" in files:
            metadata_path = os.path.join(root, "METADATA.md")
            try:
                with open(metadata_path, 'r') as f:
                    content = f.read()
                    # Extract source URL from metadata
                    match = re.search(r'^Source:\s*(.+)$', content, re.MULTILINE)
                    if match:
                        source_url = match.group(1).strip()
                        course_folder = root
                        metadata_files.append((metadata_path, source_url, course_folder))
                        print(f"   Found: {metadata_path}")
                        print(f"      Source: {source_url}")
            except Exception as e:
                print(f"   ⚠️ Could not read {metadata_path}: {e}")

    return metadata_files

def get_url_and_download_path_from_sources() -> tuple[Optional[str], Optional[str]]:
    """Tries to get a URL and download path from command-line args, clipboard, or user input."""
    download_path = None

    # Check if URL was passed as command-line argument
    if len(sys.argv) > 1:
        provided_url = sys.argv[1]
        if is_valid_url(provided_url):
            print(f"✅ Using URL from command-line argument: {provided_url}")
            # Check if download path was also provided
            if len(sys.argv) > 2:
                download_path = sys.argv[2]
                print(f"✅ Using download path from command-line argument: {download_path}")
            return provided_url, download_path
        else:
            print(f"❌ Invalid URL provided as argument: {provided_url}")
            return None, None

    try:
        clipboard_content = pyperclip.paste()
        if is_valid_url(clipboard_content):
            print(f"✅ Found valid URL in clipboard: {clipboard_content}")
            return clipboard_content, download_path
    except (pyperclip.PyperclipException, pyperclip.PyperclipWindowsException):
        print("INFO: Could not access clipboard. Please provide a URL manually.")

    while True:
        url_input = input("➡️ Please paste or type the StudOn URL and press Enter (or leave blank to exit): ")
        if not url_input: return None, None
        if is_valid_url(url_input): return url_input, download_path
        print("❌ The entered text is not a valid URL. Please try again.")

def clean_filename(name: str) -> str:
    """Removes characters that are illegal in file paths."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def extract_course_title(page_url: str, session: requests.Session) -> Optional[str]:
    """
    Extracts the course title from a StudOn page.
    Tries multiple common StudOn HTML patterns to find the title.
    """
    try:
        response = session.get(page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Try multiple selectors commonly used for course titles in StudOn
        title_selectors = [
            ('h1', {'class': re.compile(r'.*')}),  # Any h1
            ('div', {'class': re.compile(r'il.*Title|PageTitle', re.IGNORECASE)}),
            ('span', {'class': re.compile(r'il.*Title', re.IGNORECASE)}),
        ]

        for tag_name, attrs in title_selectors:
            element = soup.find(tag_name, attrs)
            if element:
                title = element.get_text(strip=True)
                if title:
                    return clean_filename(title)

        # Fallback: try to get the page title from <title> tag
        page_title = soup.find('title')
        if page_title:
            title_text = page_title.get_text(strip=True)
            # Remove common prefixes like "StudOn - "
            title_text = re.sub(r'^[^-]+ - ', '', title_text).strip()
            if title_text:
                return clean_filename(title_text)

        return None
    except Exception as e:
        print(f"   ⚠️ Could not extract course title: {e}")
        return None

def clear_download_folder(folder_path: str) -> None:
    """Completely removes and recreates the download folder to ensure fresh content."""
    if os.path.exists(folder_path):
        print(f"🗑️ Clearing existing download folder: {folder_path}")
        shutil.rmtree(folder_path)
    os.makedirs(folder_path, exist_ok=True)
    print(f"📁 Created fresh download folder: {folder_path}")

def extract_archive(archive_path: str) -> bool:
    """
    Extracts a single archive file (.zip, .tar, .tar.gz, .tar.bz2, .7z).
    Creates a folder named after the archive file (without extension) and extracts into it.
    Returns True if extraction was successful, False otherwise.
    """
    try:
        parent_dir = os.path.dirname(archive_path)
        filename = os.path.basename(archive_path)

        # Get filename without extension for folder name
        if filename.endswith('.tar.gz'):
            folder_name = filename[:-7]
        elif filename.endswith('.tar.bz2'):
            folder_name = filename[:-8]
        elif filename.endswith(('.tgz', '.tbz2')):
            folder_name = filename[:-4]
        elif filename.endswith(('.zip', '.tar', '.7z')):
            folder_name = filename.rsplit('.', 1)[0]
        else:
            folder_name = filename

        # Create extraction directory with archive name
        extract_dir = os.path.join(parent_dir, folder_name)
        os.makedirs(extract_dir, exist_ok=True)

        if archive_path.endswith('.zip'):
            print(f"      📦 Extracting ZIP: {filename}")
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            return True

        elif archive_path.endswith(('.tar', '.tar.gz', '.tar.bz2', '.tgz', '.tbz2')):
            print(f"      📦 Extracting TAR: {filename}")
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_dir)
            return True

        elif archive_path.endswith('.7z'):
            if py7zr is None:
                print(f"      ⚠️ Skipping 7z file (py7zr not installed): {filename}")
                print(f"         Install it with: pip install py7zr")
                return False
            print(f"      📦 Extracting 7z: {filename}")
            with py7zr.SevenZipFile(archive_path, 'r') as archive:
                archive.extractall(extract_dir)
            return True

    except Exception as e:
        print(f"      ❌ Error extracting {archive_path}: {e}")
        return False

def extract_all_archives(root_path: str) -> int:
    """
    Recursively finds and extracts all archive files in the directory tree.
    Returns the number of successfully extracted archives.
    """
    extracted_count = 0
    archive_extensions = ('.zip', '.tar', '.tar.gz', '.tar.bz2', '.7z', '.tgz', '.tbz2')

    # Use os.walk to traverse directory tree
    for dirpath, dirnames, filenames in os.walk(root_path):
        for filename in filenames:
            if filename.lower().endswith(archive_extensions):
                archive_path = os.path.join(dirpath, filename)
                if extract_archive(archive_path):
                    extracted_count += 1

    return extracted_count

def format_file_size(size_bytes: int) -> str:
    """Convert file size in bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def update_recent_files_log(downloaded_files_info: List[Dict[str, str]], base_download_path: str) -> None:
    """
    Updates the RECENT_UPDATES.md file with newly downloaded files.

    Args:
        downloaded_files_info: List of dicts with keys: filepath, timestamp, course, size_bytes
        base_download_path: Base path for downloads (to create relative paths)
    """
    if not downloaded_files_info:
        return

    log_file = os.path.join(base_download_path, "RECENT_UPDATES.md")

    # Read existing entries if file exists
    existing_entries = []
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Skip header lines and extract table rows
                for line in lines:
                    if line.startswith('|') and 'Date/Time' not in line and '---' not in line:
                        existing_entries.append(line.strip())
        except Exception as e:
            print(f"   ⚠️ Could not read existing log: {e}")

    # Format new entries
    new_entries = []
    for file_info in downloaded_files_info:
        filepath = file_info['filepath']
        timestamp = file_info['timestamp']
        course = file_info['course']
        size_bytes = file_info['size_bytes']

        # Get relative path from base_download_path
        try:
            rel_path = os.path.relpath(filepath, base_download_path)
        except ValueError:
            rel_path = filepath  # Fallback if paths are on different drives

        filename = os.path.basename(filepath)
        size_str = format_file_size(size_bytes)

        # Format: | Date/Time | Course | Filename | Relative Path | Size |
        entry = f"| {timestamp} | {course} | {filename} | {rel_path} | {size_str} |"
        new_entries.append(entry)

    # Combine all entries (new + existing)
    all_entries = new_entries + existing_entries

    # Sort by timestamp (newest first) - extract timestamp from each line
    def get_timestamp(entry_line: str) -> str:
        parts = entry_line.split('|')
        if len(parts) >= 2:
            return parts[1].strip()  # timestamp is second column
        return ""

    all_entries.sort(key=get_timestamp, reverse=True)

    # Write the complete log file
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("# StudOn Recent Updates\n\n")
            f.write(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("| Date/Time | Course | Filename | Relative Path | Size |\n")
            f.write("|-----------|--------|----------|---------------|------|\n")
            for entry in all_entries:
                f.write(entry + "\n")

        print(f"\n📝 Updated recent files log: {log_file}")
    except Exception as e:
        print(f"   ⚠️ Could not write log file: {e}")

# --- CORE LOGIC ---

def discover_items_recursive(page_url: str, current_path: str, session: requests.Session, file_list: List[Dict[str, str]], course_title: Optional[str] = None, debug: bool = False) -> None:
    """
    Recursively scans StudOn pages, identifying files and folders.
    It populates the `file_list` with all files it finds.
    course_title is stored in file_info for later use in metadata.
    """
    print(f"🔎 Scanning: {current_path}")
    try:
        response = session.get(page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"   ❌ Could not access {page_url}. Error: {e}. Skipping.")
        return

    # Try multiple strategies to find items
    items = soup.find_all('div', class_='il_ContainerListItem')

    if debug or not items:
        print(f"   [DEBUG] Found {len(items)} items with class 'il_ContainerListItem'")
        # Try alternative selectors
        alt_items = soup.find_all('div', class_=re.compile(r'il.*ListItem'))
        print(f"   [DEBUG] Found {len(alt_items)} items matching 'il.*ListItem' pattern")

        # Look for any links that might be files
        all_links = soup.find_all('a', href=True)
        file_links = [link for link in all_links if 'cmd=sendfile' in link.get('href', '')]
        print(f"   [DEBUG] Found {len(file_links)} direct file download links")
        folder_links = [link for link in all_links if 'cmd=view' in link.get('href', '') and 'ref_id' in link.get('href', '')]
        print(f"   [DEBUG] Found {len(folder_links)} potential folder links")

    # If no items found with standard selector, try to find any downloadable files directly
    if not items:
        print(f"   [INFO] Using fallback strategy to find files and folders")
        all_links = soup.find_all('a', href=True)

        for link in all_links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True)

            # Skip empty links or navigation links
            if not link_text or len(link_text) < 2:
                continue

            # Check if it's a file download link
            if 'cmd=sendfile' in href:
                item_url = urljoin(page_url, href)
                item_name = clean_filename(link_text)
                if item_name:
                    file_info: Dict[str, str] = {
                        'url': item_url,
                        'path': current_path,
                        'name': item_name,
                        'course_title': course_title or 'Unknown Course'
                    }
                    file_list.append(file_info)
                    print(f"   ✓ Found file: {item_name}")

            # Check if it's a folder link
            elif 'cmd=view' in href and 'ref_id' in href and link_text:
                # Skip if it looks like a navigation element
                if link_text.lower() in ['home', 'back', 'up', 'zurück', 'startseite']:
                    continue
                item_url = urljoin(page_url, href)
                item_name = clean_filename(link_text)
                if item_name:
                    new_path = os.path.join(current_path, item_name)
                    print(f"   ↳ Entering folder: {item_name}")
                    discover_items_recursive(item_url, new_path, session, file_list, course_title, debug)
        return

    for item in items:
        # Find the main link for the item
        link_tag = item.find('a', class_='il_ContainerItemTitle')
        if not link_tag:
            continue

        item_url: str = urljoin(page_url, link_tag['href'])
        item_name: str = clean_filename(link_tag.text)

        # Check if it's a folder by looking for the folder icon
        # StudOn uses an image with alt text 'Folder' or 'Ordner'
        # Look in the parent container for the icon
        parent_container = item.find_parent('div', class_='ilContainerListItemOuter')
        is_folder: bool = False
        if parent_container:
            is_folder = parent_container.find('img', alt=re.compile(r'Folder|Ordner', re.IGNORECASE))

        if is_folder:
            new_path: str = os.path.join(current_path, item_name)
            discover_items_recursive(item_url, new_path, session, file_list, course_title, debug)
        else:
            # Check if it's a file download link
            is_file: bool = "cmd=sendfile" in link_tag['href']
            if is_file:
                file_info: Dict[str, str] = {
                    'url': item_url,
                    'path': current_path,
                    'name': item_name,
                    'course_title': course_title or 'Unknown Course'
                }
                file_list.append(file_info)

def download_all_files(source: str, files_to_download: List[Dict[str, str]], session: requests.Session, course_title: Optional[str] = None, base_path: str = None) -> Tuple[int, List[str]]:
    """Downloads all files from the provided list.

    Returns:
        Tuple of (download_count, list_of_downloaded_filepaths)
    """
    if not files_to_download:
        return 0, []

    print("-" * 50)
    print(f"🚀 Starting download of {len(files_to_download)} files...")
    download_count: int = 0
    downloaded_files: List[str] = []
    downloaded_files_info: List[Dict] = []  # For logging

    # Use provided base_path or fall back to DOWNLOAD_FOLDER
    metadata_folder = base_path if base_path else DOWNLOAD_FOLDER

    with open(os.path.join(metadata_folder, "METADATA.md"), 'w') as f:
        meta_info = f"""Course: {course_title or 'Unknown Course'}
Source: {source}
Last fetched: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""
        f.write(meta_info)
    
    for i, file_info in enumerate(files_to_download):
        file_url: str = file_info['url']
        save_path: str = file_info['path']
        expected_name: str = file_info.get('name', 'unknown_file')

        print(f"   ({i+1}/{len(files_to_download)}) Checking: {expected_name}")

        try:
            # Ensure the local directory exists
            os.makedirs(save_path, exist_ok=True)

            # Check if file already exists (before downloading)
            # Try with the expected name and also with .pdf extension if no extension
            filepath_candidates = [os.path.join(save_path, expected_name)]
            if '.' not in expected_name:
                filepath_candidates.append(os.path.join(save_path, expected_name + '.pdf'))

            file_exists = False
            existing_path = None
            for candidate in filepath_candidates:
                if os.path.exists(candidate):
                    file_exists = True
                    existing_path = candidate
                    break

            if file_exists:
                print(f"   ⏭️  Skipped (already exists): {existing_path}")
                continue

            # File doesn't exist, proceed with download
            print(f"      Downloading from: {file_url}")
            file_response = session.get(file_url, stream=True)
            file_response.raise_for_status()

            # Try to get filename from Content-Disposition header first
            filename: str = expected_name
            if "Content-Disposition" in file_response.headers:
                content_disposition: str = file_response.headers["Content-Disposition"]
                match = re.search(r'filename="([^"]+)"', content_disposition)
                if match:
                    header_filename: str = clean_filename(match.group(1))
                    if header_filename:  # Only use if not empty
                        filename = header_filename

            # Ensure filename has a proper extension if missing
            if '.' not in filename:
                filename += '.pdf'  # Most StudOn files are PDFs

            filepath: str = os.path.join(save_path, filename)

            with open(filepath, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"   ✅ Successfully saved to: {filepath}")
            download_count += 1
            downloaded_files.append(filepath)

            # Collect metadata for logging
            try:
                file_size = os.path.getsize(filepath)
                downloaded_files_info.append({
                    'filepath': filepath,
                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'course': file_info.get('course_title', course_title or 'Unknown Course'),
                    'size_bytes': file_size
                })
            except Exception:
                pass  # If we can't get size, just skip logging this file
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error downloading {file_url}: {e}")
        except OSError as e:
            print(f"   ❌ File system error saving to {save_path}: {e}")

    # Update the recent files log if any files were downloaded
    if downloaded_files_info:
        update_recent_files_log(downloaded_files_info, DOWNLOAD_FOLDER)

    return download_count, downloaded_files

# --- MAIN EXECUTION ---

def process_single_url(start_url: str, session: requests.Session, base_download_path: str = None, create_course_subfolder: bool = True) -> Tuple[int, int, List[str]]:
    """
    Processes a single StudOn URL: discovers files, downloads new ones, and extracts archives.

    Args:
        start_url: The StudOn URL to process
        session: The requests session with cookies
        base_download_path: Base path for downloads (defaults to DOWNLOAD_FOLDER)
        create_course_subfolder: If True, creates a subfolder named after the course title

    Returns:
        Tuple of (downloaded_count, extracted_count, list_of_downloaded_filepaths)
    """
    # --- Extract Course Title ---
    print("\n--- Extracting Course Title ---")
    course_title = extract_course_title(start_url, session)
    if course_title:
        print(f"📚 Course: {course_title}")
    else:
        print("⚠️ Could not determine course title. Using default folder name.")
        course_title = None

    # --- Prepare download folder ---
    print("\n--- Preparing Download Folder ---")
    # Use provided base path or DOWNLOAD_FOLDER
    root_folder = base_download_path if base_download_path else DOWNLOAD_FOLDER
    os.makedirs(root_folder, exist_ok=True)
    print(f"📁 Download folder: {root_folder}")

    # Create course-specific subfolder if title was found and requested
    if course_title and create_course_subfolder:
        course_folder = os.path.join(root_folder, course_title)
        os.makedirs(course_folder, exist_ok=True)
        print(f"📁 Course folder: {course_folder}")
        final_download_path = course_folder
    else:
        final_download_path = root_folder

    # --- 1. Discovery Pass ---
    print("\n--- Starting Discovery Phase ---")
    all_files_to_download: List[Dict[str, str]] = []
    discover_items_recursive(start_url, final_download_path, session, all_files_to_download, course_title, debug=False)

    total_files: int = len(all_files_to_download)
    print("\n--- Discovery Complete ---")
    print(f"✅ Found a total of {total_files} file(s) across all folders.")

    if total_files == 0:
        print("No downloadable files found.")
        return 0, 0, []

    # --- 2. Download Pass ---
    num_downloaded, downloaded_files = download_all_files(start_url, all_files_to_download, session, course_title, final_download_path)

    print("-" * 50)
    print(f"🎉 Download completed. Successfully downloaded {num_downloaded}/{total_files} file(s).")

    # --- 3. Extract Archives Pass ---
    print("\n--- Starting Extraction Phase ---")
    num_extracted = extract_all_archives(final_download_path)

    if num_extracted > 0:
        print(f"✅ Successfully extracted {num_extracted} archive file(s).")
    else:
        print("ℹ️ No archives found to extract.")

    return num_downloaded, num_extracted, downloaded_files

def main() -> None:
    """Main execution loop."""
    global DOWNLOAD_FOLDER

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='StudOn Recursive File Downloader')
    parser.add_argument('url', nargs='?', help='StudOn URL to download from')
    parser.add_argument('download_path', nargs='?', help='Custom download path')
    parser.add_argument('--update-all', '-u', action='store_true',
                        help='Update all courses by scanning existing METADATA.md files')
    args = parser.parse_args()

    print("--- StudOn Recursive File Downloader ---")

    # --- Setup Session with Cookies ---
    try:
        print("\nAttempting to load browser cookies...")
        cj = browser_cookie3.firefox(domain_name=STUDON_DOMAIN)
        session = requests.Session()
        session.cookies.update(cj)
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        print("🍪 Firefox cookies loaded successfully.")
    except Exception as e:
        print(f"❌ An error occurred while loading Firefox cookies: {e}")
        print("   Please ensure you are logged into StudOn in Firefox.")
        return

    # --- Update All Mode ---
    if args.update_all:
        print("\n🔄 Update All Mode: Scanning for existing courses...")

        # Override DOWNLOAD_FOLDER if custom path was provided
        if args.download_path:
            DOWNLOAD_FOLDER = args.download_path
            print(f"📁 Using custom download folder: {DOWNLOAD_FOLDER}")

        metadata_files = find_all_metadata_files(DOWNLOAD_FOLDER)

        if not metadata_files:
            print("❌ No METADATA.md files found. Nothing to update.")
            return

        print(f"\n📚 Found {len(metadata_files)} course(s) to update.\n")

        total_downloaded = 0
        total_extracted = 0
        all_downloaded_files = {}  # Dict[course_folder, List[filepath]]

        for i, (metadata_path, source_url, course_folder) in enumerate(metadata_files, 1):
            print("=" * 60)
            print(f"📖 Course {i}/{len(metadata_files)}")
            print(f"   Folder: {course_folder}")
            print(f"   Source: {source_url}")
            print("=" * 60)

            try:
                # Don't create a course subfolder since we're already in the course folder
                downloaded, extracted, files_list = process_single_url(source_url, session, course_folder, create_course_subfolder=False)
                total_downloaded += downloaded
                total_extracted += extracted
                if files_list:
                    all_downloaded_files[course_folder] = files_list
            except Exception as e:
                print(f"❌ Error processing {source_url}: {e}")
                continue

        print("\n" + "=" * 60)
        print(f"🎉 Update All Complete!")
        print(f"   Total new files downloaded: {total_downloaded}")
        print(f"   Total archives extracted: {total_extracted}")
        print("=" * 60)

        # Display downloaded files organized by course
        if all_downloaded_files:
            print("\n📥 Downloaded Files:")
            print("-" * 60)
            for course_folder, files in all_downloaded_files.items():
                # Extract just the course name from the folder path
                course_name = os.path.basename(course_folder)
                print(f"\n📁 {course_name} ({len(files)} file{'s' if len(files) != 1 else ''}):")
                for filepath in files:
                    # Show relative path from course folder for readability
                    rel_path = os.path.relpath(filepath, course_folder)
                    print(f"   • {rel_path}")
            print()

        # Warn if no files were found at all (likely authentication issue)
        if total_downloaded == 0 and len(metadata_files) > 0:
            print("\n⚠️  WARNING: No files found across ANY course!")
            print("   This usually means one of the following:")
            print("   1. You're not logged into StudOn in your browser")
            print("      → Solution: Open Firefox and log into studon.fau.de")
            print("   2. Browser cookies expired or were cleared")
            print("      → Solution: Log out and log back in to refresh cookies")
            print("   3. StudOn changed their HTML structure")
            print("      → Solution: Check if the script needs updates")
            print("\n💡 Tip: Open one of the course URLs in your browser to verify access.")

        return

    # --- Single URL Mode ---
    start_url = args.url
    custom_download_path = args.download_path

    if not start_url:
        start_url, custom_download_path = get_url_and_download_path_from_sources()

    if not start_url:
        print("No URL provided. Exiting.")
        return

    # Override DOWNLOAD_FOLDER if custom path was provided
    if custom_download_path:
        DOWNLOAD_FOLDER = custom_download_path
        print(f"📁 Using custom download folder: {DOWNLOAD_FOLDER}")

    # Process the single URL
    downloaded, extracted, files_list = process_single_url(start_url, session, DOWNLOAD_FOLDER)

    print("-" * 50)
    print(f"🎉 Process completed. Downloaded {downloaded} new file(s), extracted {extracted} archive(s).")
    print(f"📁 Files are organized in the '{DOWNLOAD_FOLDER}' folder with the same structure as StudOn.")

    # Display downloaded files
    if files_list:
        print("\n📥 Downloaded Files:")
        print("-" * 50)
        for filepath in files_list:
            # Show relative path from download folder for readability
            rel_path = os.path.relpath(filepath, DOWNLOAD_FOLDER)
            print(f"   • {rel_path}")


if __name__ == "__main__":
    main()