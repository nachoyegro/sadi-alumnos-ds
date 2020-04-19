# app.py - a minimal flask api using flask_restful
from flask import Flask, escape, request
from provider import DataProvider
from transformer import DataTransformer
from manipulator import DataManipulator
import json
from config import app
from unittest import TestLoader, runner
from argparse import ArgumentParser
from jwt_decorator import tiene_jwt, get_token
import pandas as pd
from datetime import date

parser = ArgumentParser(prog='App',
                        description='App de Flask')

parser.add_argument(
    'mode', type=str, help='Modo de ejecucion (runserver|tests)'
)

args = parser.parse_args()


def get_materiascursadas(request):

    provider = DataProvider()
    transformer = DataTransformer()
    manipulator = DataManipulator()

    # Saco el token del request
    token = get_token(request)
    # Formateo los args
    fecha_inicio = request.args.get('inicio')
    fecha_fin = request.args.get('fin')
    # Tiene que ser una sola carrera y un solo plan para calcular creditos
    carrera = request.args.get('carrera')
    plan = request.args.get('plan')
    # Traigo las cursadas
    cursadas_json = provider.get_materiascursadas(token, carrera)
    cursadas_data = transformer.transform_materiascursadas_to_dataframe(
        cursadas_json)

    # Filtro periodo
    df = manipulator.filtrar_periodo(cursadas_data, fecha_inicio, fecha_fin)
    return df


def get_plan(request):
    provider = DataProvider()
    transformer = DataTransformer()

    # Saco el token del request
    token = get_token(request)
    # Formateo los args
    fecha_inicio = request.args.get('inicio')
    fecha_fin = request.args.get('fin')
    # Tiene que ser una sola carrera y un solo plan para calcular creditos
    carrera = request.args.get('carrera')
    plan = request.args.get('plan')
    # Traigo el plan
    plan_json = provider.get_plan(token, carrera, plan)
    plan_data = transformer.transform_to_dataframe(plan_json)
    return plan_data


def get_materiascursadas_plan(request):
    transformer = DataTransformer()

    cursadas_data = get_materiascursadas(request)
    plan_data = get_plan(request)
    data = transformer.merge_materias_con_plan(cursadas_data, plan_data)
    return data, cursadas_data, plan_data


@app.route('/')
def home():
    """
        Token must come as part of the request
    """
    dp = DataProvider()
    token = dp.retrieve_token(
        username=app.config['USERNAME'], password=app.config['PASSWORD'])
    # data = dp.retrieve_plan(token, 'W', '2019')
    # data = dp.retrieve_materiascursadas(token, 'W')
    # data = dp.get_materiascursadas(token, 'W')
    data = dp.get_inscriptos(token, 'W')
    # dataframe = DataTransformer().transform_to_dataframe(data)
    return json.dumps(data)


@app.route('/materias/<cod_materia>/recursantes')
@tiene_jwt
def recursantes_materia(cod_materia):

    token = get_token(request)

    cod_materia = cod_materia.zfill(5)
    carrera = request.args.get('carrera')
    dm = DataManipulator()

    # Filtro los inscriptos de la carrera y materia
    inscriptos = DataProvider().get_inscriptos(token, carrera)
    inscriptos_df = DataTransformer().transform_materiascursadas_to_dataframe(inscriptos)
    inscriptos_df = dm.filtrar_alumnos_de_materia(inscriptos_df, cod_materia)

    # Filtro las cursadas de la carrera y materia
    cursadas = DataProvider().get_materiascursadas(token, carrera)
    cursadas_df = DataTransformer().transform_materiascursadas_to_dataframe(cursadas)
    cursadas_df = dm.filtrar_alumnos_de_materia(cursadas_df, cod_materia)

    merge_df = pd.merge(inscriptos_df, cursadas_df, on=['alumno', 'codigo'])

    return merge_df['alumno'].value_counts().to_dict()


@app.route('/materias/<cod_materia>/detalle-aprobados')
@tiene_jwt
def detalle_aprobados(cod_materia):
    token = get_token(request)
    # Proceso los argumentos
    cod_materia = cod_materia.zfill(5)
    fecha_inicio = request.args.get('inicio')
    fecha_fin = request.args.get('fin')
    carreras_str = request.args.get('carreras')
    carreras = carreras_str.split(',') if carreras_str else []

    provider = DataProvider()
    manipulator = DataManipulator()

    json_data = provider.get_materiascursadas_multiples_carreras(
        token, carreras)
    df = DataTransformer().transform_materiascursadas_to_dataframe(json_data)

    df = manipulator.filtrar_alumnos_de_materia_periodo(
        df, cod_materia, fecha_inicio, fecha_fin)
    df = manipulator.filtrar_aprobados(df)
    detalle_aprobados = manipulator.cantidades_formas_aprobacion(df)
    data = detalle_aprobados.to_dict()
    return json.dumps([{"Tipo": nombre, "Cantidad": valor} for nombre, valor in data.items()])


