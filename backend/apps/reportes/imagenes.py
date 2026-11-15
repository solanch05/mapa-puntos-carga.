"""
Tratamiento seguro de fotos subidas (sección 10, fila "Fotos").

1. Validar tipo real (abriendo la imagen, no fiándonos de la extensión) y tamaño.
2. Recodificar la imagen: se genera un JPEG nuevo a partir de los píxeles.
3. Eliminar los metadatos EXIF, que pueden contener la ubicación GPS exacta.
   Al recodificar sin pasar `exif=...`, Pillow no copia ningún metadato.
"""

import io
import uuid

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

TAMANO_MAXIMO_BYTES = 5 * 1024 * 1024
FORMATOS_PERMITIDOS = {"JPEG", "PNG", "WEBP"}
LADO_MAXIMO_PX = 1280
Image.MAX_IMAGE_PIXELS = 40_000_000  # evita "bombas de descompresión"


def procesar_foto(archivo) -> ContentFile:
    if archivo.size > TAMANO_MAXIMO_BYTES:
        raise ValidationError("La foto no puede superar 5 MB.")
    try:
        imagen = Image.open(archivo)
        imagen.verify()  # detecta archivos corruptos o que no son imágenes
        archivo.seek(0)
        imagen = Image.open(archivo)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValidationError("El archivo no es una imagen válida.") from exc

    if imagen.format not in FORMATOS_PERMITIDOS:
        raise ValidationError("Formato no permitido. Usa JPEG, PNG o WebP.")

    # Respeta la orientación de la cámara antes de descartar el EXIF.
    imagen = ImageOps.exif_transpose(imagen)
    imagen = imagen.convert("RGB")
    imagen.thumbnail((LADO_MAXIMO_PX, LADO_MAXIMO_PX))

    salida = io.BytesIO()
    imagen.save(salida, format="JPEG", quality=80, optimize=True)  # sin EXIF
    return ContentFile(salida.getvalue(), name=f"{uuid.uuid4().hex}.jpg")
