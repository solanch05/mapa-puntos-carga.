# Guía del código

Esta guía sigue el orden del guion de la exposición. Para cada sección dice **qué archivo lo implementa** y **cómo funciona**, para poder explicarlo y responder preguntas.

## Recorrido de una petición (de punta a punta)

Ejemplo: el usuario pulsa "Con energía" en la ficha de un punto.

1. `frontend/src/components/BotonesReporte.jsx` llama a `api.reportarEstado(id, {estado})`.
2. `frontend/src/api/puntos.js` arma un `FormData` y llama a `peticion()`.
3. `frontend/src/api/cliente.js` añade la cabecera `Authorization: Bearer <token>` y hace `fetch('/api/puntos/7/reportes/')`. Si no hay red, `puntos.js` guarda el reporte en la cola offline.
4. En el servidor, `config/urls.py` dirige la URL a `ReportesDePuntoView` (`apps/reportes/views.py`).
5. DRF comprueba, en este orden: autenticación JWT → permiso (`IsAuthenticatedOrReadOnly`) → límite de peticiones (`throttle_scope = "reportes"`).
6. `ReporteSerializer` valida el estado. Si hay foto, `imagenes.procesar_foto()` la limpia.
7. Se guarda el reporte y se suma reputación (máximo una vez cada 30 min por punto).
8. Se recalcula `estado_actual()` y se devuelve en el JSON. El frontend recarga la ficha y el mapa.

## Sección 4 · Los bloques

| Bloque | Dónde empezar a leer |
|---|---|
| Frontend | `frontend/src/main.jsx` → `App.jsx` (rutas) → `pages/MapaPage.jsx` |
| Backend | `backend/config/urls.py` (todas las rutas en un sitio) → `apps/*/views.py` |
| Base de datos | `apps/*/models.py` y las migraciones en `apps/*/migrations/` |
| IA | `apps/ia/extractor.py` (borrador) y `apps/ia/detector.py` (duplicados y spam) |

## Sección 5 · Esquema de datos

- `apps/usuarios/models.py` → tabla `usuario`. Hereda de `AbstractUser` para tener el hash de contraseñas gratis. El `save()` sincroniza el rol con `is_staff` (acceso al panel).
- `apps/puntos/models.py` → `punto_carga`, `horario`, `favorito`. Fíjate en:
  - `PointField(geography=True)`: PostGIS guarda un punto en la esfera terrestre; las distancias salen en metros.
  - `save()`: las viviendas siempre son aproximadas y `ubicacion_publica` se calcula con `ajustar_a_rejilla()`.
  - `Favorito` usa `CompositePrimaryKey` (nuevo en Django 5.2): la clave es el par (usuario, punto), como pide el documento.
- `apps/reportes/models.py` → `reporte_estado`.
- `apps/moderacion/models.py` → `denuncia`.

**"El estado actual no se guarda, se calcula"** → `apps/reportes/services.py`. Lee `anotar_estado_actual()`: con `Subquery` + `OuterRef` el ORM genera una subconsulta que, para cada punto, busca su último reporte vigente. Todo en una sola consulta (evita el problema N+1).

## Sección 6 · Decisiones técnicas en el código

| Decisión | Archivo |
|---|---|
| PWA y caché | `frontend/vite.config.js` (bloque `VitePWA`) |
| Leaflet + OSM | `frontend/src/components/MapaPuntos.jsx` |
| JWT corto + refresco | `backend/config/settings.py` (`SIMPLE_JWT`) y `frontend/src/api/cliente.js` (`refrescarToken`) |
| Monolito modular | `backend/apps/` (una app por responsabilidad) |
| IA desde el backend | `backend/apps/ia/views.py` |
| Docker + Actions | `docker-compose.yml`, `*/Dockerfile`, `.github/workflows/ci.yml` |

## Sección 7 · Los flujos del demo

| Flujo | Frontend | Backend |
|---|---|---|
| 1. Encontrar | `pages/MapaPage.jsx`, `components/Filtros.jsx`, `components/FichaPunto.jsx` | `PuntoViewSet.list` y `retrieve` + `puntos/services.py` (`filtrar_puntos`, `condicion_abierto`) |
| 2. Compartir | `pages/PuntoFormPage.jsx`, `SelectorUbicacion.jsx`, `EditorHorarios.jsx` | `PuntoViewSet.create` → `_decidir_publicacion()` |
| 3. Confirmar | `components/BotonesReporte.jsx`, `api/colaOffline.js` | `reportes/views.py` |
| 4. Moderar | Enlace "Moderar" en la barra (solo moderadores) | `puntos/admin.py`, `moderacion/admin.py`, `moderacion/services.py` |
| Extra IA | `components/AsistenteIA.jsx` | `ia/views.py`, `ia/extractor.py` |

