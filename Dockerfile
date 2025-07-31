FROM python:3.11.6-slim

WORKDIR /app
COPY . /app

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN pip install -r requirements.txt

CMD ["poetry", "run", "python", "main.py"]