"""Inspecciona los archivos aprobados antes de decidir cómo limpiarlos."""

import json
import logging
from pathlib import Path

import pandas as pd


def cargar_lote(carpeta_entrada: Path) -> pd.DataFrame:
    """Lee los CSV verificados, los une y muestra su estructura y sus valores nulos."""
    archivos = sorted(carpeta_entrada.glob("*.csv"))
    if not archivos:
        raise FileNotFoundError(f"No hay archivos CSV verificados en {carpeta_entrada}")

    tablas = []
    for archivo in archivos:
        # read_csv convierte cada archivo CSV en una tabla de pandas (DataFrame).
        tabla = pd.read_csv(archivo)
        tablas.append(tabla)
        mensaje = f"{archivo.name}: {len(tabla)} filas y {len(tabla.columns)} columnas"
        print(mensaje)
        logging.info(mensaje)

    # Unimos las tiendas en una tabla; ignore_index crea una numeración continua de filas.
    datos = pd.concat(tablas, ignore_index=True)
    print(f"\nLote conjunto: {len(datos)} filas y {len(datos.columns)} columnas")
    print("\nColumnas:")
    for columna in datos.columns:
        print(f"- {columna}")

    # isna detecta celdas vacías; sum cuenta cuántas hay en cada columna.
    nulos = datos.isna().sum()
    print("\nValores nulos por columna:")
    print(nulos.to_string())
    logging.info("Lote conjunto: %s filas y %s columnas", len(datos), len(datos.columns))
    logging.info("Valores nulos por columna: %s", nulos.to_dict())
    return datos


