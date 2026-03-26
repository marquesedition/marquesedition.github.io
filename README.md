# Marques Edition

Web oficial de Marques Edition migrada a Astro.

## Estructura
- `src/pages/`: rutas Astro
- `src/components/`: componentes reutilizables
- `src/data/reels.json`: fuente de datos de reels
- `public/`: assets públicos
- `scripts/update_reels.py`: refresca datos desde Instagram
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

El workflow `.github/workflows/update-reels.yml` hace este proceso automáticamente.
