"""Entry point for python -m lofi_gen.api"""
import uvicorn
from lofi_gen.api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
