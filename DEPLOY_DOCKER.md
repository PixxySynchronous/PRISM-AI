# Deploy with Docker (local / VM)

This project contains the full activity classification and attendance pipelines. Building and running the full stack is easiest with Docker.

Build (local):
```bash
# build image
docker build -t classroom-activity:latest .

# run container (maps host ./activity_web/runtime to container persistent folder)
docker run --rm -p 5000:8080 \
  -v "$(pwd)/activity_web/runtime:/data/activity_runtime" \
  -v "$(pwd)/models:/app/models" \
  -e ACTIVITY_WEB_RUNTIME_DIR=/data/activity_runtime \
  classroom-activity:latest
```

With `docker-compose` (recommended for development):
```bash
docker compose up --build
```

Notes:
- The image installs heavy ML libraries (Torch, InsightFace, Ultralytics) which may take several minutes to build.
- For GPU support, use an appropriate base image (NVIDIA CUDA) and run with `--gpus` on a host with drivers.
- Store large model files in `./models` (mounted into the container) or a remote object store and point the app to them.
