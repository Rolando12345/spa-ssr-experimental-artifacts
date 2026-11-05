# Pipeline experimental SPA–SSR — campaña oficial 3.2.0

## Qué corrige esta versión

- Lighthouse, k6 y costos alternan SPA/SSR mediante AB/BA.
- Lighthouse genera una traza real de red por página.
- k6 ya no compara solamente el `index.html` estático de Angular contra el
  renderizado de Next.js. Reconstruye una navegación fría completa usando el
  documento, recursos y llamadas REST observados por Lighthouse.
- La latencia, tasa de error y throughput de k6 corresponden a transacciones
  completas, no a solicitudes de recursos aisladas.
- La navegación se reproduce en tres etapas: documento, recursos estáticos en
  paralelo y solicitudes XHR/Fetch en paralelo. Esto aproxima el patrón de un
  navegador y evita sumar artificialmente las latencias de 10–12 recursos.
- k6 concede hasta 180 segundos para terminar iteraciones iniciadas y aplica
  un timeout de 15 segundos por recurso. Las transacciones fallidas quedan
  registradas en lugar de desaparecer de las métricas.
- k6 reproduce solicitudes HTTP, pero no ejecuta JavaScript del cliente ni
  verifica la hidratación en un navegador. Por ello, el renderizado Angular en
  el navegador queda fuera de la latencia y del throughput de k6, mientras el
  renderizado de Next.js ocurre antes de devolver el documento SSR.
- La campaña oficial utiliza 1, 5, 10, 25 y 50 VUs durante 30 segundos por
  repetición. Estos niveles fueron calibrados con la campaña piloto completa
  y permiten observar la transición desde la línea base hasta la saturación.
- Un incumplimiento del SLA se conserva como resultado de degradación; no
  equivale a una ejecución incompleta.
- Cada VU limita sus lotes a 10 solicitudes y a 6 conexiones simultáneas por
  host, aproximando el comportamiento del navegador sin generar una ráfaga
  artificialmente ilimitada.
- Costos aplica la misma tasa de llegada a ambos tratamientos (1 navegación
  completa por segundo), evitando el sesgo del ciclo cerrado anterior.
- Costos incluye métricas normalizadas por transacción exitosa.

## Entorno confirmado

- Python 3.14.6
- psutil 7.2.2
- Angular SPA en `http://localhost:4200`
- Next.js SSR en `http://localhost:3000`
- Spring Boot en `http://localhost:8080`

Spring Boot y MySQL deben permanecer activos durante toda la campaña. Angular
y Next.js deben ejecutarse en modo producción.

## Preparación

```powershell
venv\Scripts\activate
python -m pip install -r requirements.txt
python --version
k6 version
lighthouse --version
```

Antes de comenzar, comprobar manualmente las seis rutas Dashboard, Inventory y
Sales en los puertos 4200 y 3000.

## Orden obligatorio cuando se ejecuta por fases

Lighthouse debe ejecutarse primero porque sus trazas generan automáticamente
los manifiestos de transacción utilizados por k6 y costos.

```powershell
python main.py --phase lighthouse
python main.py --phase k6 --keep-results
python main.py --phase costs --keep-results
```

No omitir `--keep-results` en la segunda y tercera orden. Sin ese parámetro se
eliminarían las trazas Lighthouse requeridas.

Al iniciar `--phase k6 --keep-results`, esta versión elimina solamente los
resultados, tabla y figuras anteriores de k6. Conserva las trazas Lighthouse y
los resultados de costos, evitando mezclar el piloto con la campaña oficial.

La alternativa oficial, que limpia y ejecuta todo en el orden correcto, es:

```powershell
python main.py --phase all
```

El orden automático es Lighthouse -> costos -> k6. Costos se mide antes de la
carga de estrés para evitar que el estado residual de los procesos contamine
las observaciones de CPU y RAM.

## Diseño experimental

Cada fase utiliza cinco repeticiones. En cada página y repetición se alternan
los tratamientos:

```text
Repetición 1: SPA -> SSR
Repetición 2: SSR -> SPA
Repetición 3: SPA -> SSR
Repetición 4: SSR -> SPA
Repetición 5: SPA -> SSR
```

k6 ejecuta 2 arquitecturas × 3 páginas × 5 cargas × 5 repeticiones = 150
ejecuciones. Las cargas oficiales son 1, 5, 10, 25 y 50 VUs durante 30
segundos.

En la laptop de 4 GB, 50 VUs representa el nivel de estrés calibrado. Para la
ejecución oficial deben cerrarse aplicaciones ajenas, evitar el uso del equipo
y mantenerlo conectado a la corriente. No se debe cancelar una repetición
solamente por incumplir el SLA. El pipeline exige 150/150 ejecuciones completas
antes de aceptar la campaña para agregación.

## Modelo de transacción

Después de Lighthouse se crean seis manifiestos en:

```text
config/transactions/spa/dashboard.json
config/transactions/ssr/dashboard.json
...
```

Cada manifiesto conserva las solicitudes HTTP 200 observadas durante una
navegación real: documento, CSS, JavaScript, fuentes, llamadas XHR/Fetch y otros
recursos. El modelo corresponde a una navegación fría reconstruida por etapas:
documento, descarga concurrente de recursos estáticos y carga concurrente de
datos. Esta definición debe indicarse expresamente en el artículo.

Si Angular o Next.js se vuelven a compilar y cambian los nombres hash de los
recursos, hay que volver a ejecutar Lighthouse antes de k6 y costos.

## Costos

Ambas arquitecturas reciben una tasa fija de una navegación completa por
segundo durante 30 segundos. CPU y RAM corresponden al árbol del proceso del
servidor frontend en el puerto 4200 o 3000.

La red sigue siendo un contador global del sistema con corrección por línea
base, debido a la limitación portable de psutil. Debe declararse como
limitación. Las tablas incluyen:

- CPU y RAM medias/máximas.
- transacciones exitosas y fallidas.
- transacciones exitosas por segundo.
- CPU normalizada por throughput exitoso.
- red corregida por transacción exitosa.

## Integridad

- No mezclar los resultados generados por versiones anteriores.
- Conservar los JSON originales, validaciones, logs, tablas y figuras.
- Una ejecución k6 completa que incumple el SLA se conserva como evidencia de
  saturación.
- El SLA continúa siendo P95 ≤ 2000 ms y error de transacción ≤ 20 %.
- Si una fase no completa todas sus repeticiones, no publicar resultados
  parciales sin justificar explícitamente los datos faltantes.

La carpeta `results` conserva 360 archivos JSON: 210 corresponden a las
ejecuciones oficiales (30 Lighthouse, 150 k6 y 30 recursos) y 150 son registros
de validación asociados uno a uno con las ejecuciones k6. Estos últimos son
controles de integridad y no constituyen ejecuciones adicionales.
