# Política de seguridad

## Versiones soportadas

Este repositorio es un proyecto educativo de análisis de datos; mantengo la
rama `main` con soporte continuo.

| Rama | Soporte |
|--------|-----------|
| main   | ✅        |

## Alcance de esta política

Abarca el código de `src/`, `demo/` y `notebooks/`, así como el sitio estático
publicado en GitHub Pages (`docs/`). Los reportes sobre dependencias
vulnerables de `requirements.txt` también son bienvenidos.

**Fuera de alcance:**

- El contenido científico de los datos (catálogos sísmicos, censo): son
  fuentes oficiales públicas y se citan en el README.
- Solicitudes de "predicción de sismos": la sismología actual no lo permite;
  ver el README para lo que el proyecto sí hace.
- Disponibilidad del sitio (alojamiento de GitHub Pages, fuera de mi control).

## Cómo reportar una vulnerabilidad

1. **Vía preferida:** usa el *reporte privado de vulnerabilidades* de este
   repositorio (pestaña **Security → Report a vulnerability**). Está habilitado.
2. Alternativa: abre un issue **sin detalles explícitos** solicitando contacto
   seguro, y comparte los detalles por el canal privado.

**Compromiso de respuesta:** acusar recibo en un plazo de 5 días hábiles y
evaluar la severidad (CVSS cuando aplique) en un máximo de 14 días. Los
arreglos se publican en `main` con el correspondiente aviso en las notas del
release, evitando la divulgación de detalles explícitos mientras exista riesgo
activo.

## Medidas preventivas vigentes

- **Escaneo de secretos** y **protección en el push** (secret scanning + push
  protection) habilitados en el repositorio.
- **Dependabot** con actualizaciones semanales del ecosistema `pip` y de las
  acciones de GitHub (`.github/dependabot.yml`).
- **Integración continua** (`.github/workflows/ci.yml`) que verifica la
  sintaxis y la reproducibilidad del pipeline en cada push y pull request.
- El sitio de GitHub Pages es **estático**: no recopila datos personales, no
  usa cookies ni telemetría; la única referencia externa es el CDN de Plotly.
- No existen claves ni tokens en el historial del repositorio (auditado);
  el archivo `.gitignore` bloquea por defecto `.env`, claves PEM y credenciales.

## Atribución

La plantilla de esta política sigue las recomendaciones de
[github.com/security-lab](https://github.com/github/security-lab) y
[SECURITY.MD](https://security.md).
