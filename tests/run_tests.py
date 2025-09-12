#!/usr/bin/env python3
"""
Test runner script for Racer project.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run Racer tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--docker", action="store_true", help="Include Docker tests")
    parser.add_argument("--api", action="store_true", help="Include API tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--markers", help="Run tests with specific markers")
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["conda", "run", "-n", "racer", "python", "-m", "pytest"]
    
    # Add test paths
    if args.unit:
        cmd.append("tests/unit/")
    elif args.integration:
        cmd.append("tests/integration/")
    else:
        cmd.append("tests/")
    
    # Add markers
    markers = []
    if not args.docker:
        markers.append("not docker")
    if not args.api:
        markers.append("not api")
    if args.markers:
        markers.append(args.markers)
    
    if markers:
        cmd.extend(["-m", " and ".join(markers)])
    
    # Add coverage
    if args.coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
    
    # Add verbose
    if args.verbose:
        cmd.append("-v")
    
    # Run tests
    success = run_command(cmd, "Running tests")
    
    if not success:
        print("\n❌ Tests failed!")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")


if __name__ == "__main__":
    main()
