# Guion del demo (sección 7)

## Antes del demo (no omitir)

- [ ] `python manage.py sembrar_demo --reiniciar` justo antes de empezar: los reportes de ejemplo tienen horas relativas a "ahora" (uno de hace 12 min, otro de hace 4 h...). Si siembras la víspera, todo saldrá "sin confirmar".
- [ ] Probar el flujo completo una vez en el teléfono que se va a usar.
- [ ] Plan B: capturas o un vídeo corto de los 4 flujos por si falla la conexión o hay apagón. Las losetas del mapa ya vistas quedan en caché, así que abrir la app una vez con conexión ayuda.
- [ ] Equipos cargados.
- [ ] Si se quiere enseñar el extra de IA: `IA_HABILITADA=True` en `.env` (funciona sin clave, con el extractor por reglas).
- [ ] Revisar el parte de la UNE de esa mañana para la cifra del déficit.

## Flujo 1 · Encontrar dónde cargar (sin sesión)

1. Abrir la app. Aceptar el permiso de ubicación: el mapa se centra.
2. Tocar **⚡ Con energía ahora**. Quedan solo los verdes.
3. Tocar el pin de **Cafetería El Portal**: "Con energía · confirmado hace 12 min", horario, 4 tomas, con consumo.
4. **Cómo llegar** → abre la ruta a pie en la app de mapas.

Mensaje: en menos de 30 segundos de "no sé dónde" a "voy para allá".

Detalle para enseñar: **Casa de Mirta** sale gris, "sin confirmar", porque su último reporte tiene 4 horas. Y **Casa de Pedro** tiene un círculo punteado: ubicación aproximada.

## Flujo 2 · Compartir un punto (luis@demo.local)

1. Entrar como `luis@demo.local` / `Demo1234!`.
2. **Agregar punto** → tocar el mapa para poner el pin.
3. Tipo **Vivienda** → aparece el aviso de ubicación aproximada.
4. Tomas, horario (atajo "L–V"), acceso.
5. **Enviar** → "Mis puntos": *Pendiente de revisión*.

## Flujo 3 · Confirmar el estado (ana@demo.local)

1. Entrar como `ana@demo.local`.
2. Abrir **Barbería Los Amigos** (gris, sin confirmar).
3. **¿Hay corriente ahora?** → **Con energía**. Un toque.
4. La ficha pasa a verde "confirmado hace un momento" y la reputación (★ arriba) sube.

## Flujo 4 · Moderar (moderador@demo.local)

1. Entrar en `/admin/` como `moderador@demo.local`.
2. **Puntos de carga**: los pendientes salen primero. "Cafeteria el Portal" tiene la marca de avisos: posible duplicado → acción **Ocultar**.
3. "Casa de Lázaro" (y el que creó Luis) → acción **Aprobar**. La reputación del autor sube 5.
4. **Denuncias**: la de "Paladar La Esquina" → aceptar o descartar.
5. Abrir un punto → **Historial**: la acción quedó registrada con quién y cuándo.

## Extra · Alta asistida con IA

1. En **Agregar punto**, pegar: `hay corriente en casa de Pedro, de 6 a 10 de la noche, dos enchufes`.
2. **Generar borrador** → nombre "Casa de Pedro", vivienda, 2 tomas, 18:00–22:00 todos los días.
3. Leer los avisos, colocar el pin y confirmar. Nada se publicó hasta pulsar **Enviar**.