def tratar_nulos(datos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aparta filas sin identificador e imputa nulos de las demás columnas."""
    columnas_obligatorias = [
        "id_transaccion",
        "timestamp",
        "importe_eur",
        "unidades",
    ]
    columnas_faltantes = [columna for columna in columnas_obligatorias if columna not in datos]
    if columnas_faltantes:
        raise ValueError(f"Faltan columnas obligatorias: {columnas_faltantes}")

    # Un identificador vacío no permite rastrear ni distinguir la transacción.
    ids_vacios = datos["id_transaccion"].isna() | (
        datos["id_transaccion"].astype("string").str.strip() == ""
    )
    rechazados = datos.loc[ids_vacios].copy()
    rechazados["motivo_rechazo"] = "id_transaccion nulo"
    logging.warning("Filas apartadas por id_transaccion nulo: %s", len(rechazados))

    # Las filas restantes se pueden conservar y completar según el tipo de dato.
    limpios = datos.loc[~ids_vacios].copy()
    medianas = limpios["importe_eur"].median()
    if pd.isna(medianas):
        raise ValueError("No se puede imputar importe_eur: no hay valores numéricos disponibles")
    limpios["importe_eur"] = limpios["importe_eur"].fillna(medianas)
    print(f"importe_eur: nulos rellenados con la mediana ({medianas})")
    logging.info("Nulos de importe_eur imputados con la mediana: %s", medianas)

    for columna in ("categoria", "metodo_pago"):
        if columna not in limpios.columns:
            continue
        valores_frecuentes = limpios[columna].mode(dropna=True)
        if limpios[columna].isna().any() and valores_frecuentes.empty:
            raise ValueError(f"No se puede imputar {columna}: no hay valores disponibles")
        if not valores_frecuentes.empty:
            valor_mas_frecuente = valores_frecuentes.iloc[0]
            limpios[columna] = limpios[columna].fillna(valor_mas_frecuente)
            print(f"{columna}: nulos rellenados con la moda ({valor_mas_frecuente})")
            logging.info("Nulos de %s imputados con la moda: %s", columna, valor_mas_frecuente)

    print(f"\nFilas apartadas por falta de identificador: {len(rechazados)}")
    print(f"Filas conservadas tras tratar nulos: {len(limpios)}")
    print("\nNulos restantes:")
    print(limpios.isna().sum().to_string())
    return limpios, rechazados


def validar_fechas_y_dominio(datos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aparta fechas inválidas y valores fuera de las reglas de negocio."""
    datos = datos.copy()
    # errors="coerce" convierte fechas ilegibles en NaT para poder detectarlas.
    fechas = pd.to_datetime(datos["timestamp"], errors="coerce")
    importes = pd.to_numeric(datos["importe_eur"], errors="coerce")
    unidades = pd.to_numeric(datos["unidades"], errors="coerce")

    ahora = pd.Timestamp.now()
    inicio_ano = pd.Timestamp(year=ahora.year, month=1, day=1)
    reglas_invalidas = [
        (fechas.isna(), "timestamp inválido"),
        (fechas < inicio_ano, f"timestamp anterior al año {ahora.year}"),
        (fechas > ahora, "timestamp futuro"),
        (importes.isna(), "importe_eur no numérico"),
        (importes <= 0, "importe_eur debe ser mayor que 0"),
        (unidades.isna(), "unidades no numéricas"),
        (unidades < 1, "unidades debe ser al menos 1"),
    ]

    # Una fila puede incumplir más de una regla; guardamos todos sus motivos.
    motivos = pd.Series("", index=datos.index, dtype="string")
    for mascara, motivo in reglas_invalidas:
        motivos.loc[mascara] = motivos.loc[mascara].apply(
            lambda anterior: f"{anterior}; {motivo}" if anterior else motivo
        )

    mascara_rechazo = motivos.ne("")
    rechazados = datos.loc[mascara_rechazo].copy()
    rechazados["motivo_rechazo"] = motivos.loc[mascara_rechazo]

    validos = datos.loc[~mascara_rechazo].copy()
    # Normalizamos el formato de fecha y los tipos numéricos tras validar.
    validos["timestamp"] = fechas.loc[~mascara_rechazo].dt.strftime("%Y-%m-%d %H:%M:%S")
    validos["importe_eur"] = importes.loc[~mascara_rechazo]
    validos["unidades"] = unidades.loc[~mascara_rechazo]

    print(f"\nFilas apartadas por fecha o dominio inválidos: {len(rechazados)}")
    print(f"Filas válidas para continuar: {len(validos)}")
    logging.warning("Filas apartadas por fecha o dominio inválidos: %s", len(rechazados))
    return validos, rechazados


def detectar_outliers_importe(
    datos: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Detecta y aparta importes atípicos mediante el criterio IQR.
    # IQR es el rango intercuartílico: Q3 menos Q1; marca valores muy alejados del centro.
    q1 = datos["importe_eur"].quantile(0.25)
    q3 = datos["importe_eur"].quantile(0.75)
    iqr = q3 - q1
    limite_inferior = q1 - 1.5 * iqr
    limite_superior = q3 + 1.5 * iqr

    mascara_outlier = (datos["importe_eur"] < limite_inferior) | (
        datos["importe_eur"] > limite_superior
    )
    outliers = datos.loc[mascara_outlier].copy()
    outliers["motivo_rechazo"] = "outlier de importe (criterio IQR)"
    datos_sin_outliers = datos.loc[~mascara_outlier].copy()

    print(
        "\nCriterio IQR para importe_eur: "
        f"límite inferior={limite_inferior:.2f}, "
        f"límite superior={limite_superior:.2f}"
    )
    print(f"Importes atípicos apartados: {len(outliers)}")
    if not outliers.empty:
        print(outliers[["id_transaccion", "importe_eur"]].to_string(index=False))

    logging.info(
        "Criterio IQR de importes: Q1=%s, Q3=%s, IQR=%s, límites=(%s, %s)",
        q1,
        q3,
        iqr,
        limite_inferior,
        limite_superior,
    )
    logging.warning("Importes atípicos apartados por IQR: %s", len(outliers))
    return datos_sin_outliers, outliers


def guardar_resultados(
    datos_limpios: pd.DataFrame,
    rechazados: pd.DataFrame,
    proyecto: Path,
) -> None:
    """Guarda el dataset preparado y genera métricas."""
    carpeta_procesados = proyecto / "processed"
    carpeta_informes = proyecto / "reports"
    carpeta_muestras = proyecto / "output_samples"
    carpeta_procesados.mkdir(exist_ok=True)
    carpeta_informes.mkdir(exist_ok=True)
    carpeta_muestras.mkdir(exist_ok=True)

    archivo_dataset = carpeta_procesados / "dataset_kdd_listo.csv"
    datos_limpios.to_csv(archivo_dataset, index=False)

    total_entrada = len(datos_limpios) + len(rechazados)
    filas_completas = int(datos_limpios.notna().all(axis=1).sum())
    tasa_completitud = filas_completas / len(datos_limpios) * 100 if len(datos_limpios) else 0
    ids_unicos = int(datos_limpios["id_transaccion"].nunique())
    tasa_unicidad = ids_unicos / len(datos_limpios) * 100 if len(datos_limpios) else 0

    # La tasa de integridad compara los ficheros copiados a staging con el manifiesto.
    manifiesto = proyecto / "datos_previos" / "raw_batch_202611" / "manifest_checksums.sha256"
    total_archivos = sum(1 for linea in manifiesto.read_text(encoding="utf-8").splitlines() if linea.strip())
    archivos_aceptados = len(list((proyecto / "staging" / "verified").glob("*.csv")))
    archivos_rechazados = total_archivos - archivos_aceptados
    tasa_integridad = archivos_aceptados / total_archivos * 100 if total_archivos else 0

    importes = datos_limpios["importe_eur"]
    outliers_importe = rechazados.loc[
        rechazados["motivo_rechazo"].eq("outlier de importe (criterio IQR)"),
        "importe_eur",
    ]
    importes_antes_de_apartar_outliers = pd.concat([importes, outliers_importe])
    q1 = importes_antes_de_apartar_outliers.quantile(0.25)
    q3 = importes_antes_de_apartar_outliers.quantile(0.75)
    iqr = q3 - q1
    metricas = {
        "registros": {
            "entrada": total_entrada,
            "procesados": len(datos_limpios),
            "rechazados": len(rechazados),
        },
        "calidad": {
            "completitud_pct": round(tasa_completitud, 2),
            "unicidad_id_pct": round(tasa_unicidad, 2),
            "validez_registros_pct": round(
                len(datos_limpios) / total_entrada * 100 if total_entrada else 0,
                2,
            ),
        },
        "integridad_criptografica": {
            "archivos_total": total_archivos,
            "archivos_validados": archivos_aceptados,
            "archivos_rechazados": archivos_rechazados,
            "tasa_validacion_pct": round(tasa_integridad, 2),
        },
        "importe_eur": {
            "media": round(float(importes.mean()), 2),
            "mediana": round(float(importes.median()), 2),
            "desviacion_estandar": round(float(importes.std()), 2),
            "percentil_25": round(float(importes.quantile(0.25)), 2),
            "percentil_75": round(float(importes.quantile(0.75)), 2),
            "limite_inferior_iqr": round(float(q1 - 1.5 * iqr), 2),
            "limite_superior_iqr": round(float(q3 + 1.5 * iqr), 2),
        },
    }

    archivo_metricas = carpeta_muestras / "metricas_perfilado.json"
    archivo_metricas.write_text(
        json.dumps(metricas, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\nDataset KDD guardado en: {archivo_dataset}")
    print(f"Métricas guardadas en: {archivo_metricas}")
    logging.info("Dataset KDD guardado en %s", archivo_dataset)
    logging.info("Métricas de perfilado guardadas en %s", archivo_metricas)

if __name__ == "__main__":
    proyecto = Path(__file__).resolve().parents[1]
    carpeta_logs = proyecto / "logs"
    carpeta_logs.mkdir(exist_ok=True)

    logging.basicConfig(
        filename=carpeta_logs / "ejecucion_pipeline.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        encoding="utf-8",
    )

    carpeta_entrada = proyecto / "staging" / "verified"
    logging.info("Inicio de inspección de datos")
    datos = cargar_lote(carpeta_entrada)
    datos_sin_nulos, rechazados_sin_id = tratar_nulos(datos)
    datos_limpios, rechazados_por_reglas = validar_fechas_y_dominio(datos_sin_nulos)
    datos_limpios, outliers = detectar_outliers_importe(datos_limpios)

    # Escribimos todos los registros rechazados juntos, con su motivo correspondiente.
    archivo_rechazados = proyecto / "output_samples" / "bad_records.csv"
    todos_rechazados = pd.concat(
        [rechazados_sin_id, rechazados_por_reglas, outliers],
        ignore_index=True,
    )
    todos_rechazados.to_csv(archivo_rechazados, index=False)
    print(f"Detalle de filas apartadas guardado en: {archivo_rechazados}")
    print(f"Filas finales que continúan en el pipeline: {len(datos_limpios)}")
    logging.info(
        "Validación finalizada: %s filas listas para continuar",
        len(datos_limpios),
    )
    logging.info("Filas rechazadas guardadas en %s", archivo_rechazados)
    guardar_resultados(datos_limpios, todos_rechazados, proyecto)