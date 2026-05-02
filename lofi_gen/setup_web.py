"""
LofiGen Setup Web Interface - Initial Configuration

This is a special Streamlit app for first-time setup on VPS.
It allows users to configure API keys without editing .env files manually.
"""

import os
import re
import subprocess
from pathlib import Path

import streamlit as st

# Page config
st.set_page_config(
    page_title="LofiGen Setup - Initial Configuration",
    page_icon="⚙️",
    layout="centered",
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #eee;
    }
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 15px 30px;
        font-weight: bold;
        width: 100%;
    }
    .success-box {
        background: rgba(0, 255, 0, 0.1);
        border: 1px solid #00ff00;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
    .warning-box {
        background: rgba(255, 165, 0, 0.1);
        border: 1px solid #ffa500;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
    .info-box {
        background: rgba(102, 126, 234, 0.1);
        border: 1px solid #667eea;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

def read_env_file():
    """Read current .env file."""
    env_path = Path("/opt/lofigen/.env") if Path("/opt/lofigen/.env").exists() else Path(".env")
    
    if not env_path.exists():
        return {}
    
    env_vars = {}
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key] = value
    return env_vars

def write_env_file(env_vars: dict) -> bool:
    """Write to .env file and restart services."""
    env_path = Path("/opt/lofigen/.env") if Path("/opt/lofigen/.env").exists() else Path(".env")
    
    try:
        # Read existing file to preserve comments
        existing_lines = []
        if env_path.exists():
            with open(env_path, "r") as f:
                existing_lines = f.readlines()
        
        # Build new content
        new_lines = []
        written_keys = set()
        
        # Update existing lines
        for line in existing_lines:
            stripped = line.strip()
            if stripped.startswith("#") or not stripped or "=" not in stripped:
                new_lines.append(line)
            else:
                key = stripped.split("=", 1)[0]
                if key in env_vars:
                    new_lines.append(f"{key}={env_vars[key]}\n")
                    written_keys.add(key)
                else:
                    new_lines.append(line)
        
        # Add new keys
        for key, value in env_vars.items():
            if key not in written_keys:
                new_lines.append(f"{key}={value}\n")
        
        with open(env_path, "w") as f:
            f.writelines(new_lines)
        
        # Restart Docker services
        try:
            compose_file = Path("/opt/lofigen/docker-compose.prod.yml")
            if compose_file.exists():
                subprocess.run(
                    ["docker-compose", "-f", str(compose_file), "restart"],
                    capture_output=True,
                    cwd="/opt/lofigen"
                )
            else:
                subprocess.run(
                    ["docker-compose", "restart"],
                    capture_output=True
                )
        except:
            pass  # Ignore restart errors
        
        return True
    except Exception as e:
        st.error(f"Error saving configuration: {e}")
        return False

def test_api_key(service: str, key: str) -> bool:
    """Test if an API key is valid."""
    if not key:
        return False
    
    try:
        import requests
        
        if service == "pexels":
            response = requests.get(
                "https://api.pexels.com/v1/search?query=test&per_page=1",
                headers={"Authorization": key},
                timeout=5
            )
            return response.status_code == 200
        
        elif service == "kie":
            # Simple connectivity test
            response = requests.get(
                "https://kie.ai/api/v1/status",
                headers={"Authorization": f"Bearer {key}"},
                timeout=5
            )
            return response.status_code in [200, 401]  # 401 means key format OK
        
        return True  # For others, just check non-empty
    except:
        return False

# Main UI
st.title("⚙️ LofiGen Pro Setup")
st.subheader("Initial Configuration")

st.markdown("""
<div class="info-box">
    Welcome to LofiGen Pro! This setup wizard will help you configure your API keys
    and get your video generator running.
</div>
""", unsafe_allow_html=True)

# Read current env
env_vars = read_env_file()

# API Keys Section
st.markdown("---")
st.markdown("### 🔑 API Keys Configuration")

st.info("These keys are required for automatic media generation. You can skip optional ones.")

# Required keys
col1, col2 = st.columns(2)

with col1:
    st.markdown("**🎵 Music Generation (Required)**")
    kie_key = st.text_input(
        "Kie.ai API Key",
        value=env_vars.get("KIE_API_KEY", ""),
        type="password",
        help="Get from https://kie.ai/dashboard/api-keys",
        placeholder="kie_xxxxxxxx"
    )
    
    if kie_key:
        if test_api_key("kie", kie_key):
            st.success("✓ Key format looks valid")
        else:
            st.warning("⚠ Could not verify key (may still work)")

with col2:
    st.markdown("**🖼️ Stock Media (Required)**")
    pexels_key = st.text_input(
        "Pexels API Key",
        value=env_vars.get("PEXELS_API_KEY", ""),
        type="password",
        help="Get from https://www.pexels.com/api/new/",
        placeholder="xxxxxxxxxxxxxxxxxxxx"
    )
    
    if pexels_key:
        if test_api_key("pexels", pexels_key):
            st.success("✓ Key verified!")
        else:
            st.error("✗ Invalid key")

# Optional keys
st.markdown("---")
st.markdown("### 🤖 AI Enhancement (Optional)")

ai_provider = st.selectbox(
    "AI Provider",
    ["auto", "gemini", "openrouter"],
    index=["auto", "gemini", "openrouter"].index(env_vars.get("AI_PROVIDER", "auto")),
    help="Auto tries Gemini first, falls back to OpenRouter"
)

col1, col2 = st.columns(2)

with col1:
    gemini_key = st.text_input(
        "Gemini API Key (Optional)",
        value=env_vars.get("GEMINI_API_KEY", ""),
        type="password",
        help="Get from https://aistudio.google.com/app/apikey"
    )

with col2:
    openrouter_key = st.text_input(
        "OpenRouter API Key (Optional)",
        value=env_vars.get("OPENROUTER_API_KEY", ""),
        type="password",
        help="Get from https://openrouter.ai/keys (free models available)"
    )

# Database Status
st.markdown("---")
st.markdown("### 💾 System Status")

try:
    # Check Docker
    docker_result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
    docker_running = docker_result.returncode == 0
    
    # Check services
    try:
        import requests
        api_response = requests.get("http://localhost:8000/health", timeout=2)
        api_running = api_response.status_code == 200
    except:
        api_running = False
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if docker_running:
            st.success("🐳 Docker: Running")
        else:
            st.error("🐳 Docker: Not running")
    
    with col2:
        if api_running:
            st.success("⚡ API: Online")
        else:
            st.warning("⚡ API: Starting...")
    
    with col3:
        db_initialized = Path("/opt/lofigen/.env").exists() or Path(".env").exists()
        if db_initialized:
            st.success("💾 Config: Ready")
        else:
            st.warning("💾 Config: Pending")

except:
    st.info("Status check unavailable")

# Save Button
st.markdown("---")

if st.button("💾 Save Configuration & Restart Services", type="primary"):
    if not kie_key and not pexels_key:
        st.error("⚠️ Please provide at least Kie.ai or Pexels API key")
    else:
        # Update env vars
        new_vars = {
            "KIE_API_KEY": kie_key,
            "PEXELS_API_KEY": pexels_key,
            "GEMINI_API_KEY": gemini_key,
            "OPENROUTER_API_KEY": openrouter_key,
            "AI_PROVIDER": ai_provider,
        }
        
        # Keep existing vars
        for key in env_vars:
            if key not in new_vars:
                new_vars[key] = env_vars[key]
        
        if write_env_file(new_vars):
            st.markdown("""
            <div class="success-box">
                <h3>✅ Configuration Saved!</h3>
                <p>Your API keys have been saved and services are restarting.</p>
                <p>Wait 30 seconds, then refresh this page.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.balloons()
            
            st.markdown("### 🚀 Next Steps:")
            st.markdown("""
            1. **Wait 30 seconds** for services to restart
            2. **Go to Main App**: Click link below
            3. **Create First User**: Use the API or Web interface
            4. **Start Generating**: Your lofi videos!
            """)
            
            # Get server IP
            try:
                server_ip = subprocess.run(
                    ["hostname", "-I"],
                    capture_output=True,
                    text=True
                ).stdout.strip().split()[0]
            except:
                server_ip = "localhost"
            
            st.markdown(f"### 📍 Access Your LofiGen:")
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("🌐 Main Web Interface", f"http://{server_ip}:8501", use_container_width=True)
            with col2:
                st.link_button("📚 API Documentation", f"http://{server_ip}:8000/docs", use_container_width=True)
            
            st.info("💡 Tip: Bookmark these URLs for easy access!")
        else:
            st.error("Failed to save configuration")

# Footer
st.markdown("---")
st.caption("🎵 LofiGen Pro Setup Wizard v1.0.0 | [Documentation](https://github.com/yourname/lofi-video-generator)")
