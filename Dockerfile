FROM python

WORKDIR /fingertas

COPY . ./

RUN pip install -r requirements.txt

EXPOSE 8080

ENTRYPOINT python test.py
