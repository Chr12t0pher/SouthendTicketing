FROM python:3-stretch

RUN mkdir /opt/app
ADD . /opt/app
WORKDIR /opt/app


RUN pip install -r requirements.txt
RUN pip install gunicorn

EXPOSE 8080

CMD ["/usr/bin/gunicorn", "--bind", "0.0.0.0:8080", "wsgi:app"]