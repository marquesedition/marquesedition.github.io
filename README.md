# Marques Edition

Web oficial de Marques Edition migrada a Astro.

## Estructura

### Código fuente
- `src/pages/`: rutas Astro
- `src/components/layout/`: estructura compartida de páginas
- `src/components/content/`: tarjetas y bloques de contenido
- `src/config/`: configuración compartida, como la navegación
- `src/lib/`: utilidades pequeñas de formato
- `src/data/`: fuentes JSON internas de reels, streams y eventos
- `public/`: assets públicos

### Scripts
- `scripts/content/update_reels.py`: refresca datos desde Instagram
- `scripts/content/update_streams.py`: refresca datos desde YouTube
- `scripts/content/update_events.py`: genera la agenda recurrente
- `scripts/content/update_library.py`: sincroniza la library pública de Google Drive a JSON
- `scripts/content/generate_library_previews.py`: crea previews locales de 1 minuto y baja calidad para proteger los temas
- `scripts/events/import_bandsintown_events.py`: importa un bloque HTML de Bandsintown a eventos

### Publicación
- GitHub Pages se despliega desde `dist/` mediante Actions
- la fuente real está en `src/`, `public/` y `scripts/`
- si va a editar algo, empiece siempre por ahí

## Desarrollo local
```bash
npm install
./dev.sh
```

Servidor por defecto:
```text
http://localhost:5500
```

## Build
```bash
npm run build:site
```

Esto genera `dist/` con Astro. La publicación de GitHub Pages se hace desde GitHub Actions.

## Actualizar reels
```bash
python3 scripts/content/update_reels.py
npm run build:site
```

## Actualizar streams
```bash
python3 scripts/content/update_streams.py
npm run build:site
```

## Actualizar library
```bash
python3 scripts/content/update_library.py
python3 scripts/content/generate_library_previews.py
npm run build:site
```

## Actualizar contenido
```bash
npm run refresh:content
npm run build:site
```

## Actualizar agenda recurrente
```bash
python3 scripts/content/update_events.py
npm run build:site
```

## Importar eventos desde Bandsintown
```bash
npm run import:events -- bandsintown-events.html
npm run build:site
```

También puedes pegar el bloque HTML por `stdin`:
```bash
pbpaste | npm run import:events
```

El workflow `.github/workflows/update-reels.yml` hace este proceso automáticamente para events, reels y streams.
