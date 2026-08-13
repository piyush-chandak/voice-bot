# Voice Technician Assistant Backend

# 1. Start LiveKit + Redis (Docker)
make infra

# 2. Then in separate terminals:
make backend    # FastAPI on :8000
make agent      # LiveKit voice agent worker
make frontend   # React on :5173

# Or all at once (needs `npm i -g concurrently`):
make run
