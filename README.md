# Serena

A local voice/assistant project with a nested Stable Diffusion WebUI checkout.

## Structure

- `main.py` — entry point
- `ai.py`, `background.py`, `control.py`, `router.py` — assistant logic
- `voice.py`, `vision.py`, `tray.py` — runtime integrations
- `stable-diffusion-webui/` — tracked as a Git submodule

## Setup

1. Clone this repository.
2. Initialize submodules:
   `git submodule update --init --recursive`
3. Install dependencies as needed for your local environment.

## Notes

This repo is configured so the Stable Diffusion WebUI is kept as a separate upstream project while still being part of this repository.
