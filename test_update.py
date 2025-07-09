#!/usr/bin/env python3
"""
Test script for the autoupdate functionality.
This script imports and tests the autoupdate module directly.
"""

import sys
import json
import os

try:
    import autoupdate
    from libnetat import __version__ as libnetat_version
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def main():
    print(f"Testing autoupdate module v{autoupdate.__version__}")
    print(f"LibNetat version: {libnetat_version}")
    print("=" * 50)
    
    # Check versions match
    if autoupdate.__version__ != libnetat_version:
        print(f"WARNING: Version mismatch between modules!")
        print(f"  autoupdate: {autoupdate.__version__}")
        print(f"  libnetat:   {libnetat_version}")
    else:
        print(f"Versions match: {autoupdate.__version__}")
    
    # Check for updates
    print("\nChecking for updates...")
    has_update, current, latest, release_info = autoupdate.check_for_updates(verbose=True)
    
    if has_update:
        print(f"Update available: {current} → {latest}")
        print("Release info:", json.dumps(release_info, indent=2)[:200] + "...")
    else:
        print(f"No updates available. Current version {current} is up to date.")
    
    # Test functions
    print("\nTesting parse_version function:")
    versions = ["1.0.0", "1.0.1", "1.1.0", "v2.0.0", "2.0.1", "2.0.2", "2.1.0", "3.0.0"]
    parsed = [(v, autoupdate.parse_version(v)) for v in versions]
    
    for v, p in parsed:
        print(f"  {v:6} -> {p}")
    
    # Sort by parsed version to verify function works correctly
    sorted_versions = sorted(parsed, key=lambda x: x[1])
    print("Sorted versions:")
    for v, p in sorted_versions:
        print(f"  {v:6} -> {p}")
    
    # Check GitHub repo is accessible
    print("\nChecking GitHub repository access...")
    try:
        request = autoupdate.Request(autoupdate.GITHUB_API_URL)
        request.add_header('User-Agent', autoupdate.USER_AGENT)
        
        with autoupdate.urlopen(request, timeout=10) as response:
            repo_info = json.loads(response.read().decode('utf-8'))
            
        print(f"GitHub repository: {repo_info.get('full_name', 'Unknown')}")
        print(f"Owner: {repo_info.get('owner', {}).get('login', 'Unknown')}")
        print(f"Stars: {repo_info.get('stargazers_count', 0)}")
        print(f"Forks: {repo_info.get('forks_count', 0)}")
        print(f"Access successful!")
    except Exception as e:
        print(f"Error accessing GitHub: {e}")
    
    print("\nAutoupdate module test completed successfully.")

if __name__ == "__main__":
    main()