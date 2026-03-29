# Marques Edition

Web oficial de Marques Edition migrada a Astro.

## Estructura
- `src/pages/`: rutas Astro
- `src/components/`: componentes reutilizables
- `src/data/reels.json`: fuente de datos de reels
- `src/data/streams.json`: fuente de datos de streams de YouTube
- `src/data/events.json`: fuente de datos de próximos eventos
- `public/`: assets públicos
- `scripts/update_reels.py`: refresca datos desde Instagram
- `scripts/update_streams.py`: refresca datos desde YouTube
- `scripts/import_bandsintown_events.py`: importa un bloque HTML de Bandsintown a eventos
- `scripts/publish_dist.py`: sincroniza la build estática con la raíz del repo

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

Esto genera `dist/` con Astro y luego copia la salida publicada a la raíz para mantener GitHub Pages funcionando desde `main`.

## Actualizar reels
```bash
python3 scripts/update_reels.py
npm run build:site
```

## Actualizar streams
```bash
python3 scripts/update_streams.py
npm run build:site
```

## Actualizar contenido
```bash
npm run refresh:content
npm run build:site
```

## Actualizar agenda recurrente
```bash
python3 scripts/update_events.py
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
