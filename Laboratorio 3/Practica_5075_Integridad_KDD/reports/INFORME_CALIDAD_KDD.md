# Informe de calidad del dataset KDD

## Resultados del saneamiento

- Registros de entrada: 100
- Registros preparados para análisis: 88
- Registros apartados: 12
- Completitud del dataset preparado: 100.00%
- Unicidad de *id_transaccion*: 100.00%
- Registros válidos sobre el lote de entrada: 88.00%
- Integridad criptográfica: 2 de 3 archivos validados (66.67%)

## Distribución de `importe_eur` tras la limpieza

- Media: 71.01
- Mediana: 73.22
- Desviación estándar: 26.19
- Percentil 25: 54.14
- Percentil 75: 84.94

## Decisiones de saneamiento

- Se apartaron las filas sin *id_transaccion*, porque no se pueden rastrear de forma fiable.
- El nulo de *importe_eur* se imputó con la mediana; los nulos de *categoria* y *metodo_pago*, con la moda.
- Se apartaron las filas con fechas inválidas, anteriores al año actual o futuras, e importes o unidades fuera de las reglas de negocio.
- Los importes atípicos se detectaron con el criterio IQR (límites: 7.72 y 136.38, calculados como Q1 - 1,5 × IQR y Q3 + 1,5 × IQR) y se apartaron para revisión, sin borrarlos de la evidencia.
- Los registros rechazados y sus motivos se conservan en **output_samples/bad_records.csv**.

El dataset preparado se guarda en **processed/dataset_kdd_listo.csv**. La inspección estadística ayuda a detectar valores extremos, pero no demuestra por sí sola que sean errores de negocio.
