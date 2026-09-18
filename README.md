# Voice Technician Assistant Backend

# 1. Start LiveKit + Redis (Docker)
make infra

# 2. Then in separate terminals:
make backend    # FastAPI on :8000
make agent      # LiveKit voice agent worker
make frontend   # React on :5173

# Or all at once (needs `npm i -g concurrently`):
make run

## LiveKit Files
[text](livekit/livekit.yaml)
port: 7880

rtc:
  tcp_port: 7881
  port_range_start: 50000
  port_range_end: 60000

keys:
  devkey: secret

[text](livekit/docker-compose.yml)
services:
  livekit:
    image: livekit/livekit-server:latest
    command: --config /etc/livekit.yaml
    ports:
      - "7880:7880"
      - "7881:7881"
      - "50000-50100:50000-50100/udp"
    volumes:
      - ./livekit.yaml:/etc/livekit.yaml:ro
    restart: unless-stopped