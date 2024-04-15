FROM python:3.11-slim

RUN apt-get update

# create working directory
RUN mkdir collector
WORKDIR collector

# install requirements
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN rm -f requirements.txt

# add source code
COPY src/ .

# run application
CMD ["python", "main.py"]
