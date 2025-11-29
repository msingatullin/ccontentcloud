"""
Background workers для выполнения фоновых задач
"""

from .scheduled_posts_worker import ScheduledPostsWorker
from .auto_posting_worker import AutoPostingWorker

__all__ = ['ScheduledPostsWorker', 'AutoPostingWorker']

