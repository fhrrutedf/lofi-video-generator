"""
API Keys Validation Script
Checks if all required API keys are properly configured
"""

import os
import sys
from pathlib import Path

# ANSI color codes for terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text, color):
    """Print colored text to terminal"""
    print(f"{color}{text}{Colors.RESET}")

def check_env_file():
    """Check if .env file exists"""
    env_path = Path(".env")
    if not env_path.exists():
        print_colored("\n⚠️  Warning: .env file not found!", Colors.YELLOW)
        print_colored("📝 Creating .env from template...", Colors.BLUE)
        
        # Copy .env.example to .env
        example_path = Path(".env.example")
        if example_path.exists():
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print_colored("✅ Created .env file. Please fill in your API keys!\n", Colors.GREEN)
            return False
        else:
            print_colored("❌ .env.example not found either!\n", Colors.RED)
            return False
    return True

def load_env():
    """Load environment variables from .env file"""
    env_path = Path(".env")
    if not env_path.exists():
        return
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if value and not value.startswith('your_'):
                    os.environ[key.strip()] = value.strip()

# Required API keys with instructions
API_KEYS = {
    "KIE_API_KEY": {
        "name": "Kie.ai API",
        "url": "https://kie.ai/dashboard/api-keys",
        "description": "Music & Video generation via Suno & Veo",
        "required": True
    },
    "GEMINI_API_KEY": {
        "name": "Google Gemini AI",
        "url": "https://aistudio.google.com/app/apikey",
        "description": "Intelligent prompt orchestration",
        "required": False  # Can use OpenRouter instead
    },
    "OPENROUTER_API_KEY": {
        "name": "OpenRouter AI",
        "url": "https://openrouter.ai/keys",
        "description": "Free alternative (e.g. Llama 3, Gemini Free)",
        "required": False  # Can use Gemini instead
    },
    "PEXELS_API_KEY": {
        "name": "Pexels API",
        "url": "https://www.pexels.com/api/new/",
        "description": "Stock videos and images",
        "required": False  # Can use local videos
    }
}

def validate_api_keys():
    """Validate all required API keys"""
    print_colored(f"\n{Colors.BOLD}🔍 Checking API Keys Configuration{Colors.RESET}\n", Colors.BLUE)
    print("=" * 70)
    
    # Load .env file first
    load_env()
    
    all_valid = True
    missing_required = []
    
    for key, info in API_KEYS.items():
        value = os.getenv(key)
        status_icon = "✅" if value else "❌"
        
        # Check if it's still the placeholder
        if value and value.startswith('your_'):
            value = None
            status_icon = "⚠️ "
        
        if value:
            # Mask the key (show only first 8 chars)
            masked = value[:8] + "..." + ("*" * 20) if len(value) > 8 else value
            print_colored(f"{status_icon} {info['name']}: {masked}", Colors.GREEN)
            print(f"   Purpose: {info['description']}")
        else:
            color = Colors.RED if info['required'] else Colors.YELLOW
            print_colored(f"{status_icon} {info['name']}: NOT SET", color)
            print(f"   Purpose: {info['description']}")
            print(f"   Get it from: {info['url']}")
            
            if info['required']:
                missing_required.append(key)
                all_valid = False
        
        print("-" * 70)
    
    # Summary
    print()
    if all_valid:
        print_colored("🎉 All required API keys are configured!", Colors.GREEN)
        print_colored("✨ Your automation pipeline is ready to run!\n", Colors.GREEN)
        return True
    else:
        print_colored("⚠️  Some required API keys are missing:", Colors.RED)
        for key in missing_required:
            print_colored(f"   - {key}: {API_KEYS[key]['url']}", Colors.YELLOW)
        
        print_colored("\n📝 How to fix:", Colors.BLUE)
        print("   1. Open .env file in a text editor")
        print("   2. Replace 'your_xxx_here' with your actual API keys")
        print("   3. Save the file and run this script again")
        print()
        return False

def test_api_connections():
    """Test actual API connections (optional)"""
    print_colored(f"\n{Colors.BOLD}🧪 Testing API Connections{Colors.RESET}\n", Colors.BLUE)
    print("=" * 70)
    
    # Test Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print("Testing Gemini API...", end=" ")
        try:
            from gemini_integration import GeminiClient
            client = GeminiClient(api_key=gemini_key)
            # Simple test call
            result = client._call_gemini("Hello")
            if result and result != "ERR_QUOTA_EXHAUSTED":
                print_colored("✅ Connected!", Colors.GREEN)
            elif result == "ERR_QUOTA_EXHAUSTED":
                print_colored("⚠️  Quota exhausted (but key is valid)", Colors.YELLOW)
            else:
                print_colored("❌ Failed", Colors.RED)
        except Exception as e:
            print_colored(f"❌ Error: {str(e)[:50]}", Colors.RED)
    else:
        print_colored("⏭️  Skipping Gemini (not configured)", Colors.YELLOW)
    
    # Test Kie.ai
    kie_key = os.getenv("KIE_API_KEY")
    if kie_key:
        print("Testing Kie.ai API...", end=" ")
        try:
            from kie_ai_integration import KieAIClient
            client = KieAIClient(api_key=kie_key)
            # We can't test without actually generating, so just check initialization
            print_colored("✅ Initialized (full test requires credits)", Colors.GREEN)
        except ValueError as e:
            print_colored(f"❌ Invalid key: {e}", Colors.RED)
        except Exception as e:
            print_colored(f"❌ Error: {str(e)[:50]}", Colors.RED)
    else:
        print_colored("⏭️  Skipping Kie.ai (not configured)", Colors.YELLOW)
    
    # Test Pexels
    pexels_key = os.getenv("PEXELS_API_KEY")
    if pexels_key:
        print("Testing Pexels API...", end=" ")
        try:
            from pexels_integration import PexelsVideoFetcher
            fetcher = PexelsVideoFetcher(api_key=pexels_key)
            # Try a simple search
            results = fetcher.search_videos("nature", per_page=1)
            if results:
                print_colored("✅ Connected!", Colors.GREEN)
            else:
                print_colored("⚠️  No results (might be rate limited)", Colors.YELLOW)
        except ValueError as e:
            print_colored(f"❌ Invalid key: {e}", Colors.RED)
        except Exception as e:
            print_colored(f"❌ Error: {str(e)[:50]}", Colors.RED)
    else:
        print_colored("⏭️  Skipping Pexels (not configured)", Colors.YELLOW)
    
    print()

if __name__ == "__main__":
    print_colored("""
╔══════════════════════════════════════════════════════════════════╗
║                  Lofi Video Generator                            ║
║              API Configuration Validator                         ║
╚══════════════════════════════════════════════════════════════════╝
    """, Colors.BLUE)
    
    # Check if .env exists
    if not check_env_file():
        sys.exit(1)
    
    # Validate keys
    keys_valid = validate_api_keys()
    
    # Optionally test connections
    if keys_valid and "--test" in sys.argv:
        test_api_connections()
    elif keys_valid:
        print_colored("💡 Tip: Run 'python validate_env.py --test' to test actual connections\n", Colors.BLUE)
    
    # Exit with appropriate code
    sys.exit(0 if keys_valid else 1)
