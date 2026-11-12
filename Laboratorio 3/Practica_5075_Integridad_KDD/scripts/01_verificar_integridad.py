import logging
from hashlib import sha256
from pathlib import Path


def calcular_sha256(ruta: Path) -> str:
    """Calcula la huella SHA-256 de un archivo sin cargarlo entero en memoria."""
    hasher = sha256()
    # "rb" abre el archivo como bytes: el hash debe usar el contenido exacto.
    with ruta.open("rb") as fichero:
        # Se procesa por bloques de 64 KiB, incluso si el archivo es grande.
        for bloque in iter(lambda: fichero.read(65536), b""):
            hasher.update(bloque)

    return hasher.hexdigest()


def verificar_lote(manifiesto: Path) -> None:
    """Compara cada archivo del manifiesto y registra los resultados."""
    # Los CSV están en la misma carpeta que el manifiesto.
    carpeta_datos = manifiesto.parent
    archivos_verificados = 0
    rechazados = []

    # Cada línea del manifiesto contiene el hash esperado y el nombre del archivo.
    with manifiesto.open("r", encoding="utf-8") as fichero:
        for numero_linea, linea in enumerate(fichero, start=1):
            linea = linea.strip()
            if not linea:
                continue

            # maxsplit=1 permite que el resto de la línea sea el nombre del archivo.
            partes = linea.split(maxsplit=1)
            if len(partes) != 2 or len(partes[0]) != 64:
                raise ValueError(f"Formato incorrecto en línea {numero_linea} del manifiesto")

            hash_esperado, nombre_archivo = partes
            ruta_archivo = carpeta_datos / nombre_archivo
            hash_obtenido = calcular_sha256(ruta_archivo)
            archivos_verificados += 1

            if hash_obtenido.lower() == hash_esperado.lower():
                mensaje = f"VALIDO: {nombre_archivo}"
                print(mensaje)
                # INFO registra un resultado normal de la comprobación.
                logging.info(mensaje)
            else:
                mensaje = f"RECHAZADO: {nombre_archivo} (el hash no coincide)"
                print(mensaje)
                # WARNING señala un problema que no detiene la verificación del lote.
                logging.warning(mensaje)
                rechazados.append(
                    f"{nombre_archivo} | esperado: {hash_esperado} | obtenido: {hash_obtenido}"
                )

    if archivos_verificados == 0:
        raise ValueError("El manifiesto no contiene archivos para verificar")

    # Guardamos solo el listado de rechazados; los CSV originales no se mueven.
    proyecto = manifiesto.parents[2]
    carpeta_salida = proyecto / "output_samples"
    archivo_cuarentena = carpeta_salida / "quarantine_manifest.txt"
    contenido = "\n".join(rechazados)
    archivo_cuarentena.write_text(
        f"{contenido}\n" if contenido else "No se rechazaron archivos.\n",
        encoding="utf-8",
    )
    logging.info("Manifiesto de cuarentena guardado en %s", archivo_cuarentena)


if __name__ == "__main__":
    
    # parents[1] llega a la carpeta del proyecto.
    proyecto = Path(__file__).resolve().parents[1]
    carpeta_logs = proyecto / "logs"
    # exist_ok evita error si la carpeta ya existe.
    carpeta_logs.mkdir(exist_ok=True)
    carpeta_salida = proyecto / "output_samples"
    carpeta_salida.mkdir(exist_ok=True)

    # Configura logging para añadir mensajes al archivo y distinguir su nivel.
    logging.basicConfig(
        filename=carpeta_logs / "ejecucion_pipeline.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        encoding="utf-8",
    )

    # Construye la ruta al manifiesto a partir de la raíz del proyecto.
    manifiesto = (
        proyecto
        / "datos_previos"
        / "raw_batch_202611"
        / "manifest_checksums.sha256"
    )
    # Estos mensajes marcan el principio y el final de una ejecución.
    logging.info("Inicio de verificación del lote")
    verificar_lote(manifiesto)
    logging.info("Fin de verificación del lote")