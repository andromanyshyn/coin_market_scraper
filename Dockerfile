FROM python:3.10

WORKDIR /crypto_service

COPY requirements.txt .

RUN pip install -r requirements.txt

EXPOSE 5000

COPY . .

CMD ["python", "main.py"]