#!/usr/bin/env python3
"""
Calculate the PriceFeed contract hash using neo-express.

Requirements:
- dotnet build tooling (to compile the contract)
- neo-express (neoxp) on PATH
"""

import argparse
import shutil
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NEF = ROOT / "src/PriceFeed.Contracts/bin/sc/PriceFeed.Oracle.nef"
DEFAULT_ACCOUNT = "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX"  # Master account used across configs


def run(cmd, **kwargs):
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description="Compute contract hash for the compiled PriceFeed contract.")
    parser.add_argument("--nef", default=str(DEFAULT_NEF), help="Path to .nef file (defaults to compiled contract)")
    parser.add_argument("--account", default=DEFAULT_ACCOUNT, help="Deployer account (address or label)")
    parser.add_argument("--data-file", help="Optional neo-express data file to resolve account labels")
    parser.add_argument("--skip-build", action="store_true", help="Skip rebuilding the contract before hashing")
    args = parser.parse_args()

    neoxp = shutil.which("neoxp") or shutil.which("neo-express")
    if not neoxp:
        print("neo-express (neoxp) is required. Install via: dotnet tool install -g Neo.Express", file=sys.stderr)
        sys.exit(1)

    nef_path = Path(args.nef)
    if not args.skip_build:
        print("==> Building contract (Release)")
        run(
            [
                "dotnet",
                "build",
                str(ROOT / "src/PriceFeed.Contracts/PriceFeed.Contracts.csproj"),
                "-c",
                "Release",
                "--nologo",
                "/p:GeneratePackageOnBuild=false",
            ]
        )

    if not nef_path.is_file():
        print(f"NEF file not found: {nef_path}", file=sys.stderr)
        sys.exit(1)

    cmd = [neoxp, "contract", "hash", str(nef_path), args.account]
    if args.data_file:
        cmd.extend(["-i", args.data_file])

    print(f"==> Calculating contract hash from {nef_path}")
    result = run(cmd)
    contract_hash = result.stdout.strip().splitlines()[-1]

    print("\nContract hash")
    print("============")
    print(contract_hash)
    print("\nUpdate your configuration (BatchProcessing:ContractScriptHash) with the value above.")


if __name__ == "__main__":
    main()
