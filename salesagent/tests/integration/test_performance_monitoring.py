"""
Integration tests for performance monitoring system
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from datetime import datetime, UTC

from src.orchestrator.performance import (
    PerformanceMetrics, 
    PerformanceMonitor, 
    ConcurrencyOptimizer, 
    CacheManager
)


class TestPerformanceMonitoring:
    """Test performance monitoring functionality"""
    
    def test_performance_metrics_calculation(self):
        """Test PerformanceMetrics calculations"""
        # Create metrics
        start_time = time.time()
        metrics = PerformanceMetrics(start_time=start_time)
        
        # Add some data
        metrics.total_agents_contacted = 10
        metrics.successful_agents = 8
        metrics.failed_agents = 2
        metrics.total_products_found = 50
        metrics.total_products_after_dedupe = 45
        metrics.total_products_after_sort = 40
        metrics.agent_response_times = {
            "agent_1": 100.0,
            "agent_2": 150.0,
            "agent_3": 200.0
        }
        metrics.agent_product_counts = {
            "agent_1": 20,
            "agent_2": 15,
            "agent_3": 15
        }
        metrics.errors = ["timeout", "connection_error"]
        
        # End the operation
        time.sleep(0.1)  # Simulate some processing time
        metrics.end_time = time.time()
        
        # Test calculations
        assert metrics.duration_ms > 0
        assert metrics.success_rate == 80.0  # 8/10 * 100
        assert metrics.avg_response_time_ms == 150.0  # (100+150+200)/3
        assert metrics.median_response_time_ms == 150.0
        assert metrics.max_response_time_ms == 200.0
        assert metrics.min_response_time_ms == 100.0
    
    def test_performance_monitor_operations(self):
        """Test PerformanceMonitor operations"""
        monitor = PerformanceMonitor(max_history=5)
        
        # Start multiple operations
        metrics1 = monitor.start_operation()
        metrics1.total_agents_contacted = 5
        metrics1.successful_agents = 4
        metrics1.agent_response_times = {"agent_1": 100.0}
        monitor.end_operation(metrics1)
        
        metrics2 = monitor.start_operation()
        metrics2.total_agents_contacted = 3
        metrics2.successful_agents = 3
        metrics2.agent_response_times = {"agent_2": 150.0}
        monitor.end_operation(metrics2)
        
        # Test summary
        summary = monitor.get_performance_summary()
        assert summary["total_requests"] == 2
        assert summary["total_successful_requests"] == 2
        assert summary["overall_success_rate"] == 100.0
        assert summary["recent_operations"] == 2
        assert summary["total_agents_tracked"] == 2
    
    def test_agent_performance_tracking(self):
        """Test agent performance tracking"""
        monitor = PerformanceMonitor()
        
        # Simulate multiple calls to the same agent
        for i in range(5):
            metrics = monitor.start_operation()
            metrics.agent_response_times = {f"agent_1": 100.0 + i * 10}
            monitor.end_operation(metrics)
        
        # Test agent performance
        agent_perf = monitor.get_agent_performance("agent_1")
        assert agent_perf["agent_id"] == "agent_1"
        assert agent_perf["total_calls"] == 5
        assert agent_perf["avg_response_time_ms"] == 120.0  # (100+110+120+130+140)/5
        assert agent_perf["median_response_time_ms"] == 120.0
        assert agent_perf["max_response_time_ms"] == 140.0
        assert agent_perf["min_response_time_ms"] == 100.0
    
    def test_top_performing_agents(self):
        """Test top performing agents ranking"""
        monitor = PerformanceMonitor()
        
        # Add agents with different performance
        agents_data = [
            ("agent_slow", 300.0),
            ("agent_fast", 50.0),
            ("agent_medium", 150.0)
        ]
        
        for agent_id, response_time in agents_data:
            metrics = monitor.start_operation()
            metrics.agent_response_times = {agent_id: response_time}
            monitor.end_operation(metrics)
        
        # Get top performing agents
        top_agents = monitor.get_top_performing_agents(3)
        
        # Should be sorted by response time (fastest first)
        assert len(top_agents) == 3
        assert top_agents[0]["agent_id"] == "agent_fast"
        assert top_agents[0]["avg_response_time_ms"] == 50.0
        assert top_agents[1]["agent_id"] == "agent_medium"
        assert top_agents[2]["agent_id"] == "agent_slow"
    
    def test_error_tracking(self):
        """Test error tracking and summary"""
        monitor = PerformanceMonitor()
        
        # Add operations with errors
        error_types = ["timeout", "connection_error", "timeout", "invalid_response"]
        
        for error in error_types:
            metrics = monitor.start_operation()
            metrics.errors.append(error)
            monitor.end_operation(metrics)
        
        # Test error summary
        error_summary = monitor.get_error_summary()
        assert error_summary["total_errors"] == 4
        assert error_summary["error_breakdown"]["timeout"] == 2
        assert error_summary["error_breakdown"]["connection_error"] == 1
        assert error_summary["error_breakdown"]["invalid_response"] == 1
    
    def test_concurrency_optimizer(self):
        """Test ConcurrencyOptimizer functionality"""
        optimizer = ConcurrencyOptimizer(max_concurrent=2, timeout_seconds=1)
        
        # Test stats
        stats = optimizer.get_stats()
        assert stats["max_concurrent"] == 2
        assert stats["active_tasks"] == 0
        assert stats["completed_tasks"] == 0
        assert stats["failed_tasks"] == 0
        assert stats["success_rate"] == 100.0
    
    async def test_concurrency_optimizer_execution(self):
        """Test ConcurrencyOptimizer with actual coroutines"""
        optimizer = ConcurrencyOptimizer(max_concurrent=2, timeout_seconds=2)
        
        async def mock_coro(delay, should_fail=False):
            await asyncio.sleep(delay)
            if should_fail:
                raise Exception("Test error")
            return "success"
        
        # Test successful execution
        result = await optimizer.execute_with_semaphore(mock_coro, 0.1)
        assert result == "success"
        
        # Test failed execution
        with pytest.raises(Exception, match="Test error"):
            await optimizer.execute_with_semaphore(mock_coro, 0.1, True)
        
        # Test timeout
        with pytest.raises(asyncio.TimeoutError):
            await optimizer.execute_with_semaphore(mock_coro, 3.0)  # Longer than timeout
        
        # Check stats
        stats = optimizer.get_stats()
        assert stats["completed_tasks"] == 1
        assert stats["failed_tasks"] == 2  # 1 error + 1 timeout
    
    def test_cache_manager(self):
        """Test CacheManager functionality"""
        cache = CacheManager(max_size=3, ttl_seconds=1)
        
        # Test basic operations
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") is None
        
        # Test cache size limit
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict key1
        
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
        
        # Test TTL
        time.sleep(1.1)  # Wait for TTL to expire
        assert cache.get("key2") is None  # Expired
        
        # Test clear
        cache.clear()
        assert cache.get("key3") is None
        assert cache.get("key4") is None
        
        # Test stats
        stats = cache.get_stats()
        assert stats["size"] == 0
        assert stats["max_size"] == 3
        assert stats["ttl_seconds"] == 1


class TestPerformanceMonitoringAPI:
    """Test performance monitoring API endpoints"""
    
    def test_performance_summary_endpoint(self, client):
        """Test performance summary endpoint"""
        response = client.get('/monitoring/performance')
        assert response.status_code == 200
        data = response.json
        assert "total_requests" in data or data.get("status") == "no_data"
    
    def test_agent_performance_endpoint(self, client):
        """Test agent performance endpoint"""
        # Test without agent_id (top performers)
        response = client.get('/monitoring/performance/agents')
        assert response.status_code == 200
        data = response.json
        assert "top_performing_agents" in data
        
        # Test with agent_id
        response = client.get('/monitoring/performance/agents?agent_id=test_agent')
        assert response.status_code == 200
        data = response.json
        assert "agent_id" in data or data.get("status") == "agent_not_found"
    
    def test_error_summary_endpoint(self, client):
        """Test error summary endpoint"""
        response = client.get('/monitoring/performance/errors')
        assert response.status_code == 200
        data = response.json
        assert "total_errors" in data
    
    def test_concurrency_stats_endpoint(self, client):
        """Test concurrency stats endpoint"""
        response = client.get('/monitoring/concurrency')
        assert response.status_code == 200
        data = response.json
        assert "max_concurrent" in data
        assert "success_rate" in data
    
    def test_cache_stats_endpoint(self, client):
        """Test cache stats endpoint"""
        response = client.get('/monitoring/cache')
        assert response.status_code == 200
        data = response.json
        assert "size" in data
        assert "max_size" in data
    
    def test_cache_clear_endpoint(self, client):
        """Test cache clear endpoint"""
        response = client.post('/monitoring/cache/clear')
        assert response.status_code == 200
        data = response.json
        assert data["status"] == "success"
    
    def test_monitoring_health_endpoint(self, client):
        """Test monitoring health endpoint"""
        response = client.get('/monitoring/health')
        assert response.status_code == 200
        data = response.json
        assert "status" in data
        assert "components" in data
        assert "summary" in data
    
    def test_all_metrics_endpoint(self, client):
        """Test all metrics endpoint"""
        response = client.get('/monitoring/metrics')
        assert response.status_code == 200
        data = response.json
        assert "performance" in data
        assert "concurrency" in data
        assert "cache" in data
        assert "errors" in data
        assert "top_agents" in data


class TestPerformanceIntegration:
    """Test performance monitoring integration with orchestrator"""
    
    @patch('src.services.agent_management_service.agent_management_service.discover_active_agents')
    @patch('src.orchestrator.fanout.fanout_orchestrator.fanout_to_agents')
    async def test_orchestrator_performance_tracking(
        self, 
        mock_fanout, 
        mock_discover_agents
    ):
        """Test that orchestrator tracks performance metrics"""
        from src.services.orchestrator_service import orchestrator_service
        from src.core.schemas.agent import AgentSelectRequest
        
        # Mock agent discovery
        mock_discover_agents.return_value = [
            (Mock(), "tenant_1", "Test Tenant 1")
        ]
        
        # Mock fanout results
        mock_fanout.return_value = (
            [
                {
                    "product_id": "prod_1",
                    "name": "Test Product",
                    "publisher_tenant_id": "tenant_1",
                    "source_agent_id": "agent_1",
                    "score": 0.9,
                    "price_cpm": 10.0
                }
            ],
            [Mock(status=Mock(value="active"), products_count=1, agent_id="agent_1", response_time_ms=150.0)]
        )
        
        # Create request
        request = AgentSelectRequest(
            prompt="Find technology products",
            max_results=10,
            filters={},
            locale="en-US",
            currency="USD",
            timeout_seconds=10
        )
        
        # Call orchestrator
        response = await orchestrator_service.orchestrate(request)
        
        # Verify performance metrics are included
        assert "performance" in response["metadata"]
        performance = response["metadata"]["performance"]
        assert "avg_response_time_ms" in performance
        assert "median_response_time_ms" in performance
        assert "success_rate" in performance
        
        # Verify cache is working
        cached_response = await orchestrator_service.orchestrate(request)
        assert cached_response == response  # Should be cached
    
    def test_performance_monitor_persistence(self):
        """Test that performance monitor persists data across operations"""
        monitor = PerformanceMonitor(max_history=10)
        
        # Add multiple operations
        for i in range(5):
            metrics = monitor.start_operation()
            metrics.total_agents_contacted = 1
            metrics.successful_agents = 1
            metrics.agent_response_times = {f"agent_{i}": 100.0 + i * 10}
            monitor.end_operation(metrics)
        
        # Verify data persistence
        summary = monitor.get_performance_summary()
        assert summary["total_requests"] == 5
        assert summary["total_agents_tracked"] == 5
        
        # Verify history limit
        for i in range(10):  # Add more operations to test history limit
            metrics = monitor.start_operation()
            metrics.total_agents_contacted = 1
            metrics.successful_agents = 1
            monitor.end_operation(metrics)
        
        summary = monitor.get_performance_summary()
        assert summary["recent_operations"] <= 10  # Should respect max_history
