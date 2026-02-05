# Deploying to Azure (Free Tier) - Standard Method

This guide uses the Azure App Service (F1 Free tier) to host both your game and the real-time communication.

## Prerequisites
1. An Azure Account ([Create one for free](https://azure.microsoft.com/free/)).
2. Your project is pushed to GitHub.

---

## Step 1: Create a Fresh Web App
Since the per-plan quota might have been hit, we recommend starting fresh:
1. Go to the **Azure Portal**.
2. Create a new **Web App**:
   - **Name**: Pick a new unique name (e.g., `ttt-ultra-backend-v2`)
   - **Runtime stack**: `Python 3.12`
   - **Operating System**: `Linux`
   - **Pricing Plan**: Click "Create New" App Service Plan and ensure **Free F1** is selected.
3. Under **Deployment**, leave GitHub Actions **Disabled** for now.
4. Click **Review + Create**, then **Create**.

## Step 2: Configure Settings (Before Deployment)
Once the app is created, go to the resource and set these up:

### A. Environment Variables
1. Go to **Settings** -> **Environment variables**.
2. Under **App settings**, make sure `SCM_DO_BUILD_DURING_DEPLOYMENT` is set to `1` or `true`.
3. Click **Apply**.

### B. General Settings (Crucial!)
1. Go to **Settings** -> **Configuration** (or **General settings**).
2. **Web sockets**: Set this toggle to **On**. (This allows the game to be real-time).
3. **Startup Command**: Paste the following exactly:
   `gunicorn -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT server:socket_app`
4. Click **Save** and click "Continue" to restart the app.

## Step 3: Connect GitHub
1. Go to **Deployment** -> **Deployment Center**.
2. Select **Source**: `GitHub`.
3. Select your repository (`Python-TicTacToe`) and the `main` branch.
4. Choose the **first** Workflow option (let Azure create the file).
5. Click **Save**.

---

## Technical Details
This app uses:
- **FastAPI** to serve the logic.
- **Python-SocketIO** for real-time play.
- **Web Sockets** enabled on Azure to allow persistent connections.
- **F1 Free Plan**: Provides 60 minutes of CPU time daily.
