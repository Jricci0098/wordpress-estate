FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY worker.py .

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os,sys,time; p='/tmp/worker-healthy'; sys.exit(0 if os.path.exists(p) and time.time() - os.path.getmtime(p) < 30 else 1)"

CMD ["python", "worker.py"]
