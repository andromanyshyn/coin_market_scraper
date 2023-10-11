import uvicorn
from src.app import app

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
    except Exception as e:
        print(e)
