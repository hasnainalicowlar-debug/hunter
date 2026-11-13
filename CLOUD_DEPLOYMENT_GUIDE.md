# 24/7 Cloud Production Deployment Guide
## Pakistan Food Business Intelligence & AI POS Lead Hunter Platform

> [!IMPORTANT]
> Is guide ke mutabiq deploy karne se aapki platform **24 ghante, 7 din (24/7) live** rahegi. Aapka laptop band hone ke bawajood:
> 1. Har raat **02:00 AM PKT** par AI Lead Hunter automatically nayi restaurants aur POS buyer requests doondhe ga.
> 2. Database updates aur CRM leads auto-sync hongi.
> 3. Aapki sales team kahin se bhi phone ya laptop se live link open karke leads access kar sakti hai.

---

## Do (2) Asaan Tareeqay (Choose Any Option)

| Feature | Method 1: Render.com | Method 2: Ubuntu Cloud VPS |
|---|---|---|
| **Setup Time** | 5 Minutes | 10 Minutes |
| **Linux Knowledge Needed** | Zero (No CLI needed) | Basic (Copy/Paste commands) |
| **Cost** | Free Tier available | \$4 - \$5 / month |
| **Custom Domain** | Supported (e.g. `posleads.pk`) | Supported (Full root access) |
| **SSL (HTTPS)** | Automatic Free SSL | Automatic Let's Encrypt |
| **Best For** | Foran live karne ke liye | High performance & custom domain |

---

## Method 1: Deploy on Render.com (Recommended for Quick & Free Setup)

Render.com Python apps ke liye sab se behtareen aur asaan platform hai. Humne already project mein `render.yaml` aur `Procfile` add kar diya hai.

### Steps:
1. **GitHub Repository Banayein:**
   - [GitHub.com](https://github.com) par free account banayein ya login karein.
   - Ek nayi private ya public repository banayein (e.g., `pakistan-food-pos-intel`).
   - Project folder (`c:\Users\Hasnain.DESKTOP-80IKSQ9\Desktop\pos\pakistan_food_pos_intel`) ki files ko GitHub repo mein push karein:
     ```bash
     git init
     git add .
     git commit -m "Production release with 200k database & AI Lead Hunter"
     git branch -M main
     git remote add origin https://github.com/YOUR_USERNAME/pakistan-food-pos-intel.git
     git push -u origin main
     ```

2. **Render.com par Connect Karein:**
   - [Render.com](https://render.com) par ja kar **Sign Up / Log In** karein (GitHub se login karna sab se fast hai).
   - Dashboard mein **New +** button daba kar **Web Service** select karein.
   - Apni GitHub repository (`pakistan-food-pos-intel`) ko select karein.

3. **Service Settings:**
   - **Name:** `pakistan-food-pos`
   - **Region:** `Frankfurt (EU)` ya `Singapore` (Pakistan ke qareeb)
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn api.server:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
   - **Instance Type:** Free ya Starter ($7/mo for 24/7 persistent execution)

4. **Deploy Web Service:**
   - **Create Web Service** par click karein.
   - 2-3 minute mein build complete ho jayegi aur aapko ek live HTTPS link mil jaye ga:
     `https://pakistan-food-pos.onrender.com`

---

## Method 2: Deploy on Ubuntu Cloud VPS (DigitalOcean / Hetzner / Contabo / AWS)

Agar aap apna private server chahte hain jahan custom domain (e.g., `posleads.pk`) lagana ho, to ek \$4/month Ubuntu VPS lein. Humne aapke liye **`deploy_vps.sh`** 1-click automated script bana di hai!

### Steps:
1. **VPS Order Karein:**
   - DigitalOcean ($4/mo Droplet), Hetzner (EUR 3.79/mo), ya AWS Lightsail ($3.50/mo) se **Ubuntu 22.04 LTS ya 24.04 LTS** VPS select karein.
   - Server ka IP address (e.g., `167.99.123.45`) note karein.

2. **Server par SSH Login Karein:**
   - Apne computer ke terminal se connect karein:
     ```bash
     ssh root@YOUR_SERVER_IP
     ```

3. **Project Files Upload Karein:**
   - Apne laptop se project files ya zip file server par transfer karein:
     ```bash
     scp Pakistan_Food_POS_Intelligence_Platform_v2.zip root@YOUR_SERVER_IP:/root/
     ```
   - Server ke andar unzip karein:
     ```bash
     sudo apt install -y unzip
     unzip /root/Pakistan_Food_POS_Intelligence_Platform_v2.zip -d /opt/pakistan_food_pos_intel
     cd /opt/pakistan_food_pos_intel
     ```

4. **1-Click Deployment Script Run Karein:**
   ```bash
   bash deploy_vps.sh
   ```
   *Yeh script automatically:*
   - Nginx install aur configure karegi.
   - Python virtual environment banayegi aur requirements install karegi.
   - **Systemd background service (`foodpos.service`)** banayegi jo 24/7 background mein chalta rahe ga aur server reboot hone par khud restart hoga.
   - Firewall ports open karegi.

5. **Aapki Website LIVE hai!**
   - Script ke end par aapko message aayega:
     `>>> SUCCESS! Platform is now LIVE online 24/7 at http://YOUR_SERVER_IP`
   - Agar aap apna custom domain lagana chahein to sirf Certbot chala dein:
     ```bash
     sudo apt install -y certbot python3-certbot-nginx
     sudo certbot --nginx -d yourdomain.com
     ```
     Yeh free SSL padlock (`https://yourdomain.com`) activate kar dega.

---

## 24/7 Autonomous Lead Hunter Verification
Server par deployment ke baad:
- AI Lead Hunter daemon background mein 24/7 chalta rahe ga.
- Har roz **02:00 AM PKT** par research job auto-run hogi.
- Nayi businesses discover hongi, contact verify honge aur POS buyer radar automatically update hoga.
- Aap kisi bhi waqt web dashboard ke top header mein **Run Hunter Now** daba kar on-demand live run bhi trigger kar sakte hain.
