from hashlib import sha256
from pathlib import Path


def calcular_sha256(ruta: Path) -> str:
    hasher = sha256()
    with ruta.open("rb") as fichero:
        for bloque in iter(lambda: fichero.read(65536), b""):
            hasher.update(bloque)

    return hasher.hexdigest()


def verificar_lote(manifiesto: Path) -> None:
    """Compara el SHA-256 de cada archivo del manifiesto con su valor esperado."""
    carpeta_datos = manifiesto.parent
    archivos_verificados = 0

    with manifiesto.open("r", encoding="utf-8") as fichero:
        for numero_linea, linea in enumerate(fichero, start=1):
            linea = linea.strip()
            if not linea:
                continue

            partes = linea.split(maxsplit=1)
            if len(partes) != 2 or len(partes[0]) != 64:
                raise ValueError(f"Formato incorrecto en línea {numero_linea} del manifiesto")

            hash_esperado, nombre_archivo = partes
            ruta_archivo = carpeta_datos / nombre_archivo
            hash_obtenido = calcular_sha256(ruta_archivo)
            archivos_verificados += 1

            if hash_obtenido.lower() == hash_esperado.lower():
                print(f"VALIDO: {nombre_archivo}")
            else:
                print(f"RECHAZADO: {nombre_archivo} (el hash no coincide)")

    if archivos_verificados == 0:
        raise ValueError("El manifiesto no contiene archivos para verificar")


if __name__ == "__main__":
    # La ruta se calcula desde este script para poder ejecutarlo desde cualquier carpeta.
    proyecto = Path(__file__).resolve().parents[1]
    manifiesto = (
        proyecto
        / "datos_previos"
        / "raw_batch_202611"
        / "manifest_checksums.sha256"
    )
    verificar_lote(manifiesto)