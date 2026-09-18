"""
Centralized Audit Logging for Serena
Phase 1: Single authoritative audit trail for all operations

This module provides the AuditLog class that captures lifecycle events with correlation IDs.
Audit logging records events; it does not authorize or execute them.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import uuid

# Try to import Phase 1 core data contracts
try:
    from core_data_contracts import AuditEntry, generate_audit_id, generate_correlation_id
    CORE_CONTRACTS_AVAILABLE = True
except ImportError:
    CORE_CONTRACTS_AVAILABLE = False
    
    # Fallback definitions for Phase 1 data contracts
    @dataclass
    class AuditEntry:
        entry_id: str
        event_type: str
        correlation_id: Optional[str]
        task_id: Optional[str]
        agent_id: Optional[str]
        operation: Optional[str]
        details: Dict[str, Any]
        timestamp: float = field(default_factory=time.time)
        outcome: str = "unknown"
        metadata: Dict[str, Any] = field(default_factory=dict)
        
        def to_dict(self) -> Dict:
            return {
                "entry_id": self.entry_id,
                "event_type": self.event_type,
                "correlation_id": self.correlation_id,
                "task_id": self.task_id,
                "agent_id": self.agent_id,
                "operation": self.operation,
                "details": self.details,
                "timestamp": self.timestamp,
                "outcome": self.outcome,
                "metadata": self.metadata
            }
    
    def generate_audit_id() -> str:
        return f"audit_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    
    def generate_correlation_id() -> str:
        return str(uuid.uuid4())


class AuditLog:
    """
    Centralized audit logging system for Serena.
    
    Phase 1: Captures lifecycle events with correlation IDs for tracking.
    Audit logging records events; it does not authorize or execute them.
    """
    
    def __init__(self, log_file: str = "audit.log"):
        """
        Initialize the audit log system.
        
        Args:
            log_file: Path to store audit log entries
        """
        self.log_file = Path(log_file)
        self.audit_entries: List[AuditEntry] = []
        self.load_entries()
    
    def log_operation(self, operation: str, agent_id: str, result: str, 
                     verification: str, correlation_id: str = None, 
                     task_id: str = None, metadata: Dict = None) -> AuditEntry:
        """
        Log an operation execution.
        
        Args:
            operation: The operation that was performed
            agent_id: The agent that performed the operation
            result: The result of the operation
            verification: The verification result
            correlation_id: Correlation ID for tracking
            task_id: Optional task ID
            metadata: Additional metadata
            
        Returns:
            The created audit entry
        """
        entry = AuditEntry(
            entry_id=generate_audit_id(),
            event_type="operation",
            correlation_id=correlation_id,
            task_id=task_id,
            agent_id=agent_id,
            operation=operation,
            details={
                "result": result,
                "verification": verification
            },
            outcome="success" if "error" not in result.lower() else "failed",
            metadata=metadata or {}
        )
        
        self.audit_entries.append(entry)
        self._write_entry(entry)
        return entry
    
    def log_permission_decision(self, operation: str, decision: Dict, 
                               correlation_id: str = None, agent_id: str = None) -> AuditEntry:
        """
        Log a permission decision.
        
        Args:
            operation: The operation that was decided upon
            decision: The permission decision details
            correlation_id: Correlation ID for tracking
            agent_id: Optional agent ID
            
        Returns:
            The created audit entry
        """
        entry = AuditEntry(
            entry_id=generate_audit_id(),
            event_type="permission_decision",
            correlation_id=correlation_id,
            task_id=None,
            agent_id=agent_id,
            operation=operation,
            details=decision,
            outcome="allowed" if decision.get("allowed") else "denied",
            metadata={"decision_type": "authorization"}
        )
        
        self.audit_entries.append(entry)
        self._write_entry(entry)
        return entry
    
    def log_approval_request(self, request: Dict, correlation_id: str = None) -> AuditEntry:
        """
        Log an approval request.
        
        Args:
            request: The approval request details
            correlation_id: Correlation ID for tracking
            
        Returns:
            The created audit entry
        """
        entry = AuditEntry(
            entry_id=generate_audit_id(),
            event_type="approval_request",
            correlation_id=correlation_id,
            task_id=None,
            agent_id=request.get("agent_id"),
            operation=request.get("operation"),
            details=request,
            outcome="pending",
            metadata={"approval_type": "human_in_the_loop"}
        )
        
        self.audit_entries.append(entry)
        self._write_entry(entry)
        return entry
    
    def log_execution(self, tool: str, operation: str, result: Any, 
                     success: bool, correlation_id: str = None, 
                     agent_id: str = None, task_id: str = None) -> AuditEntry:
        """
        Log a tool execution.
        
        Args:
            tool: The tool that was executed
            operation: The operation performed
            result: The execution result
            success: Whether execution was successful
            correlation_id: Correlation ID for tracking
            agent_id: Optional agent ID
            task_id: Optional task ID
            
        Returns:
            The created audit entry
        """
        entry = AuditEntry(
            entry_id=generate_audit_id(),
            event_type="execution",
            correlation_id=correlation_id,
            task_id=task_id,
            agent_id=agent_id,
            operation=f"{tool}:{operation}",
            details={
                "tool": tool,
                "result": str(result) if result else None
            },
            outcome="success" if success else "failed",
            metadata={"execution_type": "tool"}
        )
        
        self.audit_entries.append(entry)
        self._write_entry(entry)
        return entry
    
    def log_verification(self, operation: str, status: str, details: str,
                        correlation_id: str = None, agent_id: str = None) -> AuditEntry:
        """
        Log a verification check.
        
        Args:
            operation: The operation that was verified
            status: The verification status
            details: Verification details
            correlation_id: Correlation ID for tracking
            agent_id: Optional agent ID
            
        Returns:
            The created audit entry
        """
        entry = AuditEntry(
            entry_id=generate_audit_id(),
            event_type="verification",
            correlation_id=correlation_id,
            task_id=None,
            agent_id=agent_id,
            operation=operation,
            details={
                "status": status,
                "details": details
            },
            outcome=status,
            metadata={"verification_type": "post_execution"}
        )
        
        self.audit_entries.append(entry)
        self._write_entry(entry)
        return entry
    
    def log_error(self, error_type: str, error_message: str, 
                 context: Dict = None, correlation_id: str = None) -> AuditEntry:
        """
        Log an error event.
        
        Args:
            error_type: The type of error
            error_message: The error message
            context: Additional context
            correlation_id: Correlation ID for tracking
            
        Returns:
            The created audit entry
        """
        entry = AuditEntry(
            entry_id=generate_audit_id(),
            event_type="error",
            correlation_id=correlation_id,
            task_id=None,
            agent_id=None,
            operation=error_type,
            details={
                "error_message": error_message,
                "context": context or {}
            },
            outcome="failed",
            metadata={"error_type": error_type}
        )
        
        self.audit_entries.append(entry)
        self._write_entry(entry)
        return entry
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """
        Get recent audit log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of audit entries as dictionaries
        """
        recent = self.audit_entries[-limit:]
        return [entry.to_dict() for entry in recent]
    
    def get_logs_by_correlation_id(self, correlation_id: str) -> List[Dict]:
        """
        Get all audit entries for a specific correlation ID.
        
        Args:
            correlation_id: The correlation ID to search for
            
        Returns:
            List of audit entries as dictionaries
        """
        matching = [entry for entry in self.audit_entries 
                   if entry.correlation_id == correlation_id]
        return [entry.to_dict() for entry in matching]
    
    def get_logs_by_event_type(self, event_type: str, limit: int = 100) -> List[Dict]:
        """
        Get audit entries by event type.
        
        Args:
            event_type: The event type to filter by
            limit: Maximum number of entries to return
            
        Returns:
            List of audit entries as dictionaries
        """
        matching = [entry for entry in self.audit_entries 
                   if entry.event_type == event_type]
        recent = matching[-limit:]
        return [entry.to_dict() for entry in recent]
    
    def get_logs_by_agent(self, agent_id: str, limit: int = 100) -> List[Dict]:
        """
        Get audit entries for a specific agent.
        
        Args:
            agent_id: The agent ID to filter by
            limit: Maximum number of entries to return
            
        Returns:
            List of audit entries as dictionaries
        """
        matching = [entry for entry in self.audit_entries 
                   if entry.agent_id == agent_id]
        recent = matching[-limit:]
        return [entry.to_dict() for entry in recent]
    
    def generate_audit_report(self, start_date: datetime = None, 
                            end_date: datetime = None) -> str:
        """
        Generate a comprehensive audit report.
        
        Args:
            start_date: Start date for report (defaults to 24 hours ago)
            end_date: End date for report (defaults to now)
            
        Returns:
            Formatted audit report
        """
        if start_date is None:
            start_date = datetime.fromtimestamp(time.time() - 86400)  # 24 hours ago
        if end_date is None:
            end_date = datetime.now()
        
        start_timestamp = start_date.timestamp()
        end_timestamp = end_date.timestamp()
        
        # Filter entries by date range
        filtered = [entry for entry in self.audit_entries 
                   if start_timestamp <= entry.timestamp <= end_timestamp]
        
        # Generate statistics
        total_entries = len(filtered)
        by_event_type = {}
        by_outcome = {}
        
        for entry in filtered:
            # Count by event type
            event_type = entry.event_type
            by_event_type[event_type] = by_event_type.get(event_type, 0) + 1
            
            # Count by outcome
            outcome = entry.outcome
            by_outcome[outcome] = by_outcome.get(outcome, 0) + 1
        
        # Build report
        report = []
        report.append("=" * 60)
        report.append(f"Audit Report: {start_date} to {end_date}")
        report.append("=" * 60)
        report.append(f"Total Entries: {total_entries}")
        report.append("")
        
        report.append("By Event Type:")
        for event_type, count in sorted(by_event_type.items()):
            report.append(f"  {event_type}: {count}")
        report.append("")
        
        report.append("By Outcome:")
        for outcome, count in sorted(by_outcome.items()):
            report.append(f"  {outcome}: {count}")
        report.append("")
        
        report.append("Recent Errors:")
        error_entries = [e for e in filtered if e.event_type == "error"][-10:]
        for entry in error_entries:
            report.append(f"  [{entry.timestamp}] {entry.operation}: {entry.details.get('error_message', 'Unknown')}")
        
        return "\n".join(report)
    
    def _write_entry(self, entry: AuditEntry):
        """Write an audit entry to the log file."""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except Exception as e:
            print(f"Error writing audit entry: {e}")
    
    def load_entries(self):
        """Load audit entries from the log file."""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                entry = AuditEntry(
                                    entry_id=data["entry_id"],
                                    event_type=data["event_type"],
                                    correlation_id=data.get("correlation_id"),
                                    task_id=data.get("task_id"),
                                    agent_id=data.get("agent_id"),
                                    operation=data.get("operation"),
                                    details=data["details"],
                                    timestamp=data["timestamp"],
                                    outcome=data.get("outcome", "unknown"),
                                    metadata=data.get("metadata", {})
                                )
                                self.audit_entries.append(entry)
                            except Exception as e:
                                print(f"Error loading audit entry: {e}")
        except Exception as e:
            print(f"Error loading audit log: {e}")
    
    def archive_old_entries(self, older_than_days: int = 30):
        """
        Archive audit entries older than specified days.
        
        Args:
            older_than_days: Archive entries older than this many days
        """
        cutoff_time = time.time() - (older_than_days * 86400)
        
        # Separate old and new entries
        old_entries = [e for e in self.audit_entries if e.timestamp < cutoff_time]
        self.audit_entries = [e for e in self.audit_entries if e.timestamp >= cutoff_time]
        
        # Write old entries to archive file
        if old_entries:
            archive_file = self.log_file.with_suffix(f".archive_{int(time.time())}")
            try:
                with open(archive_file, 'w', encoding='utf-8') as f:
                    for entry in old_entries:
                        f.write(json.dumps(entry.to_dict()) + "\n")
                print(f"Archived {len(old_entries)} entries to {archive_file}")
            except Exception as e:
                print(f"Error archiving entries: {e}")
    
    def get_stats(self) -> Dict:
        """Get statistics about the audit log."""
        total = len(self.audit_entries)
        
        by_event_type = {}
        by_outcome = {}
        by_agent = {}
        
        for entry in self.audit_entries:
            # Count by event type
            event_type = entry.event_type
            by_event_type[event_type] = by_event_type.get(event_type, 0) + 1
            
            # Count by outcome
            outcome = entry.outcome
            by_outcome[outcome] = by_outcome.get(outcome, 0) + 1
            
            # Count by agent
            if entry.agent_id:
                by_agent[entry.agent_id] = by_agent.get(entry.agent_id, 0) + 1
        
        return {
            "total_entries": total,
            "by_event_type": by_event_type,
            "by_outcome": by_outcome,
            "by_agent": by_agent,
            "log_file": str(self.log_file)
        }


# Global instance
_audit_log = None

def get_audit_log(log_file: str = "audit.log") -> AuditLog:
    """Get or create the global AuditLog instance."""
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog(log_file)
    return _audit_log


if __name__ == "__main__":
    # Test the audit log system
    print("Testing Audit Log System...")
    
    audit_log = AuditLog("test_audit.log")
    
    # Test logging various events
    print("\n=== Testing Operation Logging ===")
    audit_log.log_operation(
        operation="read_file",
        agent_id="TestAgent",
        result="Success",
        verification="Passed",
        correlation_id="test-correlation-1"
    )
    
    print("\n=== Testing Permission Decision Logging ===")
    audit_log.log_permission_decision(
        operation="delete_file",
        decision={"allowed": False, "reason": "Dangerous operation"},
        correlation_id="test-correlation-2"
    )
    
    print("\n=== Testing Execution Logging ===")
    audit_log.log_execution(
        tool="write_file",
        operation="write",
        result="File written successfully",
        success=True,
        correlation_id="test-correlation-3"
    )
    
    print("\n=== Testing Verification Logging ===")
    audit_log.log_verification(
        operation="write_file",
        status="passed",
        details="File exists and contains expected content",
        correlation_id="test-correlation-3"
    )
    
    # Get recent logs
    print("\n=== Recent Logs ===")
    recent = audit_log.get_recent_logs(5)
    for entry in recent:
        print(f"[{entry['event_type']}] {entry['operation']} - {entry['outcome']}")
    
    # Get stats
    print("\n=== Audit Stats ===")
    stats = audit_log.get_stats()
    print(json.dumps(stats, indent=2))
    
    # Generate report
    print("\n=== Audit Report ===")
    report = audit_log.generate_audit_report()
    print(report)
    
    # Cleanup
    if Path("test_audit.log").exists():
        Path("test_audit.log").unlink()
    
    print("\n✅ Audit Log System Test Passed!")