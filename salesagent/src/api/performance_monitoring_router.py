"""
Performance Monitoring API Router - Expose performance metrics and monitoring endpoints
"""
import logging
from typing import Dict, Any

from flask import Blueprint, jsonify, request
from src.orchestrator.performance import performance_monitor, concurrency_optimizer, cache_manager

logger = logging.getLogger(__name__)

# Create Blueprint
performance_monitoring_bp = Blueprint("performance_monitoring", __name__, url_prefix="/monitoring")


@performance_monitoring_bp.route("/performance", methods=["GET"])
def get_performance_summary():
    """
    Get comprehensive performance summary
    """
    try:
        summary = performance_monitor.get_performance_summary()
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}", exc_info=True)
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500


@performance_monitoring_bp.route("/performance/agents", methods=["GET"])
def get_agent_performance():
    """
    Get performance metrics for all agents
    """
    try:
        agent_id = request.args.get('agent_id')
        
        if agent_id:
            # Get specific agent performance
            performance = performance_monitor.get_agent_performance(agent_id)
            return jsonify(performance)
        else:
            # Get top performing agents
            limit = request.args.get('limit', 10, type=int)
            top_agents = performance_monitor.get_top_performing_agents(limit)
            return jsonify({
                "top_performing_agents": top_agents,
                "total_agents": len(top_agents)
            })
        
    except Exception as e:
        logger.error(f"Error getting agent performance: {e}", exc_info=True)
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500


@performance_monitoring_bp.route("/performance/errors", methods=["GET"])
def get_error_summary():
    """
    Get error summary and trends
    """
    try:
        error_summary = performance_monitor.get_error_summary()
        return jsonify(error_summary)
        
    except Exception as e:
        logger.error(f"Error getting error summary: {e}", exc_info=True)
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500


@performance_monitoring_bp.route("/concurrency", methods=["GET"])
def get_concurrency_stats():
    """
    Get concurrency optimization statistics
    """
    try:
        stats = concurrency_optimizer.get_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting concurrency stats: {e}", exc_info=True)
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500


@performance_monitoring_bp.route("/cache", methods=["GET"])
def get_cache_stats():
    """
    Get cache statistics
    """
    try:
        stats = cache_manager.get_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}", exc_info=True)
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500


@performance_monitoring_bp.route("/cache/clear", methods=["POST"])
def clear_cache():
    """
    Clear the cache
    """
    try:
        cache_manager.clear()
        return jsonify({
            "status": "success",
            "message": "Cache cleared successfully"
        })
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500


@performance_monitoring_bp.route("/health", methods=["GET"])
def monitoring_health():
    """
    Health check for monitoring system
    """
    try:
        # Get basic stats
        performance_summary = performance_monitor.get_performance_summary()
        concurrency_stats = concurrency_optimizer.get_stats()
        cache_stats = cache_manager.get_stats()
        
        # Determine overall health
        overall_health = "healthy"
        issues = []
        
        # Check performance
        if performance_summary.get("status") == "no_data":
            overall_health = "warning"
            issues.append("No performance data available")
        
        # Check error rate
        total_errors = performance_summary.get("total_errors", 0)
        total_requests = performance_summary.get("total_requests", 0)
        if total_requests > 0:
            error_rate = (total_errors / total_requests) * 100
            if error_rate > 10:  # More than 10% error rate
                overall_health = "unhealthy"
                issues.append(f"High error rate: {error_rate:.1f}%")
        
        # Check concurrency
        concurrency_success_rate = concurrency_stats.get("success_rate", 100)
        if concurrency_success_rate < 90:  # Less than 90% success rate
            overall_health = "warning"
            issues.append(f"Low concurrency success rate: {concurrency_success_rate:.1f}%")
        
        return jsonify({
            "status": overall_health,
            "issues": issues,
            "components": {
                "performance_monitor": "healthy",
                "concurrency_optimizer": "healthy",
                "cache_manager": "healthy"
            },
            "summary": {
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate": (total_errors / max(total_requests, 1)) * 100,
                "concurrency_success_rate": concurrency_success_rate,
                "cache_size": cache_stats.get("size", 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Error in monitoring health check: {e}", exc_info=True)
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "components": {
                "performance_monitor": "error",
                "concurrency_optimizer": "error",
                "cache_manager": "error"
            }
        }), 500


@performance_monitoring_bp.route("/metrics", methods=["GET"])
def get_all_metrics():
    """
    Get all monitoring metrics in one response
    """
    try:
        # Collect all metrics
        performance_summary = performance_monitor.get_performance_summary()
        concurrency_stats = concurrency_optimizer.get_stats()
        cache_stats = cache_manager.get_stats()
        error_summary = performance_monitor.get_error_summary()
        top_agents = performance_monitor.get_top_performing_agents(10)
        
        return jsonify({
            "performance": performance_summary,
            "concurrency": concurrency_stats,
            "cache": cache_stats,
            "errors": error_summary,
            "top_agents": top_agents,
            "timestamp": performance_summary.get("timestamp")
        })
        
    except Exception as e:
        logger.error(f"Error getting all metrics: {e}", exc_info=True)
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500
