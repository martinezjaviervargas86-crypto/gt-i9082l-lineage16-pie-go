# Cómo compilar LineageOS 16.0 (Android 9.0 Pie Go) sin tener otro PC

Tu Mac Apple Silicon solo tiene ~19 GB libres y el código fuente + compilación de LineageOS 16.0 requiere Linux `x86_64` con ~140 GB de disco y ≥16 GB de RAM. Aquí tienes las 3 mejores opciones para compilarlo directamente desde tu Mac:

---

## Opción 1 (Recomendada — Más rápida y barata): VPS en la nube por horas (~US\$0.10–\$0.30 en total)
Alquilas una máquina Ubuntu `20.04` / `22.04` `x86_64` por **2 horas** (ej. **Hetzner Cloud `CPX51`** 16 vCPU / 32 GB RAM / 240 GB SSD ~€0.05/h, o **Google Cloud / AWS / DigitalOcean** con crédito gratuito), compilas y luego borras la instancia:

```bash
# 1. Desde tu Mac, sube este proyecto al VPS:
rsync -avz --exclude='out/backups' --exclude='kernel/samsung/i9082/src' \
  /Users/javier/.gemini/antigravity/scratch/samsung-i9082l-pie-go/ \
  root@<IP_DEL_VPS>:~/samsung-i9082l-pie-go/

# 2. En el VPS (con Docker instalado):
cd ~/samsung-i9082l-pie-go
docker build -f build/Dockerfile.lineage16 -t lineage16-i9082 .
mkdir -p ~/lineage-16.0
docker run --rm -it -v "$PWD":/workspace -v "$HOME/lineage-16.0":/lineage lineage16-i9082

# 3. Al terminar (~60-90 min), descarga el ZIP flasheable directo a tu Mac:
scp root@<IP_DEL_VPS>:~/lineage-16.0/out/target/product/i9082/lineage-16.0-*.zip \
  /Users/javier/.gemini/antigravity/scratch/samsung-i9082l-pie-go/out/
```

Después borras el VPS y flasheamos el `.zip` por TWRP (`adb sideload`) desde tu Mac.

---

## Opción 2 (Gratis): GitHub Actions (para pruebas de kernel `bootimage` o runner propio)
1. Sube este proyecto a un repositorio en GitHub (sin `out/backups/`).
2. Copia `build/github_actions_build_lineage16.yml` a `.github/workflows/build_lineage16.yml`.
3. En la pestaña **Actions**, ejecuta el workflow:
   - `bootimage` compila y verifica nuestro kernel `3.0.101` parcheado (`binder,hwbinder,vndbinder` + ZRAM LZ4) gratis en ~25 min.
   - `bacon` compila la ROM completa (requiere un runner con ≥120 GB libres; el runner gratuito estándar tiene ~75 GB tras limpieza, por lo que para `bacon` completo es mucho más confiable la Opción 1).

---

## Opción 3 (Local en tu Mac): Disco SSD externo USB (≥200 GB) + VM Linux `x86_64` (UTM / Lima)
Si cuentas con un SSD externo USB-C de al menos 200 GB, puedes crear una VM Ubuntu 20.04 `x86_64` en **UTM** guardando el disco virtual en el SSD externo y ejecutar `build/build_lineage16_i9082_go.sh` dentro de la VM (toma más tiempo por emulación `x86_64` en Apple Silicon, pero es 100% local).
