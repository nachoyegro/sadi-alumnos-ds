#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd


class DataManipulator:

    ########################################### Filtrado ###############################################

    def filtrar_carreras(self, df, *carreras):
        """
            Quiero obtener las materias cursadas de carreras
            :return Dataframe
        """
        return df.loc[df['carrera'].isin(*carreras)]

    def filtrar_alumnos_de_materia(self, df, materia):
        """
            Quiero obtener los alumnos de una materia
            :return Dataframe
        """
        df = df.loc[df['codigo'] ==
                    materia]
        return df

    def filtrar_periodo(self, df, fecha_inicio, fecha_fin):
        """
            Se filtra por periodo seleccionado separando los casos correspondientes.
            Se puede querer filtrar solo "fecha mayor a" o "fecha menor a"
        """
        # Si hay fecha de inicio y fecha de fin, se filtra por gte & lte
        if fecha_inicio and fecha_fin:
            return df.loc[(df.fecha >= fecha_inicio) & (df.fecha <= fecha_fin)]
        # Si solo hay fecha de inicio, se filtra por gte
        elif fecha_inicio:
            return df.loc[(df.fecha >= fecha_inicio)]
        # Si solo hay fecha de fin, se filtra por lte
        elif fecha_fin:
            return df.loc[(df.fecha <= fecha_fin)]
        # Si no hay ni fecha de inicio ni fecha de fin, se retorna todo
        else:
            return df

    def filtrar_alumnos_de_materia_periodo(self, df, materia, fecha_inicio, fecha_fin):
        """
            Quiero obtener los alumnos de una materia en un período determinado
            :return Dataframe
        """
        df = self.filtrar_alumnos_de_materia(df, materia)
        df = self.filtrar_periodo(df, fecha_inicio, fecha_fin)
        return df

    def filtrar_aprobados(self, df):
        # A: Regular | P: Acredito
        return df.loc[(df.resultado == 'A') | (df.resultado == 'P')]

    def filtrar_ausentes(self, df):
        return df.loc[(df.resultado == 'U')]  # U: Ausente/Libre

    def filtrar_desaprobados(self, df):
        return df.loc[(df.resultado == 'R')]  # R: Reprobado

    def filtrar_pendientes(self, df):
        return df.loc[(df.resultado == 'E')]  # A: Regular | P: Acredito

    def filtrar_area(self, df, area):
        return df.loc[df['area'] == area]

    def filtrar_nucleo(self, df, nucleo):
        return df.loc[df['nucleo'] == nucleo]

    def filtrar_materias_obligatorias(self, df):
        return df.loc[df['nucleo'] != 'C']

    def filtrar_materias_de_alumno(self, df, legajo_alumno):
        return df.loc[df['alumno'] == legajo_alumno]

    def aprobados_de_materia(self, df, materia):
        """
            Obtengo los aprobados en base al resultado, no a la nota
            :return Dataframe
        """
        df = self.filtrar_alumnos_de_materia(df, materia)
        df = self.filtrar_aprobados(df)
        return df

    def pendientes_de_materia(self, df, materia):
        """
            Obtengo los pendientes en base al resultado, no a la nota
            :return Dataframe
        """
        df = self.filtrar_alumnos_de_materia(df, materia)
        df = self.filtrar_pendientes(df)
        return df

    def desaprobados_de_materia(self, df, materia):
        """
            Obtengo los desaprobados en base al resultado, no a la nota
            No tiene en cuenta los ausentes
            :return Dataframe
        """
        df = self.filtrar_alumnos_de_materia(df, materia)
        df = self.filtrar_desaprobados(df)
        return df

    def ausentes_de_materia(self, df, materia):
        """
            Obtengo los ausentes en base al resultado
            :return Dataframe
        """
        df = self.filtrar_alumnos_de_materia(df, materia)
        df = self.filtrar_ausentes(df)
        return df

    def alumnos_aprobados_materia_series(self, df, materia):
        """
            Obtengo los alumnos aprobados de una materia
            :return Series
        """
        aprobados = self.aprobados_de_materia(df, materia)
        return pd.Series(pd.unique(aprobados['alumno']))

    def alumnos_totales_materia_series(self, df, materia):
        """
            Obtengo los alumnos totales de una materia
            :return Series
        """
        alumnos = pd.unique(df['alumno'])
        return pd.Series(alumnos)

    def alumnos_falta_aprobar_materia_series(self, df, materia):
        """
            Obtengo los alumnos que aun no aprobaron esta materia
        """
        aprobados = self.alumnos_aprobados_materia_series(df, materia)
        totales = self.alumnos_totales_materia_series(df, materia)
        # Hago la resta
        # Me quedo con aquellos que estan como desaprobados/ausentes y no estan en aprobados
        resultado = totales[~totales.isin(aprobados)]
        return resultado

    def cantidad_creditos(self, df):
        return int(df['creditos'].sum())

    def cantidad_alumnos_falta_aprobar(self, df, materia):
        return len(self.alumnos_falta_aprobar_materia_series(df, materia))

    def cantidad_alumnos_aprobados(self, df, materia):
        return len(self.aprobados_de_materia(df, materia))

    def cantidad_alumnos_desaprobados(self, df, materia):
        return len(self.desaprobados_de_materia(df, materia))

    def cantidad_alumnos_ausentes(self, df, materia):
        return len(self.ausentes_de_materia(df, materia))

    def cantidad_alumnos_pendientes(self, df, materia):
        return len(self.pendientes_de_materia(df, materia))

    def cantidad_materias_distintas(self, df):
        return len(pd.unique(df['codigo']))

    # TODO: esto hay que sacarlo del plan
    def get_nombre_materia(self, df, cod_materia):
        try:
            return df.loc[df['codigo'] == cod_materia]['materia'].iloc[0]
        except:
            return ''

    def areas_unicas(self, df):
        return pd.unique(df['area'])

    def nucleos_unicos(self, df):
        return pd.unique(df['nucleo'])

    def filtrar_materias_obligatorias_area(self, df, area):
        areas_filtradas = self.filtrar_area(df, area)
        obligatorias = self.filtrar_materias_obligatorias(areas_filtradas)
        return obligatorias

    def total_materias_obligatorias_area(self, df, area):
        obligatorias = self.filtrar_materias_obligatorias_area(df, area)
        total_materias_area = self.cantidad_materias_distintas(obligatorias)
        return total_materias_area

    def porcentaje_aprobadas_area(self, plan_data, cursadas, area):
        # Calculo el total de materias de un area, en base al plan
        total_area = self.total_materias_obligatorias_area(plan_data, area)

        # Si tiene materias esa area
        if total_area:
            # Filtro las materias aprobadas del alumno dentro de esa area
            materias_obligatorias_area = self.filtrar_materias_obligatorias_area(
                cursadas, area)

            # De las materias del alumno, quiero solo las que aprobo
            materias_obligatorias_area_alumno_aprobadas = self.filtrar_aprobados(
                materias_obligatorias_area)

            # Obtengo el total de materias del area aprobadas por el alumno
            total_materias_obligatorias_area_alumno = self.cantidad_materias_distintas(
                materias_obligatorias_area_alumno_aprobadas)

            return (float(total_materias_obligatorias_area_alumno) / total_area) * 100
        else:
            return 0

    def porcentaje_aprobadas_nucleo(self, plan_data, cursadas, nucleo):
        # Filtro ambos DataFrames por nucleo
        nucleo_data = self.filtrar_nucleo(plan_data, nucleo)
        alumno_nucleo_data = self.filtrar_nucleo(
            cursadas, nucleo)

        # Filtro solo las aprobadas del alumno
        aprobadas_alumno = self.filtrar_aprobados(alumno_nucleo_data)

        # Calculo las materias distintas de ambos DataFrames
        cantidad_materias_nucleo = self.cantidad_materias_distintas(
            nucleo_data)
        cantidad_materias_aprobadas = self.cantidad_materias_distintas(
            aprobadas_alumno)

        # Calculo el porcentaje
        if cantidad_materias_nucleo:
            return (float(cantidad_materias_aprobadas) / cantidad_materias_nucleo) * 100
        else:
            return 0

    def porcentajes_aprobadas_areas(self, plan_data, cursadas_data):
        """
            Precondicion: se asume que las materias ya vienen filtradas por alumno/s
        """
        areas = self.areas_unicas(plan_data)
        result = {}
        for area in areas:
            # Si no tiene seteada el Área, no me interesa
            if area:
                result[area] = self.porcentaje_aprobadas_area(
                    plan_data, cursadas_data, area)
        return result

    def porcentajes_aprobadas_nucleos(self, plan_data, cursadas_data):
        """
            Precondicion: se asume que las materias ya vienen filtradas por alumno/s
        """
        nucleos = self.nucleos_unicos(plan_data)
        result = {}
        for nucleo in nucleos:
            # Si no tiene seteada el Área, no me interesa
            if nucleo:
                result[nucleo] = self.porcentaje_aprobadas_nucleo(
                    plan_data, cursadas_data, nucleo)
        return result

    def porcentaje_creditos(self, total_creditos, df):
        if total_creditos:
            return (float(self.cantidad_creditos(df)) / total_creditos) * 100
        else:
            return 0

    def cantidad_creditos_nucleo(self, data, nucleo):
        nucleo_data = self.filtrar_nucleo(data, nucleo)
        return self.cantidad_creditos(nucleo_data)

    def cantidades_creditos_nucleos(self, data, nucleos):
        result = {}
        for nucleo in nucleos:
            # Filtro los nucleos
            result[nucleo] = self.cantidad_creditos_nucleo(data, nucleo)
        return result

    def cantidad_creditos_area(self, data, area):
        area_data = self.filtrar_area(data, area)
        return self.cantidad_creditos(area_data)

    def cantidades_creditos_areas(self, data, areas):
        result = {}
        for area in areas:
            # Filtro las areas
            result[area] = self.cantidad_creditos_area(data, area)
        return result

    def porcentajes_creditos_areas(self, plan_data, cursadas_data):
        """
            Precondicion: se asume que las cursadas ya estan filtradas por el alumno
        """
        result = {}
        areas = self.areas_unicas(plan_data)
        for area in areas:
            area_data = self.filtrar_materias_obligatorias_area(
                plan_data, area)
            creditos_area = self.cantidad_creditos(area_data)

            alumno_area_data = self.filtrar_materias_obligatorias_area(
                cursadas_data, area)
            result[area] = self.porcentaje_creditos(
                creditos_area, alumno_area_data)
        return result

    def porcentajes_creditos_nucleos(self, plan_data, cursadas_data):
        """
            Precondicion: se asume que las cursadas ya estan filtradas por el alumno
        """
        result = {}
        nucleos = self.nucleos_unicos(plan_data)
        for nucleo in nucleos:
            if nucleo:
                nucleo_data = self.filtrar_nucleo(
                    plan_data, nucleo)
                creditos_nucleo = self.cantidad_creditos(nucleo_data)

                alumno_nucleo_data = self.filtrar_nucleo(
                    cursadas_data, nucleo)
                result[nucleo] = self.porcentaje_creditos(
                    creditos_nucleo, alumno_nucleo_data)
        return result

    def cantidades_formas_aprobacion(self, df):
        return df['forma_aprobacion'].value_counts()

    def inscriptos_por_carrera(self, dataframe):
        #Saco los que no tienen fecha de inscripcion
        df = dataframe.dropna(subset=['fecha_inscripcion'])
        #Transformo la columna en date
        df['fecha_inscripcion'] = pd.to_datetime(df['fecha_inscripcion'])
        #Agrupo por fechas cada 6 meses
        df = df.groupby(pd.Grouper(key='fecha_inscripcion', freq='6MS')).count()
        #Saco la columna plan
        df = df.drop(['plan'], axis=1)
        return df
    