FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY analyzer.py gdocs.py main.py ./

ENV ALLOWED_ORIGINS=https://wordbboba.netlify.app,http://localhost:5173

EXPOSE 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
