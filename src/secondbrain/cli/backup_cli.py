"""
Command-line interface for companion journaling backup system.
"""
import os
import sys
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.secondbrain.backup.companion_journaling_backup import CompanionJournalingBackup

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Companion Journaling Backup System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--backup-root",
        type=str,
        default=os.path.expanduser("~/.secondbrain/backups"),
        help="Root directory for backups (default: ~/.secondbrain/backups)"
    )
    
    parser.add_argument(
        "--max-backups",
        type=int,
        default=5,
        help="Maximum number of backups to keep (default: 5)"
    )
    
    parser.add_argument(
        "--enable-cloud-sync",
        action="store_true",
        help="Enable cloud synchronization of backups"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing backups"
    )
    
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old backups"
    )
    
    return parser.parse_args()

def list_backups(backup_root: str):
    """List existing backups."""
    backup_dir = Path(backup_root)
    if not backup_dir.exists():
        print("No backups found.")
        return
    
    backups = sorted(backup_dir.glob("journaling_backup_*.zip"))
    if not backups:
        print("No backups found.")
        return
    
    print("\nExisting backups:")
    print("-" * 80)
    print(f"{'Backup File':<40} {'Size':<10} {'Date':<20}")
    print("-" * 80)
    
    for backup in backups:
        size = backup.stat().st_size / (1024 * 1024)  # Convert to MB
        date = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"{backup.name:<40} {size:.1f}MB {date.strftime('%Y-%m-%d %H:%M:%S')}")

async def run_backup(args):
    """Run the backup process."""
    backup = CompanionJournalingBackup(
        backup_root=args.backup_root,
        max_backups=args.max_backups,
        enable_cloud_sync=args.enable_cloud_sync
    )
    
    print("Starting backup process...")
    result = await backup.create_backup()
    
    if result["status"] == "success":
        print("\nBackup completed successfully!")
        print(f"Backup location: {result['backup_path']}")
        print(f"Duration: {result['duration']:.2f} seconds")
        
        # Print component statistics
        print("\nBackup Statistics:")
        print("-" * 40)
        for component, stats in result["manifest"]["components"].items():
            print(f"{component.replace('_', ' ').title()}:")
            print(f"  Total entries: {stats['total_entries']}")
            print(f"  Entry types: {', '.join(stats['entry_types'])}")
            print()
    else:
        print("\nBackup failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)

def main():
    """Main entry point."""
    args = parse_args()
    
    if args.list:
        list_backups(args.backup_root)
        return
    
    if args.cleanup:
        backup = CompanionJournalingBackup(
            backup_root=args.backup_root,
            max_backups=args.max_backups
        )
        backup._cleanup_old_backups()
        print("Cleanup completed.")
        return
    
    asyncio.run(run_backup(args))

if __name__ == "__main__":
    main() 