FROM python:3.10

WORKDIR /usr/local/src/app

COPY . .

RUN pip install --no-cache-dir -r  requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]