@app.route('/materias/<cod_materia>/basicos')
@tiene_jwt
def datos_basicos_materia(cod_materia):
    token = get_token(request)
    # Proceso los argumentos
    cod_materia = cod_materia.zfill(5)
    fecha_inicio = request.args.get('inicio')
    fecha_fin = request.args.get('fin')
    carreras_str = request.args.get('carreras')
    carreras = carreras_str.split(',') if carreras_str else []
    # Traigo las materias cursadas
    json_data = DataProvider().get_materiascursadas_multiples_carreras(token, carreras)
    df = DataTransformer().transform_materiascursadas_to_dataframe(json_data)
    manipulator = DataManipulator()
    df = manipulator.filtrar_alumnos_de_materia_periodo(
        df, cod_materia, fecha_inicio, fecha_fin)
    aprobados = manipulator.cantidad_alumnos_aprobados(df, cod_materia)
    desaprobados = manipulator.cantidad_alumnos_desaprobados(df, cod_materia)
    ausentes = manipulator.cantidad_alumnos_ausentes(df, cod_materia)
    faltantes = manipulator.cantidad_alumnos_falta_aprobar(df, cod_materia)
    nombre = manipulator.get_nombre_materia(df, cod_materia)
    return json.dumps([{'Materia': cod_materia,
                        'Nombre': nombre,
                        'Aprobados': aprobados,
                        'Ausentes': ausentes,
                        'Desaprobados': desaprobados,
                        'Faltantes': faltantes}])


@app.route('/alumnos/<legajo>/porcentajes-areas')
@tiene_jwt
def porcentajes_areas_alumno(legajo):
    merged_data, _, plan_data = get_materiascursadas_plan(request)

    fecha_inicio = request.args.get('inicio')
    fecha_fin = request.args.get('fin')
    manipulator = DataManipulator()
    materias_alumno = manipulator.filtrar_materias_de_alumno(
        merged_data, legajo)
    materias_alumno = manipulator.filtrar_periodo(
        materias_alumno, fecha_inicio, fecha_fin)
    data = manipulator.porcentajes_aprobadas_areas(
        plan_data, materias_alumno)
    return json.dumps([{"nombre": nombre, "valor": valor} for nombre, valor in data.items()])


@app.route('/alumnos/<legajo>/porcentajes-nucleos')
@tiene_jwt
def porcentajes_nucleos_alumno(legajo):
    merged_data, _, plan_data = get_materiascursadas_plan(request)

    fecha_inicio = request.args.get('inicio')
    fecha_fin = request.args.get('fin')
    manipulator = DataManipulator()
    materias_alumno = manipulator.filtrar_materias_de_alumno(
        merged_data, legajo)
    materias_alumno = manipulator.filtrar_periodo(
        materias_alumno, fecha_inicio, fecha_fin)
    data = manipulator.porcentajes_aprobadas_nucleos(
        plan_data, materias_alumno)
    return json.dumps([{"nombre": nombre, "valor": valor} for nombre, valor in data.items()])


@app.route('/carreras/<carrera>/alumnos')
@tiene_jwt
def alumnos_carrera(carrera):
    token = get_token(request)
    transformer = DataTransformer()
    json_data = DataProvider().get_alumnos_de_carrera(token, carrera)
    data = transformer.transform_to_dataframe(json_data)
    inscriptos = DataManipulator().inscriptos_por_carrera(data)['alumno']
    return json.dumps([{"nombre": transformer.transform_timestamp_to_semester(key), "cantidad": value} for key, value in inscriptos.items()])

@app.route('/carreras/<carrera>/cantidades-alumnos')
@tiene_jwt
def cantidades_alumnos_carrera(carrera):
    '''
        Deberia retornar una lista del tipo [{"anio": 2015, "graduados": 2, "cursantes": 200, "ingresantes": 100, "postulantes": 500}]
    '''
    token = get_token(request)
    provider = DataProvider()
    graduados = provider.get_graduados(token, carrera)
    ingresantes = provider.get_ingresantes(token, carrera)
    cursantes = provider.get_cursantes(token, carrera)
    return json.dumps([{"Cohorte": cursantes[i]["anio"], 
                        "Graduados": graduados[i]["cantidad"], 
                        "Cursantes": cursantes[i]["cantidad"], 
                        "Ingresantes": ingresantes[i]["cantidad"]}
                        for i in range(0, len(cursantes))
                        ])

