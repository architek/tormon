FROM python:3.9-alpine
LABEL Maintainer="architek"

RUN adduser -D user
USER user

WORKDIR /usr/app/src
COPY src/* .

RUN pip install -r requirements.txt
ENV PYTHONUNBUFFERED=1
CMD [ "python", "./tormon.py"]
