# DJ Marques Edition 🎧

Open Format DJ based in Madrid 🇪🇸  
Latin vibes + club energy

---

## 🔥 Bookings
📩 Contact: marquesedition.com  

---

## 🎧 About
DJ focused on keeping the dancefloor active all night.  
From reggaeton to club energy.

---

## 🌐 Links
- TikTok: https://www.tiktok.com/@marquesedition
- Instagram: https://www.instagram.com/marquesedition/

---

## 💻 Ver en local (antes de GitHub Pages)
1. En la carpeta del proyecto, ejecuta:

```bash
./dev.sh
```

2. Abre en el navegador:

```text
http://localhost:5500
```

3. Opcional: elegir otro puerto:

```bash
./dev.sh 8080
```

4. Para abrirlo en el movil (misma Wi-Fi), usa la IP local que muestra el script.

Para parar el servidor: `Ctrl + C`.

## 🔄 Actualizar reels
Para regenerar el listado de reels que usa `media-links`:

```bash
python3 scripts/update_reels.py
```

La página muestra 4 reels destacados y deja el resto dentro de “Ver todos los reels”.

En GitHub, el workflow `.github/workflows/update-reels.yml` también puede refrescar `media-links/reels.json` automáticamente.
