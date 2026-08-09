import os
import yaml

workers = 1
worker_class = "uvicorn.workers.UvicornWorker"

port = os.getenv("AICA_AGENT_PORT")
bind = f"0.0.0.0:{port}"

accesslog = "-"

with open("config.yml", "r") as f:
    logconfig_dict = yaml.safe_load(f.read())["logging"]
