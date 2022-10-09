FROM python:3

RUN mkdir -p /home/app

WORKDIR /home/app

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /home/app/requirements.txt

RUN pip install -r requirements.txt

COPY . /home/app
CMD [ "python", "./main.py" ]