"""
Custom hooks for LiteLLM Proxy

This module contains custom callback hooks for specialized routing and processing logic.
"""

from .nova_task_routing import NovaTaskRoutingHook, nova_task_router

__all__ = ["NovaTaskRoutingHook", "nova_task_router"]
