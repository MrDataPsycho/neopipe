"""
Pipeline module providing unified access to sync and async pipelines.

This module imports and re-exports pipeline classes from their respective modules
to maintain backward compatibility while keeping sync and async implementations separate.
"""

from neopipe.sync_pipeline import SyncPipeline
from neopipe.async_pipeline import AsyncPipeline

__all__ = ["SyncPipeline", "AsyncPipeline"]
