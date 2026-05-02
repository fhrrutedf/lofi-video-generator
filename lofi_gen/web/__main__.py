"""Entry point for python -m lofi_gen.web"""
import subprocess
import sys

def main():
    """Launch Streamlit web interface."""
    web_file = "lofi_gen/web/__init__.py"
    cmd = [sys.executable, "-m", "streamlit", "run", web_file, "--server.headless", "true"]
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
