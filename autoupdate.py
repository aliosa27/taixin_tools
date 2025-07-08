
import os
import sys
import tempfile
import shutil
import platform
import subprocess
import logging
from urllib.request import urlopen, Request
import json
import hashlib
import time

GITHUB_OWNER = "aliosa27"
GITHUB_REPO = "taixin_tools"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
GITHUB_RELEASES_URL = f"{GITHUB_API_URL}/releases/latest"
USER_AGENT = "Taixin-LibNetat-Tool-Updater/1.0"

__version__ = "2.0.1"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("autoupdate")

def get_current_version():
    return __version__

def parse_version(version_str):
    if version_str.startswith('v'):
        version_str = version_str[1:]
    
    try:
        return tuple(map(int, version_str.split('.')))
    except ValueError:
        logger.warning(f"Could not parse version: {version_str}")
        return (0, 0, 0)

def check_for_updates(force=False, verbose=False):
    current_version = get_current_version()
    if verbose:
        logger.info(f"Current version: {current_version}")
    
    cache_dir = os.path.join(tempfile.gettempdir(), "taixin_update_cache")
    cache_file = os.path.join(cache_dir, "github_release_info.json")
    cache_max_age = 3600
    
    release_info = None
    
    if not force and os.path.exists(cache_file):
        try:
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < cache_max_age:
                with open(cache_file, 'r') as f:
                    release_info = json.load(f)
                if verbose:
                    logger.info(f"Using cached release info (age: {file_age:.0f} seconds)")
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
    
    if release_info is None:
        try:
            if verbose:
                logger.info("Checking for updates from GitHub...")
            
            request = Request(GITHUB_RELEASES_URL)
            request.add_header('User-Agent', USER_AGENT)
            
            with urlopen(request, timeout=10) as response:
                release_info = json.loads(response.read().decode('utf-8'))
            
            os.makedirs(cache_dir, exist_ok=True)
            with open(cache_file, 'w') as f:
                json.dump(release_info, f)
                
            if verbose:
                logger.info("Successfully fetched release info from GitHub")
                
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False, current_version, None, None
    
    latest_version = release_info.get('tag_name', '0.0.0')
    if latest_version.startswith('v'):
        latest_version = latest_version[1:]
    
    has_update = parse_version(latest_version) > parse_version(current_version)
    
    if verbose:
        if has_update:
            logger.info(f"Update available: {current_version} → {latest_version}")
        else:
            logger.info(f"No updates available. Current version {current_version} is up to date.")
    
    return has_update, current_version, latest_version, release_info

def get_update_assets(release_info):
    if not release_info or 'assets' not in release_info:
        return []
    
    assets = []
    for asset in release_info['assets']:
        assets.append({
            'name': asset.get('name', ''),
            'url': asset.get('browser_download_url', ''),
            'size': asset.get('size', 0)
        })
    
    return assets

def download_file(url, dest_path, progress_callback=None):
    try:
        request = Request(url)
        request.add_header('User-Agent', USER_AGENT)
        
        with urlopen(request) as response, open(dest_path, 'wb') as out_file:
            content_length = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            block_size = 8192
            
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                    
                downloaded += len(buffer)
                out_file.write(buffer)
                
                if progress_callback and content_length > 0:
                    progress = downloaded / content_length
                    progress_callback(progress, downloaded, content_length)
        
        return True
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return False

def verify_file_integrity(file_path, expected_checksum=None, algorithm='sha256'):
    if not expected_checksum:
        return True
    
    try:
        hasher = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        
        actual_checksum = hasher.hexdigest()
        return actual_checksum.lower() == expected_checksum.lower()
    
    except Exception as e:
        logger.error(f"Error verifying file integrity: {e}")
        return False

def backup_current_version(backup_dir=None):
    try:
        source_dir = os.path.dirname(os.path.abspath(__file__))
        
        if backup_dir is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(
                tempfile.gettempdir(), 
                f"taixin_backup_{timestamp}"
            )
        
        os.makedirs(backup_dir, exist_ok=True)
        
        for filename in os.listdir(source_dir):
            file_path = os.path.join(source_dir, filename)
            if os.path.isfile(file_path) and (
                filename.endswith('.py') or 
                filename in ['README.md', 'requirements.txt']
            ):
                shutil.copy2(file_path, backup_dir)
                logger.debug(f"Backed up: {filename}")
        
        logger.info(f"Backup created at: {backup_dir}")
        return backup_dir
    
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return None

def update_from_zip(zip_path, target_dir=None):
    import zipfile
    
    try:
        if target_dir is None:
            target_dir = os.path.dirname(os.path.abspath(__file__))
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            top_dirs = {item.split('/')[0] for item in zip_ref.namelist() if '/' in item}
            
            if len(top_dirs) == 1:
                extract_dir = tempfile.mkdtemp()
                zip_ref.extractall(extract_dir)
                
                source_dir = os.path.join(extract_dir, list(top_dirs)[0])
                for item in os.listdir(source_dir):
                    s = os.path.join(source_dir, item)
                    d = os.path.join(target_dir, item)
                    
                    if os.path.isfile(s):
                        shutil.copy2(s, d)
                    elif os.path.isdir(s):
                        if os.path.exists(d):
                            shutil.rmtree(d)
                        shutil.copytree(s, d)
                
                shutil.rmtree(extract_dir)
            else:
                zip_ref.extractall(target_dir)
        
        logger.info("Update successfully extracted")
        return True
    
    except Exception as e:
        logger.error(f"Error updating from ZIP: {e}")
        return False

