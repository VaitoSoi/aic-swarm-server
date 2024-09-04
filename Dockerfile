FROM python:latest
EXPOSE 8000

VOLUME /app
ADD ./requirements.txt /app/requirements.txt
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install uvicorn websockets

CMD ["uvicorn", "main:app", "--host=0.0.0.0", "--port=8000"]
