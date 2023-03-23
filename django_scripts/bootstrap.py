import os
import sys
from datetime import datetime

import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "your_project_name.settings"
)


if __name__ == '__main__':
    django.setup()
    # your imports, e.g. Django models

    # Start timing
    start = datetime.now()


    # Put your script here..


    # Print report
    finish = datetime.now()
    print(f"\n\nScript finished after {(finish - start).total_seconds()} seconds of execution.\n\n")
