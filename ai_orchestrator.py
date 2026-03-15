"""
Universal AI Orchestrator
Supports multiple AI providers: Gemini, OpenRouter, etc.
User can choose which provider to use via config or environment variable
"""

import os
from typing import Dict, Optional
from gemini_integration import GeminiClient
from openrouter_integration import OpenRouterClient


class AIOrchestrator:
    """
    Universal orchestrator that can use Gemini, OpenRouter, or both as fallback
    """
    
    def __init__(
        self, 
        provider: str = "auto",  # "gemini", "openrouter", or "auto"
        gemini_key: Optional[str] = None,
        openrouter_key: Optional[str] = None
    ):
        """
        Initialize the orchestrator with specified provider
        
        Args:
            provider: Which AI provider to use
                - "gemini": Use only Google Gemini
                - "openrouter": Use only OpenRouter
                - "auto": Try Gemini first, fallback to OpenRouter
            gemini_key: Gemini API key (optional)
            openrouter_key: OpenRouter API key (optional)
        """
        self.provider = provider.lower()
        
        # Initialize clients
        self.gemini = None
        self.openrouter = None
        
        # Setup Gemini
        if self.provider in ["gemini", "auto"]:
            gemini_key = gemini_key or os.getenv("GEMINI_API_KEY")
            if gemini_key:
                self.gemini = GeminiClient(api_key=gemini_key)
                print("✅ Gemini client initialized")
            else:
                print("⚠️  Gemini API key not found")
        
        # Setup OpenRouter
        if self.provider in ["openrouter", "auto"]:
            openrouter_key = openrouter_key or os.getenv("OPENROUTER_API_KEY")
            if openrouter_key:
                self.openrouter = OpenRouterClient(api_key=openrouter_key)
                print("✅ OpenRouter client initialized")
            else:
                print("⚠️  OpenRouter API key not found")
        
        # Determine active provider
        if self.provider == "auto":
            if self.gemini:
                self.active_provider = "gemini"
                print("🎯 Using: Gemini (primary)")
            elif self.openrouter:
                self.active_provider = "openrouter"
                print("🎯 Using: OpenRouter (fallback)")
            else:
                self.active_provider = None
                print("❌ No AI provider available!")
        else:
            self.active_provider = self.provider
            print(f"🎯 Using: {self.provider}")
    
    def run_orchestrator(self, title: str, image_url: Optional[str] = None) -> Dict:
        """
        Run orchestration using the configured provider(s)
        
        Args:
            title: User's idea/title
            image_url: Optional image URL
            
        Returns:
            Dictionary with suno_prompt, veo_prompt, seo_metadata
        """
        result = {}
        gemini_success = False
        
        # Try primary provider (Gemini)
        if self.provider == "gemini" or (self.provider == "auto" and self.gemini):
            print("🧠 Trying Gemini...")
            result = self.gemini.run_orchestrator(title, image_url)
            
            # Check if successful (has valid suno_prompt and no error)
            if result and "error" not in result and result.get("suno_prompt"):
                print("✅ Gemini succeeded")
                gemini_success = True
                return result
            else:
                print("⚠️  Gemini failed or returned incomplete data")
                gemini_success = False
        
        # Fallback to OpenRouter if auto mode AND Gemini failed
        if self.provider == "auto" and not gemini_success and self.openrouter:
            print("🌐 Falling back to OpenRouter...")
            result = self.openrouter.run_orchestrator(title, image_url)
            
            if result and "error" not in result and result.get("suno_prompt"):
                print("✅ OpenRouter succeeded")
                return result
            else:
                print("⚠️  OpenRouter also failed")
        
        # Try OpenRouter if it's the primary choice
        if self.provider == "openrouter" and self.openrouter:
            print("🌐 Using OpenRouter...")
            result = self.openrouter.run_orchestrator(title, image_url)
            
            if result and "error" not in result and result.get("suno_prompt"):
                print("✅ OpenRouter succeeded")
                return result
        
        # If all failed, return fallback with basic prompts
        print("❌ All AI providers failed - using fallback prompts")
        return {
            "error": "ALL_PROVIDERS_FAILED",
            "suno_prompt": f"calm lofi beats, {title}, relaxing atmosphere, no lyrics",
            "veo_prompt": f"subtle cozy animation, {title}, cinematic lighting, looping style",
            "seo_metadata": {
                "title": f"Lofi Beats - {title} 🎵",
                "description": f"🎧 Lofi hip hop beats - {title}\n\nPerfect for studying, working, or relaxing.\n\n#lofi #chillbeats #studymusic",
                "tags": "lofi, chill, relax, study, work, beats"
            }
        }
        
        return result
    
    def get_provider_status(self) -> Dict:
        """Get status of all providers"""
        return {
            "gemini": "available" if self.gemini else "not configured",
            "openrouter": "available" if self.openrouter else "not configured",
            "active": self.active_provider
        }


# Quick test
if __name__ == "__main__":
    print("=== AI Orchestrator Test ===\n")
    
    # Test auto mode
    orchestrator = AIOrchestrator(provider="auto")
    
    print("\n" + "="*70)
    print("Provider Status:")
    print(orchestrator.get_provider_status())
    
    # Test orchestration
    print("\n" + "="*70)
    print("Testing orchestration...\n")
    
    result = orchestrator.run_orchestrator("Calm evening vibes")
    
    if result:
        print("\n✅ Result:")
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\n❌ No result")
