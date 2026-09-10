import os

import dotenv

dotenv.load_dotenv()

env = os.environ.get("DJANGO_ENV", "development")
if env == "production":
    from .production import *
else:
    from .development import *