def update_from_github(assets=None, verbose=False):
    if not assets:
        _, _, _, release_info = check_for_updates(force=True, verbose=verbose)
        if not release_info:
            logger.error("Failed to get release information")
            return False
        
        assets = get_update_assets(release_info)
    
    if not assets:
        logger.error("No assets found in the release")
        return False
    
    system = platform.system().lower()
    zip_asset = None
    
    for asset in assets:
        name = asset['name'].lower()
        if name.endswith('.zip') and (system in name or 'all' in name):
            zip_asset = asset
            break
    
    if not zip_asset:
        for asset in assets:
            if asset['name'].lower().endswith('.zip'):
                zip_asset = asset
                break
    
    if not zip_asset:
        logger.error("No suitable ZIP file found in release assets")
        return False
    
    temp_dir = tempfile.mkdtemp(prefix="taixin_update_")
    zip_path = os.path.join(temp_dir, zip_asset['name'])
    
    try:
        logger.info(f"Downloading {zip_asset['name']}...")
        
        def progress_callback(progress, downloaded, total):
            if verbose:
                mb_downloaded = downloaded / 1024 / 1024
                mb_total = total / 1024 / 1024
                print(f"\rDownloading: {progress:.1%} ({mb_downloaded:.1f} MB / {mb_total:.1f} MB)", end="")
        
        success = download_file(zip_asset['url'], zip_path, progress_callback)
        if verbose:
            print()
        
        if not success:
            logger.error("Failed to download update file")
            return False
        
        backup_dir = backup_current_version()
        if not backup_dir:
            logger.error("Failed to create backup, aborting update")
            return False
        
        logger.info("Installing update...")
        if update_from_zip(zip_path):
            logger.info("Update completed successfully!")
            
            shutil.rmtree(temp_dir)
            return True
        else:
            logger.error("Update failed, restoring from backup...")
            restore_from_backup(backup_dir)
            return False
    
    except Exception as e:
        logger.error(f"Update failed: {e}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return False

def restore_from_backup(backup_dir):
    try:
        if not os.path.exists(backup_dir):
            logger.error(f"Backup directory not found: {backup_dir}")
            return False
        
        target_dir = os.path.dirname(os.path.abspath(__file__))
        
        for filename in os.listdir(backup_dir):
            source = os.path.join(backup_dir, filename)
            target = os.path.join(target_dir, filename)
            
            if os.path.isfile(source):
                shutil.copy2(source, target)
                logger.debug(f"Restored: {filename}")
        
        logger.info("Restoration from backup completed")
        return True
    
    except Exception as e:
        logger.error(f"Restoration failed: {e}")
        return False

def is_git_repository():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except:
        return False

def update_via_git():
    if not is_git_repository():
        logger.warning("Not a git repository, can't update via git")
        return False
    
    try:
        backup_dir = backup_current_version()
        if not backup_dir:
            logger.error("Failed to create backup, aborting git update")
            return False
        
        logger.info("Updating via git pull...")
        result = subprocess.run(
            ["git", "pull"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("Git update successful")
            logger.info(result.stdout.strip())
            return True
        else:
            logger.error(f"Git update failed: {result.stderr.strip()}")
            restore_from_backup(backup_dir)
            return False
    
    except Exception as e:
        logger.error(f"Git update failed: {e}")
        return False

def check_update_command():
    has_update, current, latest, release_info = check_for_updates(verbose=True)
    
    if has_update:
        return (
            f"Update available: {current} → {latest}\n"
            f"Run 'python libnetat.py --update' to install the update.\n"
            f"Release notes: {release_info.get('html_url', 'N/A')}"
        )
    else:
        return f"You are using the latest version: {current}"

def perform_update_command(force=False):
    has_update, current, latest, release_info = check_for_updates(force=force, verbose=True)
    
    if not has_update and not force:
        return "You are already using the latest version. Use --force-update to update anyway."
    
    if is_git_repository():
        logger.info("Updating via git...")
        if update_via_git():
            return f"Successfully updated to version {latest} using git"
        else:
            logger.warning("Git update failed, trying direct download...")
    
    if update_from_github(verbose=True):
        return f"Successfully updated to version {latest}"
    else:
        return "Update failed. See logs for details."

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Taixin LibNetat Tool Updater")
    parser.add_argument("--check", action="store_true", help="Check for updates")
    parser.add_argument("--update", action="store_true", help="Download and install updates")
    parser.add_argument("--force", action="store_true", help="Force update even if already on latest version")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    if args.check:
        has_update, current, latest, release_info = check_for_updates(force=args.force, verbose=True)
        if has_update:
            print(f"Update available: {current} → {latest}")
            if release_info and 'body' in release_info:
                print("\nRelease notes:")
                print(release_info['body'])
        else:
            print(f"You are using the latest version: {current}")
    
    elif args.update:
        if update_from_github(verbose=True):
            print("Update completed successfully!")
        else:
            print("Update failed. See logs for details.")
    
    else:
        parser.print_help()
