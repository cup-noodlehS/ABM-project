FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt solara altair

COPY parched_model.py .
COPY scenarios.py .
COPY app.py .

EXPOSE 7860

ENV UVICORN_PROXY_HEADERS=1
ENV FORWARDED_ALLOW_IPS="*"

CMD ["solara", "run", "app.py", "--host", "0.0.0.0", "--port", "7860"]
