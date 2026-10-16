import os
from app import create_app

env = os.environ.get("FLASK_ENV", "production")
app = create_app(config_name=env)

if __name__ == "__main__":
    app.run()