### Cómo decide el sistema si un punto se publica directo

`PuntoViewSet._decidir_publicacion()`:

1. El detector (`ia/detector.py`) busca puntos a menos de 60 m con nombre parecido (similitud ≥ 0,6) y texto sospechoso (enlaces, palabras de spam, todo en mayúsculas).
2. Si el autor es de confianza (reputación ≥ 20 o moderador) **y** no hay avisos → `activo`.
3. Si no → `pendiente`, con los avisos en `nota_moderacion` para el moderador.

### "Abierto ahora"

`puntos/services.py` → `condicion_abierto()`. Un horario cubre la hora actual si:
- es de hoy y la hora cae entre inicio y fin; o
- cruza la medianoche (fin < inicio) y hoy ya pasamos el inicio; o
- es de **ayer**, cruza la medianoche y aún no llegamos al fin (22:00–02:00 sigue abierto el martes a la 01:00); o
- inicio = fin (00:00–00:00): todo el día.

## Sección 8 · Retos → código

| Reto | Implementación |
|---|---|
| Arranque en frío | `python manage.py sembrar_demo` (15 puntos en el centro de Santa Clara) |
| Datos que caducan | Ventana de 3 h, "hace X min" en la ficha, "sin confirmar" por defecto |
| Conexión débil | Service worker + `api/colaOffline.js` + `AvisoConexion.jsx` |
| Spam | Límites de peticiones, reputación, denuncias, cola de moderación, detector |
| Privacidad | Rejilla de ubicación, contacto bajo solicitud, pausar/retirar en "Mis puntos" |
| Mapa base incompleto | Pin manual + campo "Referencias para llegar" |
| La IA se equivoca | Validación con el serializador, avisos, extractor por reglas como respaldo |

## Sección 9 · Calidad

- `backend/tests/`: 70 pruebas con pytest sobre PostGIS real. Ejecuta `pytest -v` para ver los nombres; están escritos como frases ("test_reporte_de_mas_de_3_horas_no_es_estado_actual").
- El criterio de aceptación del documento ("un reporte de más de 3 horas no puede mostrarse como estado actual") es literalmente una prueba en `tests/test_estado_actual.py`.
- `frontend/e2e/flujos.spec.js`: Playwright en un Pixel 5 simulado. Comprueba además la métrica de "menos de 30 segundos hasta la ficha".

## Conceptos nuevos (si vienes de Django)

**React.** La interfaz se escribe como funciones (componentes) que devuelven HTML (JSX). Cuando cambia el *estado* (`useState`), React vuelve a pintar ese componente. `useEffect` ejecuta código cuando algo cambia (p. ej. cargar puntos cuando se mueve el mapa). Equivalente mental: cada componente es una plantilla de Django que se repinta sola.

**Vite.** El "runserver" del frontend: sirve los archivos en desarrollo y los empaqueta para producción (`npm run build` → carpeta `dist/`). En desarrollo reenvía `/api` a Django (`server.proxy` en `vite.config.js`), así no hay problemas de CORS.

**PWA y service worker.** Un service worker es un script que el navegador instala y que se sitúa entre la app y la red. Decide si responder desde la caché o desde internet. `vite-plugin-pwa` lo genera a partir de la configuración.

**Leaflet.** Librería de mapas. `react-leaflet` la envuelve en componentes: `<MapContainer>`, `<TileLayer>` (las imágenes del mapa de OSM), `<CircleMarker>` (cada pin).

**JWT.** Al iniciar sesión, el servidor firma un token con el id del usuario. El cliente lo manda en cada petición y el servidor solo comprueba la firma: no guarda sesiones. El de acceso dura 15 min (si lo roban, sirve poco); el de refresco, 7 días, y solo sirve para pedir otro de acceso. Con rotación, cada refresco invalida el anterior.

**PostGIS / GeoDjango.** PostGIS añade a PostgreSQL tipos geográficos y funciones como `ST_DWithin` (¿está a menos de X metros?). GeoDjango permite usarlas desde el ORM: `filter(ubicacion__dwithin=(punto, D(km=1)))`. El índice GiST es a la geografía lo que un índice B-tree a los números.

## Comandos útiles

```bash
python manage.py sembrar_demo --reiniciar   # recrea los datos de demo
python manage.py createsuperuser            # tu propio admin
python manage.py shell                      # probar el ORM a mano
pytest -k estado -v                         # solo las pruebas del estado
npx playwright test --headed                # ver el navegador durante la prueba e2e
```
