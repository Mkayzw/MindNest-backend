import uvicorn
import os
import sys

if __name__ == "__main__":
    # Add the project root to the Python path
    # This ensures that the 'app' module can be found
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Assuming your FastAPI app instance is named 'app' in 'app/main.py'
    # and you want to run it with reload enabled for development.
    # You might need to adjust "app.main:app" if your app instance or module path is different.
    uvicorn.run("app.main:app", host="127.0.0.0", port=8000, reload=True)