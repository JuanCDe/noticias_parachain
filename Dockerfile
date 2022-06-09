FROM docker.io/library/python:3.6

RUN apt-get update

# RUN /usr/local/bin/python -m pip install --upgrade pip

WORKDIR /~

COPY requirements.txt .
COPY noticias_parachains.py .
COPY config.yml .

RUN pip install -r requirements.txt && rm requirements.txt

ENTRYPOINT ["python", "noticias_parachains.py"]
