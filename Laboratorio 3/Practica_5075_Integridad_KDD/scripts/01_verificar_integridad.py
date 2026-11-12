from hashlib import sha256
from pathlib import Path


def calcular_sha256(ruta: Path) -> str:
    hasher = sha256()
    with ruta.open("rb") as fichero:
        for bloque in iter(lambda: fichero.read(65536), b""):
            hasher.update(bloque)

    return hasher.hexdigest()


if __name__ == "__main__":
    
    # Se construye la ruta desde este script para poder ejecutarlo desde cualquier carpeta.
    proyecto = Path(__file__).resolve().parents[1]
    archivo = proyecto / "datos_previos" / "raw_batch_202611" / "transacciones_tienda_norte.csv"
    print(calcular_sha256(archivo))