#!/usr/bin/env python3
"""
Script to fix code formatting issues for the CI pipeline.
Run this to automatically format your Python code.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"⚠️ {description} completed with warnings")
            if result.stderr.strip():
                print(f"Warnings: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {str(e)}")
        return False


def main():
    """Main formatting function."""
    print("🎨 Fixing Code Formatting Issues")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("src").exists() or not Path("tests").exists():
        print("❌ Please run this script from the project root directory")
        print("   (where src/ and tests/ directories are located)")
        return 1
    
    # Install formatting tools
    print("\n📦 Installing formatting tools...")
    install_commands = [
        "pip install black isort flake8",
    ]
    
    for cmd in install_commands:
        run_command(cmd, f"Installing tools: {cmd}")
    
    # Run Black formatter
    print("\n🎨 Running Black code formatter...")
    black_commands = [
        "black src/ tests/ --line-length=88",
        "black . --line-length=88 --extend-exclude='/(\.git|\.venv|venv|\.pytest_cache|__pycache__|\.mypy_cache)/'",
    ]
    
    for cmd in black_commands:
        run_command(cmd, "Black formatting")
    
    # Run isort for import sorting
    print("\n📦 Running isort for import sorting...")
    isort_commands = [
        "isort src/ tests/",
        "isort . --skip-glob='*/.git/*' --skip-glob='*/.venv/*' --skip-glob='*/venv/*'",
    ]
    
    for cmd in isort_commands:
        run_command(cmd, "Import sorting")
    
    # Check the results
    print("\n🔍 Checking formatting results...")
    check_commands = [
        ("black --check --diff src/ tests/", "Black formatting check"),
        ("isort --check-only --diff src/ tests/", "Import sorting check"),
    ]
    
    all_good = True
    for cmd, desc in check_commands:
        if not run_command(cmd, desc):
            all_good = False
    
    # Summary
    print("\n" + "=" * 40)
    if all_good:
        print("🎉 All formatting issues have been fixed!")
        print("\n📋 Next steps:")
        print("1. Review the changes: git diff")
        print("2. Commit the changes: git add . && git commit -m 'style: fix code formatting'")
        print("3. Push to GitHub: git push origin main")
        print("4. Check GitHub Actions - the CI should now pass!")
        return 0
    else:
        print("⚠️ Some formatting issues may remain.")
        print("Please review the output above and fix any remaining issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())