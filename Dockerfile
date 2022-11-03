FROM python

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /fingertas

COPY . ./

RUN pip install -r requirements.txt

ENTRYPOINT python app.py
