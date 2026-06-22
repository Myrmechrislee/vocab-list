FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Don't move .vscode .venc __pycache__ .git files to the container
COPY . .

ENV MONGO_DB=vocab-list-staging
ENV MONGO_URI=mongodb://host.docker.internal:27017/


EXPOSE 1234

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=1234"]
