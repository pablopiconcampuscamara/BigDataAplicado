import pandas as pd

# Rutas del archivo de entrada y del archivo de salida.
entrada = "/workspace/telemetria_envios.csv"
salida = "/workspace/telemetria_limpia.csv"

# Carga del archivo CSV original en un DataFrame de pandas.
df = pd.read_csv(entrada)

# Información inicial para conocer el estado del dataset antes de limpiar.
print(f"Filas originales: {len(df)}")
print("\nValores vacíos por columna:")
print(df.isna().sum())
print(f"\nFilas exactamente duplicadas: {df.duplicated().sum()}")
print("\nIDs de envío repetidos (revisar antes de descartarlos):")
print(df.loc[df["id_envio"].duplicated(keep=False), "id_envio"].value_counts())

# Se convierten las columnas numéricas a tipo numérico.
# Si un valor no es interpretable, se convierte a NaN para ser eliminado después.
for columna in ("peso_kg", "temp_celsius"):
    df[columna] = pd.to_numeric(df[columna], errors="coerce")

# Se eliminan filas duplicadas exactas para evitar registros repetidos.
limpio = df.drop_duplicates()

# Se eliminan filas con datos faltantes en columnas clave del proceso.
limpio = limpio.dropna(
    subset=["id_envio", "peso_kg", "temp_celsius", "destino"]
)

# Se descartan pesos negativos porque no tienen sentido en un envío válido.
limpio = limpio[limpio["peso_kg"] >= 0]

# Se elimina un valor anómalo de temperatura que podría corresponder a un error
# de medición o un dato no confiable para este caso.
limpio = limpio[limpio["temp_celsius"] != 98.4]

# Se elimina el estado "DESCONOCIDO_ERROR" sin espacios extra en el texto.
# Se usa astype("string") y str.strip() para limpiar espacios antes y después.
limpio = limpio[
    limpio["estado_envio"].astype("string").str.strip() != "DESCONOCIDO_ERROR"
]

# Se guarda la versión limpia en un archivo CSV nuevo.
limpio.to_csv(salida, index=False, encoding="utf-8")

# Resumen final del proceso de limpieza.
print(f"\nFilas limpias: {len(limpio)}")
print(f"Filas retiradas: {len(df) - len(limpio)}")
print(f"Archivo generado: {salida}")