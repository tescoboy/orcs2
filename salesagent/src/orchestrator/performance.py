"""
Performance monitoring and optimization for the orchestrator
"""
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, UTC
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for orchestrator operations"""
    start_time: float
    end_time: Optional[float] = None
    total_agents_contacted: int = 0
    successful_agents: int = 0
    failed_agents: int = 0
    total_products_found: int = 0
    total_products_after_dedupe: int = 0
    total_products_after_sort: int = 0
    agent_response_times: Dict[str, float] = field(default_factory=dict)
    agent_product_counts: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    @property
    def duration_ms(self) -> float:
        """Calculate total duration in milliseconds"""
        if self.end_time is None:
            return (time.time() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_agents_contacted == 0:
            return 0.0
        return (self.successful_agents / self.total_agents_contacted) * 100
    
    @property
    def avg_response_time_ms(self) -> float:
        """Calculate average agent response time"""
        if not self.agent_response_times:
            return 0.0
        return statistics.mean(self.agent_response_times.values())
    
    @property
    def median_response_time_ms(self) -> float:
        """Calculate median agent response time"""
        if not self.agent_response_times:
            return 0.0
        return statistics.median(self.agent_response_times.values())
    
    @property
    def max_response_time_ms(self) -> float:
        """Get maximum agent response time"""
        if not self.agent_response_times:
            return 0.0
        return max(self.agent_response_times.values())
    
    @property
    def min_response_time_ms(self) -> float:
        """Get minimum agent response time"""
        if not self.agent_response_times:
            return 0.0
        return min(self.agent_response_times.values())


class PerformanceMonitor:
    """Monitor and track orchestrator performance metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.agent_performance: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.tenant_performance: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.total_requests = 0
        self.total_successful_requests = 0
    
    def start_operation(self) -> PerformanceMetrics:
        """Start tracking a new operation"""
        metrics = PerformanceMetrics(start_time=time.time())
        return metrics
    
    def end_operation(self, metrics: PerformanceMetrics) -> None:
        """End tracking an operation and store metrics"""
        metrics.end_time = time.time()
        self.metrics_history.append(metrics)
        self.total_requests += 1
        
        if metrics.successful_agents > 0:
            self.total_successful_requests += 1
        
        # Track agent performance
        for agent_id, response_time in metrics.agent_response_times.items():
            self.agent_performance[agent_id].append(response_time)
        
        # Track errors
        for error in metrics.errors:
            self.error_counts[error] += 1
        
        logger.info(f"Operation completed: {metrics.duration_ms:.2f}ms, "
                   f"Success rate: {metrics.success_rate:.1f}%, "
                   f"Products: {metrics.total_products_after_sort}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        recent_metrics = list(self.metrics_history)[-100:]  # Last 100 operations
        
        # Calculate overall statistics
        durations = [m.duration_ms for m in recent_metrics]
        success_rates = [m.success_rate for m in recent_metrics]
        response_times = []
        for m in recent_metrics:
            response_times.extend(m.agent_response_times.values())
        
        summary = {
            "total_requests": self.total_requests,
            "total_successful_requests": self.total_successful_requests,
            "overall_success_rate": (self.total_successful_requests / max(self.total_requests, 1)) * 100,
            "recent_operations": len(recent_metrics),
            "avg_duration_ms": statistics.mean(durations) if durations else 0,
            "median_duration_ms": statistics.median(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "avg_success_rate": statistics.mean(success_rates) if success_rates else 0,
            "avg_response_time_ms": statistics.mean(response_times) if response_times else 0,
            "median_response_time_ms": statistics.median(response_times) if response_times else 0,
            "total_agents_tracked": len(self.agent_performance),
            "total_errors": sum(self.error_counts.values()),
            "top_errors": dict(sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        return summary
    
    def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """Get performance metrics for a specific agent"""
        if agent_id not in self.agent_performance:
            return {"status": "agent_not_found"}
        
        response_times = list(self.agent_performance[agent_id])
        
        return {
            "agent_id": agent_id,
            "total_calls": len(response_times),
            "avg_response_time_ms": statistics.mean(response_times) if response_times else 0,
            "median_response_time_ms": statistics.median(response_times) if response_times else 0,
            "max_response_time_ms": max(response_times) if response_times else 0,
            "min_response_time_ms": min(response_times) if response_times else 0,
            "recent_response_times": response_times[-10:]  # Last 10 calls
        }
    
    def get_top_performing_agents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing agents by average response time"""
        agent_stats = []
        
        for agent_id, response_times in self.agent_performance.items():
            if response_times:
                avg_time = statistics.mean(response_times)
                agent_stats.append({
                    "agent_id": agent_id,
                    "avg_response_time_ms": avg_time,
                    "total_calls": len(response_times)
                })
        
        # Sort by average response time (fastest first)
        agent_stats.sort(key=lambda x: x["avg_response_time_ms"])
        return agent_stats[:limit]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary and trends"""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_breakdown": dict(self.error_counts),
            "top_errors": dict(sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        }


class ConcurrencyOptimizer:
    """Optimize concurrent operations for better performance"""
    
    def __init__(self, max_concurrent: int = 12, timeout_seconds: int = 10):
        self.max_concurrent = max_concurrent
        self.timeout_seconds = timeout_seconds
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
    
    async def execute_with_semaphore(self, coro, *args, **kwargs):
        """Execute a coroutine with semaphore control"""
        async with self.semaphore:
            self.active_tasks += 1
            try:
                result = await asyncio.wait_for(coro(*args, **kwargs), timeout=self.timeout_seconds)
                self.completed_tasks += 1
                return result
            except asyncio.TimeoutError:
                self.failed_tasks += 1
                logger.warning(f"Task timed out after {self.timeout_seconds}s")
                raise
            except Exception as e:
                self.failed_tasks += 1
                logger.error(f"Task failed: {e}")
                raise
            finally:
                self.active_tasks -= 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get concurrency statistics"""
        return {
            "max_concurrent": self.max_concurrent,
            "active_tasks": self.active_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": (self.completed_tasks / max(self.completed_tasks + self.failed_tasks, 1)) * 100
        }


class CacheManager:
    """Simple in-memory cache for frequently accessed data"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            return None
        
        # Check TTL
        if time.time() - self.access_times[key] > self.ttl_seconds:
            self._remove(key)
            return None
        
        # Update access time
        self.access_times[key] = time.time()
        return self.cache[key]["value"]
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        # Evict oldest if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            self._remove(oldest_key)
        
        self.cache[key] = {"value": value, "created": time.time()}
        self.access_times[key] = time.time()
    
    def _remove(self, key: str) -> None:
        """Remove key from cache"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "hit_rate": 0.0  # TODO: Implement hit rate tracking
        }


# Global instances
performance_monitor = PerformanceMonitor()
concurrency_optimizer = ConcurrencyOptimizer()
cache_manager = CacheManager()
