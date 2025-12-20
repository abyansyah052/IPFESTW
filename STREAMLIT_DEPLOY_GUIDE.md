# 🚀 Deploy ke Streamlit Community Cloud

## ✅ GitHub Repository
**Repository URL**: https://github.com/abyansyah052/IPFESTW

Code sudah berhasil di-push! 🎉

---

## 📋 Step-by-Step Deployment

### 1️⃣ Buka Streamlit Community Cloud

1. **Kunjungi**: https://share.streamlit.io/
2. **Sign in** dengan akun GitHub kamu (abyansyah052)
3. Klik tombol **"New app"** (biru, di pojok kanan atas)

![Streamlit Dashboard](https://docs.streamlit.io/images/streamlit-community-cloud/deploy-empty-image.png)

---

### 2️⃣ Configure Deployment

Di halaman deployment, isi form:

#### **Repository**
```
abyansyah052/IPFESTW
```

#### **Branch**
```
main
```

#### **Main file path**
```
app.py
```

#### **App URL** (optional - custom subdomain)
```
scenario-calc
```
Atau biarkan kosong untuk auto-generated URL

---

### 3️⃣ Add Secrets (PENTING!)

Sebelum deploy, klik **"Advanced settings"** → **"Secrets"**

Copy-paste konfigurasi database Supabase kamu:

```toml
# Database Configuration untuk Supabase Session Pooler
DB_HOST = "aws-1-ap-south-1.pooler.supabase.com"
DB_PORT = "6543"
DB_NAME = "postgres"
DB_USER = "postgres.swkgxntzamifnmktyabo"
DB_PASSWORD = "Abyansyah123"
```

**⚠️ PENTING - TROUBLESHOOTING DATABASE CONNECTION**:

### Jika error "OperationalError", coba opsi ini:

#### Opsi A: Transaction Mode (Port 6543) - RECOMMENDED
```toml
DB_HOST = "aws-1-ap-south-1.pooler.supabase.com"
DB_PORT = "6543"
DB_NAME = "postgres"
DB_USER = "postgres.swkgxntzamifnmktyabo"
DB_PASSWORD = "Abyansyah123"
```

#### Opsi B: Session Mode (Port 5432)
```toml
DB_HOST = "aws-1-ap-south-1.pooler.supabase.com"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres.swkgxntzamifnmktyabo"
DB_PASSWORD = "Abyansyah123"
```

#### Opsi C: Direct Connection (Tanpa Pooler)
```toml
DB_HOST = "db.swkgxntzamifnmktyabo.supabase.co"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "Abyansyah123"
```

**📝 Cara Cek Connection String Lengkap**:
1. Buka Supabase Dashboard → Settings → Database
2. Scroll ke "Connection String" section
3. Pilih "URI" atau "Connection pooling"
4. Copy connection string dan extract Host, Port, User

**Cara cek credentials Supabase**:
1. Login ke https://supabase.com
2. Pilih project kamu
3. Settings → Database
4. Connection string → Scroll ke "Connection pooling"
5. Copy Host, Port, User, Password

---

### 4️⃣ Deploy!

1. Klik tombol **"Deploy!"** (biru besar)
2. Tunggu ~2-3 menit
3. Status akan berubah dari:
   - 🟡 **Building** → 🟢 **Running**

---

## 🌐 Access Your App

Setelah deploy selesai, app kamu akan live di:

```
https://scenario-calc-abyansyah052.streamlit.app
```

Atau URL yang di-generate oleh Streamlit.

---

## 🔧 Update App (Jika Ada Perubahan)

Setiap kali kamu push ke GitHub, app akan auto-redeploy:

```bash
cd /Users/macos/Documents/UNIV/SM5/IPFEST/ScenarioCalc

# Make changes to code...

git add .
git commit -m "Update: deskripsi perubahan"
git push origin main

# Streamlit akan auto-deploy dalam ~2 menit
```

---

## 📱 Streamlit Dashboard Features

Di dashboard https://share.streamlit.io/, kamu bisa:

1. **👁️ View app**: Lihat app yang sedang running
2. **📊 Analytics**: Lihat visitor stats
3. **🔄 Reboot**: Restart app jika error
4. **⚙️ Settings**: 
   - Edit secrets (database credentials)
   - Change app URL
   - Manage access (public/private)
5. **📝 Logs**: Debug errors dan monitoring
6. **🗑️ Delete**: Hapus app

---

## 🐛 Troubleshooting

### App gagal start?

1. **Check Logs**:
   - Dashboard → App → "Manage app" → "Logs"
   - Lihat error message

2. **Common Issues**:
   - ❌ Database connection error → Check secrets
   - ❌ Module not found → Check requirements.txt
   - ❌ Port binding error → Streamlit handles automatically

### Database connection error?

**Error**: `sqlalchemy.exc.OperationalError`

**Solusi Step-by-Step**:

1. **Cek Format Secrets** - HARUS ada tanda kutip:
   ```toml
   # ✅ BENAR (dengan quotes)
   DB_HOST = "aws-1-ap-south-1.pooler.supabase.com"
   DB_PORT = "6543"
   
   # ❌ SALAH (tanpa quotes)
   DB_HOST = aws-1-ap-south-1.pooler.supabase.com
   ```

2. **Coba Ganti Port**:
   - Coba port `6543` (Transaction Mode) - RECOMMENDED
   - Atau port `5432` (Session Mode)
   
3. **Test Direct Connection** (tanpa pooler):
   ```toml
   DB_HOST = "db.swkgxntzamifnmktyabo.supabase.co"
   DB_PORT = "5432"
   DB_USER = "postgres"
   DB_PASSWORD = "Abyansyah123"
   ```

4. **Cek IP Whitelist di Supabase**:
   - Dashboard → Settings → Database
   - Scroll ke "Connection Pooling"
   - Pastikan "Allow connections from any IP" enabled

5. **Restart App**:
   - Streamlit Dashboard → Reboot app
   - Tunggu 1-2 menit

**Cara Test yang Mana yang Benar**:
- Coba Opsi A dulu (port 6543)
- Jika masih error, coba Opsi B (port 5432)
- Jika masih error, coba Opsi C (direct connection)
- Save secrets → Reboot app setiap kali ganti

Verify secrets di dashboard:
```
Settings → Secrets → Edit
```

Pastikan format correct (TOML format dengan quotes):
```toml
DB_HOST = "your-host"
DB_PASSWORD = "your-password"
```

### App slow atau timeout?

Streamlit Community Cloud limits:
- **Resources**: 1 GB RAM
- **CPU**: Shared
- **Sleep**: Apps sleep after 7 days inactivity

Solusi: Upgrade ke paid plan atau optimize code.

---

## 📊 Monitoring App

### Check App Health
```
Dashboard → Your App → Status indicator
```

- 🟢 **Running**: App healthy
- 🟡 **Starting**: App booting up
- 🔴 **Error**: Check logs
- ⚪ **Sleeping**: Wake up on visit

### View Logs (Real-time)
```
Dashboard → Manage app → Logs
```

---

## 🔒 Security Best Practices

### ✅ Already Implemented:
- Database credentials in secrets (not in code)
- `.env` in `.gitignore`
- XSRF protection enabled
- No hardcoded passwords

### 🔐 Additional (Optional):
- **Private App**: Settings → "Make app private"
- **Password Protect**: Use `streamlit-authenticator`
- **API Keys**: Add to secrets if needed

---

## 📞 Get Help

### Streamlit Community
- **Forum**: https://discuss.streamlit.io/
- **Docs**: https://docs.streamlit.io/
- **GitHub**: https://github.com/streamlit/streamlit

### Your App Issues
- **GitHub Issues**: https://github.com/abyansyah052/IPFESTW/issues
- **Email Support**: Streamlit support (for paid plans)

---

## 🎉 Your App is Live!

**Repository**: https://github.com/abyansyah052/IPFESTW  
**Deployment**: Streamlit Community Cloud  
**Status**: ✅ Ready to Deploy

### Next Steps:
1. ✅ Code pushed to GitHub
2. ⏳ Deploy to Streamlit (follow steps above)
3. 🚀 Share app URL with users!

**Estimated time**: 5 minutes from start to live app

---

## 📸 Screenshots

### Dashboard Example:
```
┌─────────────────────────────────────┐
│  Streamlit Community Cloud          │
├─────────────────────────────────────┤
│  My apps                            │
│  ┌─────────────────────────────┐   │
│  │  📊 Financial Scenario       │   │
│  │  🟢 Running                  │   │
│  │  🌐 scenario-calc.streamlit  │   │
│  │  [Manage] [Analytics] [...]  │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

**Ready to deploy!** 🚀

Follow steps 1-4 above to make your app live in minutes!
