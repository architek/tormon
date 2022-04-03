FROM python:3.9-alpine

#Labels as key value pair
LABEL Maintainer="architek"

WORKDIR /usr/app/src
COPY src/* /usr/app/src/

RUN adduser -D user
USER user
RUN pip install -r requirements.txt
ENV PYTHONUNBUFFERED=1
CMD [ "python", "./tormon.py"]