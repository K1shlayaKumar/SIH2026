"""
Project setup script.

Running `python setup.py` installs the dependencies listed in
requirements.txt and then launches the Streamlit app (streamlit_app.py),
which opens the traffic-signal simulation in your browser.
"""
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
REQUIREMENTS_FILE = ROOT_DIR / "requirements.txt"
STREAMLIT_APP = ROOT_DIR / "streamlit_app.py"


def install_requirements():
    print(f"Installing dependencies from {REQUIREMENTS_FILE.name} ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])


def launch_streamlit_app():
    print(f"Launching {STREAMLIT_APP.name} ...")
    subprocess.check_call([sys.executable, "-m", "streamlit", "run", str(STREAMLIT_APP)])


def main():
    install_requirements()
    launch_streamlit_app()


if __name__ == "__main__":
    main()
