"""
Performance Analyzer for Strategic Intelligence.

Analyzes system-wide performance metrics.

Author: AFC3 Strategic Intelligence
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SystemPerformanceReport:
    """System performance report."""
    timestamp: str
    total_experiments: int
    successful_experiments: int
    failed_experiments: int
    avg_sharpe: float
    avg_drawdown: float
    compute_throughput: float
    job_failure_rate: float
    pipeline_throughput: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_experiments": self.total_experiments,
            "successful_experiments": self.successful_experiments,
            "failed_experiments": self.failed_experiments,
            "avg_sharpe": self.avg_sharpe,
            "avg_drawdown": self.avg_drawdown,
            "compute_throughput": self.compute_throughput,
            "job_failure_rate": self.job_failure_rate,
            "pipeline_throughput": self.pipeline_throughput
        }


class PerformanceAnalyzer:
    """Analyzes system performance."""
    
    def __init__(self):
        self.history: List[SystemPerformanceReport] = []
    
    def analyze(
        self,
        experiments: List[Dict[str, Any]],
        compute_stats: Dict[str, Any],
        pipeline_stats: Dict[str, Any]
    ) -> SystemPerformanceReport:
        """Analyze system performance."""
        total = len(experiments)
        successful = sum(1 for e in experiments if e.get("status") == "approved")
        failed = sum(1 for e in experiments if e.get("status") == "rejected")
        
        # Calculate metrics
        sharpes = [e.get("sharpe_ratio", 0) for e in experiments]
        avg_sharpe = sum(sharpes) / len(sharpes) if sharpes else 0
        
        drawdowns = [e.get("max_drawdown", 0) for e in experiments]
        avg_drawdown = sum(drawdowns) / len(drawdowns) if drawdowns else 0
        
        # Compute stats
        total_jobs = compute_stats.get("total", 0)
        failed_jobs = compute_stats.get("failed", 0)
        job_failure_rate = failed_jobs / total_jobs if total_jobs > 0 else 0
        
        # Create report
        report = SystemPerformanceReport(
            timestamp=datetime.utcnow().isoformat(),
            total_experiments=total,
            successful_experiments=successful,
            failed_experiments=failed,
            avg_sharpe=avg_sharpe,
            avg_drawdown=avg_drawdown,
            compute_throughput=compute_stats.get("completed", 0),
            job_failure_rate=job_failure_rate,
            pipeline_throughput=pipeline_stats.get("completed", 0)
        )
        
        self.history.append(report)
        return report
    
    def get_trend(self, metric: str, periods: int = 5) -> str:
        """Get trend for a metric."""
        if len(self.history) < 2:
            return "stable"
        
        recent = self.history[-periods:]
        values = [getattr(r, metric, 0) for r in recent]
        
        if not values:
            return "stable"
        
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        if second_half > first_half * 1.1:
            return "increasing"
        elif second_half < first_half * 0.9:
            return "decreasing"
        return "stable"
