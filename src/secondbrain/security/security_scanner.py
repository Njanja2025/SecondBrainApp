"""
Enhanced security scanner with advanced threat detection.
"""

import os
import re
import json
import hashlib
import logging
import subprocess
from typing import Dict, List, Any
from datetime import datetime
from ..phantom.phantom_core import PhantomCore

logger = logging.getLogger(__name__)


class SecurityScanner:
    def __init__(self, phantom: PhantomCore):
        """Initialize security scanner."""
        self.phantom = phantom
        self.threat_database = self._load_threat_database()
        self.file_hashes = {}
        self.known_processes = set()
        self.network_baseline = {}

    def _load_threat_database(self) -> Dict[str, Any]:
        """Load threat signatures database."""
        try:
            with open("config/threat_signatures.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Threat signatures database not found, using defaults")
            return {
                "malicious_patterns": [
                    r"(eval\(.*\))",
                    r"((?:exec|system|popen)\(.*\))",
                    r"((?:os|subprocess)\..*(?:system|popen|exec).*)",
                ],
                "suspicious_imports": [
                    "subprocess",
                    "os.system",
                    "pickle",
                ],
                "network_indicators": [
                    r"\b(?:\d{1,3}\.){3}\d{1,3}\b",  # IP addresses
                    r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}",  # Domains
                ],
                "critical_files": [
                    "config.json",
                    ".env",
                    "private_key",
                ],
            }

    def scan_file(self, filepath: str) -> Dict[str, Any]:
        """
        Perform deep security scan of a file.

        Args:
            filepath: Path to file to scan

        Returns:
            Scan results
        """
        try:
            with open(filepath, "r") as f:
                content = f.read()

            # Calculate file hash
            file_hash = hashlib.sha256(content.encode()).hexdigest()

            # Check if file was modified
            if filepath in self.file_hashes:
                if self.file_hashes[filepath] != file_hash:
                    self.phantom.log_event(
                        "Security Scan", f"File modified: {filepath}", "WARNING"
                    )

            self.file_hashes[filepath] = file_hash

            # Scan for threats
            threats = []

            # Check for malicious patterns
            for pattern in self.threat_database["malicious_patterns"]:
                matches = re.finditer(pattern, content)
                for match in matches:
                    threats.append(
                        {
                            "type": "malicious_pattern",
                            "pattern": pattern,
                            "match": match.group(),
                            "line": content.count("\n", 0, match.start()) + 1,
                            "severity": "HIGH",
                        }
                    )

            # Check for suspicious imports
            for imp in self.threat_database["suspicious_imports"]:
                if f"import {imp}" in content or f"from {imp}" in content:
                    threats.append(
                        {
                            "type": "suspicious_import",
                            "import": imp,
                            "severity": "MEDIUM",
                        }
                    )

            # Check for network indicators
            for pattern in self.threat_database["network_indicators"]:
                matches = re.finditer(pattern, content)
                for match in matches:
                    threats.append(
                        {
                            "type": "network_indicator",
                            "indicator": match.group(),
                            "line": content.count("\n", 0, match.start()) + 1,
                            "severity": "MEDIUM",
                        }
                    )

            # Generate report
            report = {
                "filepath": filepath,
                "scan_time": datetime.now().isoformat(),
                "file_hash": file_hash,
                "threats_found": len(threats),
                "threats": threats,
                "risk_level": (
                    "HIGH"
                    if any(t["severity"] == "HIGH" for t in threats)
                    else (
                        "MEDIUM"
                        if any(t["severity"] == "MEDIUM" for t in threats)
                        else "LOW"
                    )
                ),
            }

            # Log findings
            if threats:
                self.phantom.log_event(
                    "Security Scan",
                    f"Found {len(threats)} threats in {filepath}",
                    "WARNING",
                )

            return report

        except Exception as e:
            error_msg = f"Error scanning file {filepath}: {str(e)}"
            self.phantom.log_event("Security Scan", error_msg, "ERROR")
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    def scan_directory(self, directory: str) -> Dict[str, Any]:
        """Recursively scan a directory for security threats."""
        try:
            results = {
                "directory": directory,
                "scan_time": datetime.now().isoformat(),
                "files_scanned": 0,
                "threats_found": 0,
                "reports": [],
            }

            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith((".py", ".js", ".sol", ".json", ".env")):
                        filepath = os.path.join(root, file)
                        report = self.scan_file(filepath)
                        results["files_scanned"] += 1
                        if "threats" in report:
                            results["threats_found"] += len(report["threats"])
                            results["reports"].append(report)

            return results

        except Exception as e:
            error_msg = f"Error scanning directory {directory}: {str(e)}"
            self.phantom.log_event("Security Scan", error_msg, "ERROR")
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    def scan_running_processes(self) -> Dict[str, Any]:
        """Scan running processes for suspicious activity."""
        try:
            current_processes = set()
            suspicious_processes = []

            # Get all running processes
            for proc in subprocess.check_output(["ps", "aux"]).decode().split("\n"):
                if proc:
                    current_processes.add(proc)

                    # Check for new processes
                    if proc not in self.known_processes:
                        suspicious_processes.append(
                            {
                                "process": proc,
                                "type": "new_process",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

            # Check for terminated processes
            terminated_processes = self.known_processes - current_processes
            for proc in terminated_processes:
                suspicious_processes.append(
                    {
                        "process": proc,
                        "type": "terminated_process",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            # Update known processes
            self.known_processes = current_processes

            return {
                "scan_time": datetime.now().isoformat(),
                "total_processes": len(current_processes),
                "new_processes": len(
                    [p for p in suspicious_processes if p["type"] == "new_process"]
                ),
                "terminated_processes": len(
                    [
                        p
                        for p in suspicious_processes
                        if p["type"] == "terminated_process"
                    ]
                ),
                "suspicious_processes": suspicious_processes,
            }

        except Exception as e:
            error_msg = f"Error scanning processes: {str(e)}"
            self.phantom.log_event("Process Scan", error_msg, "ERROR")
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    def scan_network_activity(self) -> Dict[str, Any]:
        """Monitor network connections for suspicious activity."""
        try:
            connections = []

            # Get current network connections
            for conn in subprocess.check_output(["lsof", "-i"]).decode().split("\n"):
                if conn:
                    connections.append(conn)

            # Compare with baseline
            new_connections = []
            if self.network_baseline:
                new_connections = [
                    conn for conn in connections if conn not in self.network_baseline
                ]

            # Update baseline
            self.network_baseline = set(connections)

            return {
                "scan_time": datetime.now().isoformat(),
                "total_connections": len(connections),
                "new_connections": len(new_connections),
                "connections": connections,
                "suspicious_connections": new_connections,
            }

        except Exception as e:
            error_msg = f"Error scanning network: {str(e)}"
            self.phantom.log_event("Network Scan", error_msg, "ERROR")
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    def check_file_integrity(self, filepath: str) -> Dict[str, Any]:
        """Check file integrity against stored hash."""
        try:
            with open(filepath, "rb") as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()

            if filepath in self.file_hashes:
                if current_hash != self.file_hashes[filepath]:
                    self.phantom.log_event(
                        "File Integrity", f"File modified: {filepath}", "WARNING"
                    )
                    return {
                        "status": "modified",
                        "filepath": filepath,
                        "original_hash": self.file_hashes[filepath],
                        "current_hash": current_hash,
                        "timestamp": datetime.now().isoformat(),
                    }

            self.file_hashes[filepath] = current_hash
            return {
                "status": "unchanged",
                "filepath": filepath,
                "hash": current_hash,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            error_msg = f"Error checking file integrity: {str(e)}"
            self.phantom.log_event("File Integrity", error_msg, "ERROR")
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
