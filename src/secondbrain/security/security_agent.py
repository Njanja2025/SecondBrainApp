"""
Security Agent for smart contract vulnerability scanning and system protection.
"""
import os
import re
from typing import List, Tuple, Dict, Any
import logging
from ..voice.respond_with_voice import respond_with_voice
from ..core.phantom_mcp import PhantomMCP
from ..phantom.phantom_core import PhantomCore

logger = logging.getLogger(__name__)

class SecurityAgent:
    def __init__(self):
        self.threats = []
        self.phantom_mcp = PhantomMCP()
        self.phantom = PhantomCore()
        self.vulnerability_patterns = {
            "tx.origin": {
                "pattern": r"tx\.origin",
                "severity": "HIGH",
                "description": "Use of tx.origin is dangerous - can be manipulated by attackers"
            },
            "call.value": {
                "pattern": r"call\.value",
                "severity": "HIGH",
                "description": "Use of call.value is risky - use transfer() or send() instead"
            },
            "selfdestruct": {
                "pattern": r"selfdestruct|suicide",
                "severity": "CRITICAL",
                "description": "Use of selfdestruct can permanently destroy contract"
            },
            "reentrancy": {
                "pattern": r"\.call{.*?\bvalue:",
                "severity": "CRITICAL",
                "description": "Potential reentrancy vulnerability"
            },
            "unchecked_return": {
                "pattern": r"\.send\(|\.call\{",
                "severity": "MEDIUM",
                "description": "Unchecked return value from external call"
            },
            "timestamp_dependency": {
                "pattern": r"block\.timestamp|now",
                "severity": "MEDIUM",
                "description": "Timestamp manipulation vulnerability"
            },
            "assembly": {
                "pattern": r"assembly\s*{",
                "severity": "WARNING",
                "description": "Use of assembly - ensure it's necessary"
            }
        }

    async def initialize(self):
        """Initialize security agent with Phantom MCP integration."""
        await self.phantom_mcp.initialize()
        self.phantom.log_event("Security Agent", "Initialized with Phantom MCP")
        logger.info("Security Agent initialized with Phantom MCP")

    async def scan_contract(self, file_path: str) -> Dict[str, Any]:
        """
        Scan a smart contract for security vulnerabilities.
        Returns a detailed security report.
        """
        try:
            if not os.path.exists(file_path):
                error_msg = f"Contract file not found: {file_path}"
                self.phantom.log_event("Contract Scan", error_msg, "ERROR")
                logger.error(error_msg)
                await respond_with_voice(error_msg)
                return {"status": "error", "message": error_msg}

            self.phantom.log_event("Contract Scan", f"Starting scan of {file_path}")
            
            issues = []
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                # Scan for known vulnerability patterns
                for vuln_name, vuln_info in self.vulnerability_patterns.items():
                    matches = re.finditer(vuln_info["pattern"], content)
                    for match in matches:
                        line_no = content[:match.start()].count('\n') + 1
                        issue = {
                            "line": line_no,
                            "type": vuln_name,
                            "severity": vuln_info["severity"],
                            "description": vuln_info["description"],
                            "code": lines[line_no - 1].strip()
                        }
                        issues.append(issue)
                        
                        # Log critical and high severity issues
                        if issue["severity"] in ["CRITICAL", "HIGH"]:
                            self.phantom.log_event(
                                "Vulnerability",
                                f"{issue['severity']}: {issue['type']} at line {line_no}",
                                "WARNING"
                            )

            # Sort issues by severity
            severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "WARNING": 3}
            issues.sort(key=lambda x: severity_order[x["severity"]])

            # Store threats for later reference
            self.threats = issues

            # Generate security report
            report = self._generate_security_report(issues, file_path)
            
            # Log scan completion
            self.phantom.log_event(
                "Contract Scan",
                f"Completed scan of {file_path}. Found {len(issues)} issues."
            )
            
            # Notify through voice
            if issues:
                critical_count = sum(1 for i in issues if i["severity"] == "CRITICAL")
                high_count = sum(1 for i in issues if i["severity"] == "HIGH")
                
                msg = f"Security scan completed. Found {len(issues)} issues: "
                if critical_count:
                    msg += f"{critical_count} critical, "
                if high_count:
                    msg += f"{high_count} high severity, "
                msg += "Please review the security report."
                
                await respond_with_voice(msg)
            else:
                await respond_with_voice("Contract scan completed. No vulnerabilities found.")

            return report

        except Exception as e:
            error_msg = f"Error scanning contract: {str(e)}"
            self.phantom.log_event("Contract Scan", error_msg, "ERROR")
            logger.error(error_msg)
            await respond_with_voice("Error during security scan")
            return {"status": "error", "message": error_msg}

    def _generate_security_report(self, issues: List[Dict], file_path: str) -> Dict[str, Any]:
        """Generate a detailed security report."""
        report = {
            "status": "completed",
            "file": file_path,
            "timestamp": self.phantom_mcp.state.last_update.isoformat(),
            "summary": {
                "total_issues": len(issues),
                "critical": sum(1 for i in issues if i["severity"] == "CRITICAL"),
                "high": sum(1 for i in issues if i["severity"] == "HIGH"),
                "medium": sum(1 for i in issues if i["severity"] == "MEDIUM"),
                "warning": sum(1 for i in issues if i["severity"] == "WARNING")
            },
            "issues": issues,
            "system_health": self.phantom_mcp.state.system_health
        }

        # Log report summary
        self.phantom.log_event(
            "Security Report",
            f"Generated for {file_path}: {report['summary']['total_issues']} issues found"
        )

        # Log detailed report
        logger.info("Security Report Generated:")
        logger.info(f"File: {file_path}")
        logger.info(f"Total Issues: {report['summary']['total_issues']}")
        for issue in issues:
            logger.info(f"[{issue['severity']}] Line {issue['line']}: {issue['description']}")

        return report

    async def monitor_system(self):
        """
        Continuous system security monitoring.
        Integrates with Phantom MCP for advanced threat detection.
        """
        try:
            system_status = self.phantom_mcp.get_system_status()
            if system_status["system_health"] < 0.7:
                self.phantom.log_event(
                    "System Health",
                    f"Low system health detected: {system_status['system_health']}",
                    "WARNING"
                )
                await self._handle_security_threat()
        except Exception as e:
            error_msg = f"Error in security monitoring: {str(e)}"
            self.phantom.log_event("Monitor Error", error_msg, "ERROR")
            logger.error(error_msg)

    async def _handle_security_threat(self):
        """Handle detected security threats."""
        try:
            # Log threat detection
            self.phantom.log_event(
                "Security Threat",
                "Initiating threat response procedures",
                "WARNING"
            )
            
            # Create security checkpoint
            await self.phantom_mcp.create_backup("security_threat")
            
            # Trigger system optimization
            await self.phantom_mcp.improve_system("process_optimization")
            
            # Log security event
            logger.warning("Security threat detected - protective measures activated")
            
        except Exception as e:
            error_msg = f"Error handling security threat: {str(e)}"
            self.phantom.log_event("Threat Response", error_msg, "ERROR")
            logger.error(error_msg)

    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status."""
        phantom_status = self.phantom.get_status()
        return {
            "active_threats": len(self.threats),
            "last_scan": self.phantom_mcp.state.last_update.isoformat(),
            "system_health": self.phantom_mcp.state.system_health,
            "security_level": "HIGH" if self.phantom_mcp.state.system_health > 0.8 else "MEDIUM",
            "phantom_status": phantom_status
        } 