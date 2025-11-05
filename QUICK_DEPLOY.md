# Quick Deployment Steps

## ✅ Step 1: GitHub Repository - DONE!
Your code is now live at: https://github.com/Gaurav478-stack/stock_prediction_via_lstm

---

## 📄 Step 2: Deploy Frontend to GitHub Pages

### Method 1: Via GitHub Settings (Easiest)
1. Go to: https://github.com/Gaurav478-stack/stock_prediction_via_lstm/settings/pages
2. Under **Source**, select:
   - Branch: `main`
   - Folder: `/root`
3. Click **Save**
4. Wait 2-3 minutes
5. Your site will be live at: `https://gaurav478-stack.github.io/stock_prediction_via_lstm/frontend/`

### Update Frontend API Configuration
After deploying backend (Step 3), update `frontend/js/config.js`:
```javascript
const API_CONFIG = {
    BACKEND_URL: 'https://your-backend-url.onrender.com',
    ANALYTICS_URL: 'https://your-analytics-url.onrender.com'
};
```

---

## 🚀 Step 3: Deploy Backend to Render

### 3.1 Sign Up & Connect
1. Go to: https://render.com/signup
2. Sign up with GitHub
3. Authorize Render to access your repositories

### 3.2 Create Backend Service
1. Click **New +** → **Web Service**
2. Find and select `stock_prediction_via_lstm`
3. Fill in details:
   - **Name**: `stocksense-backend`
   - **Environment**: `Node`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Build Command**: `cd backend && npm install`
   - **Start Command**: `cd backend && npm start`
   - **Plan**: Free

### 3.3 Environment Variables (IMPORTANT!)
Click **Advanced** → **Add Environment Variable**:

```
MONGODB_URI = mongodb+srv://your-connection-string
JWT_SECRET = your-random-secret-key-here
ALPHA_VANTAGE_API_KEY = your-alpha-vantage-key
NODE_ENV = production
PORT = 5000
```

**Get MongoDB URI:**
- Go to https://www.mongodb.com/cloud/atlas
- Create free cluster
- Get connection string from "Connect" → "Connect your application"

**Get Alpha Vantage API Key:**
- Go to https://www.alphavantage.co/support/#api-key
- Sign up for free API key

### 3.4 Deploy
Click **Create Web Service** - deployment takes 5-10 minutes

Your backend URL will be: `https://stocksense-backend.onrender.com`

---

## 🐍 Step 4: Deploy Analytics to Render

### 4.1 Create Analytics Service
1. Click **New +** → **Web Service**
2. Select `stock_prediction_via_lstm` again
3. Fill in details:
   - **Name**: `stocksense-analytics`
   - **Environment**: `Python 3`
   - **Region**: Same as backend
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Build Command**: `cd analytics && pip install -r requirements.txt`
   - **Start Command**: `cd analytics && python app.py`
   - **Plan**: Free

### 4.2 Environment Variables
```
FLASK_ENV = production
PORT = 8000
```

### 4.3 Deploy
Click **Create Web Service**

Your analytics URL will be: `https://stocksense-analytics.onrender.com`

---

## 🔄 Step 5: Update Frontend with Backend URLs

1. Edit `frontend/js/config.js` with your Render URLs
2. Commit and push:
```bash
git add frontend/js/config.js
git commit -m "Update API URLs for production"
git push
```

GitHub Pages will automatically update in 1-2 minutes!

---

## 🧪 Step 6: Test Your Deployment

### Test Backend
```bash
curl https://stocksense-backend.onrender.com/health
```

### Test Analytics
```bash
curl https://stocksense-analytics.onrender.com/health
```

### Test Frontend
Open: `https://gaurav478-stack.github.io/stock_prediction_via_lstm/frontend/`

---

## ⚠️ Important Notes

### Free Tier Limitations
- **Render**: Services sleep after 15 minutes of inactivity
- **First Request**: Takes ~30 seconds to wake up
- **MongoDB Atlas**: 512 MB storage limit

### CORS Configuration
Make sure your backend allows requests from your GitHub Pages domain.

In `backend/server.js`, ensure CORS is configured:
```javascript
app.use(cors({
    origin: 'https://gaurav478-stack.github.io'
}));
```

---

## 📱 Next Steps

1. ✅ Test all features on the deployed site
2. ✅ Monitor Render logs for any errors
3. ✅ Set up MongoDB Atlas monitoring
4. ✅ Add custom domain (optional)
5. ✅ Enable HTTPS (automatic on Render & GitHub Pages)

---

## 🆘 Troubleshooting

**Backend not responding?**
- Check Render logs in dashboard
- Verify environment variables
- Confirm MongoDB connection string

**Frontend API errors?**
- Check browser console (F12)
- Verify API URLs in config.js
- Check CORS settings

**Analytics failing?**
- Check Python version (3.8+ required)
- Verify all packages installed
- Check Render build logs

---

## 💰 Upgrade Options (Optional)

**For Production:**
- Render: $7/month per service (no sleep, more resources)
- MongoDB: $9/month (better performance)
- Custom Domain: $10-15/year

**Current Cost: $0/month** ✨

---

## 📞 Support

- Render Docs: https://render.com/docs
- GitHub Pages: https://docs.github.com/pages
- MongoDB Atlas: https://docs.atlas.mongodb.com/

Good luck! Your StockSense platform is ready to go live! 🚀📈
