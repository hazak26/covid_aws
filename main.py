import os
import sys
import boto3
from ast import literal_eval
import mysql.connector

import flask
import requests
from flask import Flask
from flask import request
from werkzeug.exceptions import HTTPException
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

ENDPOINT = "test-covid.c7qedtmdkr6o.eu-west-1.rds.amazonaws.com"
PORT = "3306"
USER = "juljul"
REGION = "eu-west-1"
DBNAME = "covid"
BUCKET_NAME = "backendprojectjuljul"
os.environ['LIBMYSQL_ENABLE_CLEARTEXT_PLUGIN'] = '1'


def connect_db():

    # gets the credentials from .aws/credentials
    session = boto3.Session(profile_name='default', region_name=REGION)
    client = session.client('rds')

    token = client.generate_db_auth_token(DBHostname=ENDPOINT, Port=PORT, DBUsername=USER, Region=REGION)
    try:
        conn = mysql.connector.connect(host=ENDPOINT, user=USER, passwd=token, port=PORT, database=DBNAME,
                                   ssl_ca='rds-ca-2019-root.pem')
        return conn
    except:
        print("Database connection failed due to {}".format(e))
        sys.exit(1)


def init_db():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DROP TABLE  IF EXISTS summary_covid")
    sql = """CREATE TABLE IF NOT EXISTS summary_covid (
        summary_id INT AUTO_INCREMENT,
        country VARCHAR(255) NOT NULL,
        new_confirmed INT NOT NULL,
        total_confirmed INT NOT NULL,
        new_death INT NOT NULL,
        total_death INT NOT NULL,

        PRIMARY KEY (summary_id)
    );"""
    cur.execute(sql)
    countries = get_data()
    for country in countries:

        sql = "INSERT into summary_covid (country, new_confirmed, total_confirmed, new_death, total_death) VALUES (" \
              "%s, %s, %s, %s, %s) "
        val = (country.get('Country'),country.get('NewConfirmed'),country.get('TotalConfirmed'), country.get('NewDeaths'), country.get('TotalDeaths'))
        cur.execute(sql, val)
        conn.commit()


def get_data():
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('backendprojectjuljul')

    for obj in bucket.objects.all():
        return literal_eval(obj.get()['Body'].read().decode('utf8'))['Countries']


app = Flask(__name__)


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "status": "failed",
    })
    response.content_type = "application/json"
    return response


@app.route("/summary")
def summary_cases():
    """summary of new and total cases per country updated daily"""
    response = {}
    init_db()
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM summary_covid")
    myresult = cur.fetchall()
    for result in myresult:
        response[result[1]] = {'new_cases': result[2], 'total_cases': result[3], 'new_deaths': result[4], 'total_deaths': result[5]}
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

