# app.py - a minimal flask api using flask_restful
from flask import Flask, escape, request
from provider import DataProvider
from transformer import DataTransformer
import json
from config import app
from unittest import TestLoader, runner
from argparse import ArgumentParser

parser = ArgumentParser(prog='App',
                        description='App de Flask')

parser.add_argument(
    'mode', type=str, help='Modo de ejecucion (runserver|tests)'
)

args = parser.parse_args()


@app.route('/')
def home():
    """
        Token must come as part of the request
    """
    dp = DataProvider()
    token = dp.retrieve_token(username=app.config['USERNAME'], password=app.config['PASSWORD'])
    data = dp.retrieve_materiascursadas(token)
    dataframe = DataTransformer(data).transform_to_dataframe()
    return dataframe

@app.route('/indiceaprobacion')
def indice_aprobacion():
    return json.dumps([{'name': '01/01/2016', 'value': 75.8}, {'name': '01/01/2019', 'value': 90}])

def runserver():
    app.run(debug=True, host='0.0.0.0')

def tests():
    loader = TestLoader()
    tests = loader.discover('tests/')
    testRunner = runner.TextTestRunner()
    testRunner.run(tests)


modes = {
    'runserver': runserver,
    'tests': tests
}[args.mode]()
