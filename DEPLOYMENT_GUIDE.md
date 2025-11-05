# Deployment Guide

## Step 1: Push to GitHub

### 1.1 Add all files to git
```bash
git add .
git commit -m "Initial commit: StockSense AI Platform"
```

### 1.2 Create GitHub repository
1. Go to https://github.com/new
2. Create a new repository named "stocksense"
3. Don't initialize with README (we already have one)

### 1.3 Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/stocksense.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy Frontend to GitHub Pages

### Option A: Using GitHub Settings (Recommended)
1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under **Source**, select:
   - Branch: `main`
   - Folder: `/frontend` (if available) or `/root`
4. Click **Save**
5. Your site will be live at: `https://YOUR_USERNAME.github.io/stocksense/`

### Option B: Using gh-pages branch
```bash
# Install gh-pages (if needed)
npm install -g gh-pages

# Deploy frontend folder
gh-pages -d frontend -b gh-pages
```

Then in GitHub Settings → Pages, select `gh-pages` branch.

## Step 3: Deploy Backend to Render

### 3.1 Sign Up
1. Go to https://render.com
2. Sign up with GitHub
3. Authorize Render to access your repositories

### 3.2 Create Backend Web Service
1. Click **New +** → **Web Service**
2. Connect your `stocksense` repository
3. Configure:
   - **Name**: `stocksense-backend`
   - **Environment**: `Node`
   - **Build Command**: `cd backend && npm install`
   - **Start Command**: `cd backend && npm start`
   - **Plan**: Free (or choose your plan)

### 3.3 Add Environment Variables
Click **Advanced** → **Add Environment Variable**:
- `MONGODB_URI`: Your MongoDB connection string (use MongoDB Atlas)
- `JWT_SECRET`: Random secret key (generate secure one)
- `ALPHA_VANTAGE_API_KEY`: Your Alpha Vantage API key
- `NODE_ENV`: `production`
- `PORT`: `5000` (Render will override this)

### 3.4 Deploy
Click **Create Web Service** - Render will automatically deploy!

## Step 4: Deploy Analytics to Render

### 4.1 Create Analytics Web Service
1. Click **New +** → **Web Service**
2. Select your `stocksense` repository again
3. Configure:
   - **Name**: `stocksense-analytics`
   - **Environment**: `Python 3`
   - **Build Command**: `cd analytics && pip install -r requirements.txt`
   - **Start Command**: `cd analytics && python app.py`
   - **Plan**: Free

### 4.2 Add Environment Variables
- `FLASK_ENV`: `production`
- `PORT`: `8000`

### 4.3 Deploy
Click **Create Web Service**

## Step 5: MongoDB Setup (MongoDB Atlas)

### 5.1 Create Cluster
1. Go to https://www.mongodb.com/cloud/atlas
2. Sign up / Log in
3. Create a **Free Cluster**
4. Choose your cloud provider and region

### 5.2 Configure Access
1. **Database Access**: Create a database user with password
2. **Network Access**: Add `0.0.0.0/0` to allow connections from anywhere

### 5.3 Get Connection String
1. Click **Connect** on your cluster
2. Choose **Connect your application**
3. Copy the connection string
4. Replace `<password>` with your database user password
5. Add this to your Render backend environment variables as `MONGODB_URI`

## Step 6: Update Frontend API URLs

After deployment, update the API endpoints in your frontend:

**File**: `frontend/js/config.js` (or wherever API URLs are defined)

```javascript
const API_CONFIG = {
  BACKEND_URL: 'https://stocksense-backend.onrender.com',
  ANALYTICS_URL: 'https://stocksense-analytics.onrender.com'
};
```

Then commit and push:
```bash
git add .
git commit -m "Update API URLs for production"
git push
```

## Step 7: Verify Deployment

### Backend
Visit: `https://stocksense-backend.onrender.com/health`

### Analytics
Visit: `https://stocksense-analytics.onrender.com/health`

### Frontend
Visit: `https://YOUR_USERNAME.github.io/stocksense/`

## Troubleshooting

### Backend Issues
- Check Render logs: Dashboard → Your Service → Logs
- Verify environment variables are set correctly
- Ensure MongoDB connection string is correct

### Analytics Issues
- Check if all Python packages installed correctly
- Verify PORT environment variable
- Check Python version compatibility

### Frontend Issues
- Clear browser cache
- Check browser console for API errors
- Verify API URLs are correct
- Check CORS settings on backend

## Free Tier Limitations

### Render Free Tier
- Services spin down after 15 minutes of inactivity
- 750 hours per month
- First request after spin-down takes ~30 seconds

### MongoDB Atlas Free Tier
- 512 MB storage
- Shared CPU
- Limited to one cluster

## Custom Domain (Optional)

### For GitHub Pages
1. Buy a domain (Namecheap, GoDaddy, etc.)
2. Add CNAME file to frontend: `www.yourdomain.com`
3. Configure DNS records
4. In GitHub Settings → Pages, add custom domain

### For Render
1. In Render Dashboard → Service → Settings → Custom Domain
2. Add your domain
3. Configure DNS as instructed by Render

## Continuous Deployment

Both GitHub Pages and Render automatically deploy when you push to your main branch!

```bash
# Make changes
git add .
git commit -m "Your changes"
git push
```

GitHub Pages and Render will automatically update!

## Cost Estimate

- **GitHub Pages**: Free
- **Render (Free Tier)**: Free for 2 services
- **MongoDB Atlas (Free)**: Free up to 512MB
- **Total**: $0/month (Free tier)

For production with better performance:
- **Render**: $7/month per service
- **MongoDB Atlas**: $9+/month
- **Domain**: $10-15/year

## Support

If you encounter issues:
1. Check the logs in Render dashboard
2. Review MongoDB Atlas monitoring
3. Check browser console for frontend errors
4. Verify all environment variables are set

Good luck with your deployment! 🚀
