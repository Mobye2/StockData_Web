FROM python:3.11-slim

WORKDIR /app

COPY requirements_mcp.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "mcp_server.py"]