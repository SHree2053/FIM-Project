# FIM - File Integrity Monitor

## Quick Start (Docker)

1. Load the image:
   docker load -i fim-monitor.tar

2. Create folders:
   mkdir -p ~/fim-data/test_dir ~/fim-data/data

3. Run:
   docker run -it --name fim \
     -v ~/fim-data/test_dir:/app/test_dir \
     -v ~/fim-data/data:/app/data \
     -p 5000:5000 \
     -p 5050:5050 \
     fim-monitor

## Quick Start (Python)

1. Install dependencies:
   pip install -r requirements.txt

2. Run:
   python fim_menu.py

## Access
- API: http://localhost:5000
- Dashboard: http://localhost:5050

## To Stop
Press Ctrl+C, choose 9 from menu, or:
docker rm -f fim