@app.route('/carreras/<carrera>/cantidades-ingresantes')
@tiene_jwt
def cantidades_ingresantes_carrera(carrera):
    '''
        Deberia retornar una lista del tipo [{"anio": 2015, "ingresantes": 100}]
    '''
    token = get_token(request)
    provider = DataProvider()
    ingresantes = provider.get_ingresantes(token, carrera)
    return json.dumps([{"Cohorte": dato["anio"], "Alumnos ingresantes": dato["cantidad"]} for dato in ingresantes ])



@app.route('/carreras/<carrera>/cursantes-actual')
@tiene_jwt
def cantidad_cursantes_actual(carrera):
    token = get_token(request)
    provider = DataProvider()
    anio = date.today().year
    cursantes = provider.get_cursantes(token, carrera, anio)
    return json.dumps({'nombre': 'Cursantes del año actual', 'valor': cursantes["cantidad"]})

@app.route('/carreras/<carrera>/ingresantes-actual')
@tiene_jwt
def cantidad_ingresantes_actual(carrera):
    token = get_token(request)
    provider = DataProvider()
    anio = date.today().year
    cursantes = provider.get_ingresantes(token, carrera, anio)
    return json.dumps({'nombre': 'Ingresantes del año actual', 'valor': cursantes["cantidad"]})

@app.route('/carreras/<carrera>/graduados-total')
@tiene_jwt
def cantidad_graduados(carrera):
    token = get_token(request)
    provider = DataProvider()
    anio = date.today().year
    cursantes = provider.get_graduados(token, carrera, anio)
    return json.dumps({'nombre': 'Graduados', 'valor': cursantes["cantidad"]})

@app.route('/widget')
def widget():
    return json.dumps({'nombre': 'Aprobados', 'valor': 55})

@app.route('/alumnos/<legajo>/porcentajes-creditos-nucleos')
@tiene_jwt
def porcentajes_creditos_alumno(legajo):
    merged_data, _, plan_data = get_materiascursadas_plan(request)

    manipulator = DataManipulator()
    # Filtro las materias
    materias_alumno = manipulator.filtrar_materias_de_alumno(
        merged_data, legajo)
    aprobadas = manipulator.filtrar_aprobados(materias_alumno)

    porcentajes = manipulator.porcentajes_creditos_nucleos(
        plan_data, aprobadas)
    return json.dumps([porcentajes])


@app.route('/alumnos/<legajo>/porcentajes-creditos-areas')
@tiene_jwt
def porcentajes_creditos_areas(legajo):
    merged_data, _, plan_data = get_materiascursadas_plan(request)

    manipulator = DataManipulator()
    # Filtro las materias
    materias_alumno = manipulator.filtrar_materias_de_alumno(
        merged_data, legajo)
    aprobadas = manipulator.filtrar_aprobados(materias_alumno)

    porcentajes = manipulator.porcentajes_creditos_areas(
        plan_data, aprobadas)
    return json.dumps([porcentajes])


@app.route('/alumnos/<legajo>/creditos-nucleos')
@tiene_jwt
def creditos_nucleos(legajo):
    merged_data, _, _ = get_materiascursadas_plan(request)

    manipulator = DataManipulator()
    # Filtro las materias
    materias_alumno = manipulator.filtrar_materias_de_alumno(
        merged_data, legajo)
    aprobadas = manipulator.filtrar_aprobados(materias_alumno)

    data = manipulator.cantidades_creditos_nucleos(
        aprobadas, ['B', 'A', 'I', 'C'])

    return json.dumps([data])


@app.route('/alumnos/<legajo>/creditos-areas')
@tiene_jwt
def creditos_areas(legajo):
    merged_data, _, plan_data = get_materiascursadas_plan(request)

    manipulator = DataManipulator()
    # Filtro las materias
    materias_alumno = manipulator.filtrar_materias_de_alumno(
        merged_data, legajo)
    aprobadas = manipulator.filtrar_aprobados(materias_alumno)

    areas = manipulator.areas_unicas(plan_data)

    data = manipulator.cantidades_creditos_areas(aprobadas, areas)

    return json.dumps([data])

@app.route('/alumnos/<legajo>/scores')
@tiene_jwt
def promedios_alumno(legajo):
    merged_data, _, plan_data = get_materiascursadas_plan(request)
    manipulator = DataManipulator()
    # Filtro las materias
    materias_alumno = manipulator.filtrar_materias_de_alumno(
        merged_data, legajo)
    # Recalculo las notas faltantes
    data_recalculada = manipulator.recalcular_notas_faltantes(materias_alumno)
    # Aplico periodos a las fechas
    periodos = manipulator.aplicar_periodos(data_recalculada)
    # Aplico los scores
    data = manipulator.aplicar_scores(periodos)
    scores = manipulator.scores_periodos(data)
    return json.dumps([{"nombre": row["periodo_semestre"], "cantidad": row["score_periodo"]} for index,row in scores.iterrows()])

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
