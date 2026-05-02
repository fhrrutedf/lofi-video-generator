"""Tests for prompt system."""

import pytest
from lofi_gen.ai.prompt_system import PromptSystem, THEME_TEMPLATES, KEYWORD_MAP


def test_theme_templates_exist():
    """Test that theme templates are defined."""
    assert "default" in THEME_TEMPLATES
    assert "rain" in THEME_TEMPLATES
    assert "cafe" in THEME_TEMPLATES
    assert "study" in THEME_TEMPLATES


def test_keyword_mapping():
    """Test keyword to theme mapping."""
    ps = PromptSystem()
    
    # English keywords
    assert ps.detect_theme("rain") == "rain"
    assert ps.detect_theme("study session") == "study"
    assert ps.detect_theme("coffee shop") == "cafe"
    
    # Arabic keywords
    assert ps.detect_theme("مطر") == "rain"
    assert ps.detect_theme("دراسة") == "study"
    assert ps.detect_theme("قهوة") == "cafe"


def test_generate_theme_info():
    """Test theme info generation."""
    ps = PromptSystem()
    
    theme_info = ps.generate("rainy day lofi")
    
    assert theme_info.name == "rain"
    assert 60 <= theme_info.bpm <= 75
    assert theme_info.mood == "sad"
    assert "rain" in theme_info.music_prompt.lower()
    assert len(theme_info.video_prompt) > 0


def test_seo_metadata():
    """Test SEO metadata generation."""
    ps = PromptSystem()
    
    theme_info = ps.generate("cafe")
    seo = ps.generate_seo_metadata(theme_info, "cafe", 4.0)
    
    assert "title" in seo
    assert "description" in seo
    assert "tags" in seo
    assert "lofi" in seo["tags"].lower()


def test_default_theme_fallback():
    """Test fallback to default theme."""
    ps = PromptSystem()
    
    theme_info = ps.generate("something completely unknown")
    assert theme_info.name == "default"
