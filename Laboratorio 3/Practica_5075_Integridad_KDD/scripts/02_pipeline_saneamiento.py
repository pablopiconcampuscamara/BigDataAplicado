"""Inspecciona los archivos aprobados antes de decidir cómo limpiarlos."""

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


def tratar_nulos(datos: pd.DataFrame, archivo_rechazados: Path) -> pd.DataFrame:
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
    rechazados.to_csv(archivo_rechazados, index=False)
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
    print(f"Detalle guardado en: {archivo_rechazados}")
    print(f"Filas conservadas tras tratar nulos: {len(limpios)}")
    print("\nNulos restantes:")
    print(limpios.isna().sum().to_string())
    return limpios


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
    archivo_rechazados = proyecto / "output_samples" / "bad_records.csv"
    datos_limpios = tratar_nulos(datos, archivo_rechazados)
    logging.info(
        "Tratamiento de nulos finalizado: %s filas listas para las siguientes validaciones",
        len(datos_limpios),
    )
    logging.info("Filas sin identificador guardadas en %s", archivo_rechazados)