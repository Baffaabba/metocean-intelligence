import os
import sys

from streamlit.web import cli

if __name__ == "__main__":
    sys.argv = [
        "streamlit",
        "run",
        f"{os.path.dirname(os.path.realpath(__file__))}/st_app.py",
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--server.baseUrlPath=transfer-learning",
        "--logger.level=debug",
    ]
    sys.exit(cli.main())
