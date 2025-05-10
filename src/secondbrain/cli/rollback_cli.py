"""
Command-line interface for SecondBrain backup and rollback management.
"""

import os
import sys
import argparse
from datetime import datetime
from typing import Optional, List, Dict

from ..monitoring.rollback_manager import rollback_manager

def list_backups(args):
    """List available backups.
    
    Args:
        args: Command line arguments
    """
    backups = rollback_manager.list_backups()
    
    if not backups:
        print("No backups available.")
        return
    
    print("\nAvailable Backups:")
    print("-" * 80)
    print(f"{'Version':<15} {'Timestamp':<20} {'Status':<10} {'Notes':<30}")
    print("-" * 80)
    
    for backup in backups:
        timestamp = datetime.strptime(
            backup['timestamp'],
            "%Y%m%d_%H%M%S"
        ).strftime("%Y-%m-%d %H:%M:%S")
        
        print(
            f"{backup['version']:<15} "
            f"{timestamp:<20} "
            f"{backup['status']:<10} "
            f"{backup['notes']:<30}"
        )

def create_backup(args):
    """Create a new backup.
    
    Args:
        args: Command line arguments
    """
    notes = args.notes if args.notes else "Manual backup"
    
    success = rollback_manager.create_backup(notes=notes)
    
    if success:
        print("Backup created successfully.")
    else:
        print("Failed to create backup.")
        sys.exit(1)

def restore_backup(args):
    """Restore a backup version.
    
    Args:
        args: Command line arguments
    """
    if not args.version:
        print("Error: Version must be specified.")
        sys.exit(1)
    
    success = rollback_manager.rollback(args.version)
    
    if success:
        print(f"Successfully restored version {args.version}.")
    else:
        print(f"Failed to restore version {args.version}.")
        sys.exit(1)

def cleanup_backups(args):
    """Clean up old backups.
    
    Args:
        args: Command line arguments
    """
    keep_count = args.keep if args.keep else 5
    
    success = rollback_manager.cleanup_old_backups(keep_count)
    
    if success:
        print(f"Successfully cleaned up old backups. Keeping {keep_count} most recent.")
    else:
        print("Failed to clean up old backups.")
        sys.exit(1)

def main():
    """Main entry point for the rollback CLI."""
    parser = argparse.ArgumentParser(
        description="SecondBrain Backup and Rollback Management"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List backups command
    list_parser = subparsers.add_parser(
        "list",
        help="List available backups"
    )
    list_parser.set_defaults(func=list_backups)
    
    # Create backup command
    create_parser = subparsers.add_parser(
        "create",
        help="Create a new backup"
    )
    create_parser.add_argument(
        "--notes",
        help="Notes for the backup"
    )
    create_parser.set_defaults(func=create_backup)
    
    # Restore backup command
    restore_parser = subparsers.add_parser(
        "restore",
        help="Restore a backup version"
    )
    restore_parser.add_argument(
        "version",
        help="Version to restore"
    )
    restore_parser.set_defaults(func=restore_backup)
    
    # Cleanup backups command
    cleanup_parser = subparsers.add_parser(
        "cleanup",
        help="Clean up old backups"
    )
    cleanup_parser.add_argument(
        "--keep",
        type=int,
        help="Number of backups to keep"
    )
    cleanup_parser.set_defaults(func=cleanup_backups)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)

if __name__ == "__main__":
    main() 