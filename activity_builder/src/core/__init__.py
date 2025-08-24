"""
Athlete Insight Analytics Platform - Core Module

This module contains the core functionality for activity analysis and story generation.
"""

from .interactive_analyzer import InteractiveActivityAnalyzer
from .story_generator import StravaStoryGenerator

__all__ = ['InteractiveActivityAnalyzer', 'StravaStoryGenerator']
