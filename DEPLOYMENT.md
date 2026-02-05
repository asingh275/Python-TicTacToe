# Deploying to Azure (Free Tier)

This guide will help you deploy the Tic-Tac-Toe Ultra project to Azure using only free services.

## Prerequisites
1. An Azure Account ([Create one for free](https://azure.microsoft.com/free/)).
2. Azure CLI installed (type `az` in terminal to check).

---

## Step 1: Create Azure App Service (Backend)
1. Go to the **Azure Portal**.
2. Create a new **Web App**:
   - **Name**: `ttt-ultra-backend` (or similar)
   - **Runtime stack**: `Python 3.12`
   - **Operating System**: `Linux`
   - **Pricing Plan**: `Free F1` (This is very important!)
3. Under **Deployment**, leave GitHub Actions **Disabled** for now (Azure often blocks this during the initial creation of Free Linux plans).
4. Click **Review + Create**, then **Create**.

## Step 1.5: Connect GitHub (After App is Created)
1. Go to your new **Web App** resource in the portal.
2. Go to **Deployment Center** (in the left sidebar).
3. Select **Source**: `GitHub`.
4. Sign in and select your repository (`Python-TicTacToe`) and the `main` branch.
5. Click **Save**. This will automatically trigger a build and deploy your code!

## Step 2: Create Azure Web PubSub for Socket.IO (Real-time)
1. In the Azure Portal, search for **Web PubSub**.
2. Create a new resource:
   - **Pricing Tier**: `Free`
   - **Service Mode**: `Socket.IO`
3. Once created, go to **Keys** and copy the **Connection String**.

## Step 3: Configure environment variables
1. Go back to your **App Service** (ttt-ultra-backend).
2. Go to **Settings** -> **Configuration** -> **Application settings**.
3. Add a new setting:
   - **Name**: `AZURE_WEB_PUBSUB_CONNECTION_STRING`
   - **Value**: (Paste your connection string here)
4. Add another setting:
   - **Name**: `SCM_DO_BUILD_DURING_DEPLOYMENT`
   - **Value**: `true`
5. Set the **Startup Command** (under **Configuration** -> **General Settings**):
   - Command: `gunicorn -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT server:socket_app`
6. Click **Save**.

## Step 4: Add a "Hub" to Web PubSub
1. Go to your **Web PubSub** resource.
2. Go to **Settings** -> **Socket.IO Settings**.
3. Click **Add Hub**:
   - **Hub Name**: `hub1` (or anything)
   - **Event Handler**: Add a URL pointing to your backend: `https://ttt-ultra-backend.azurewebsites.net/socket.io/`
4. This allows the Web PubSub service to talk to your FastAPI code.

---

## Technical Details
This app uses:
- **FastAPI** for logic and static files.
- **Azure App Service (Free Tier)** for hosting.
- **Azure Web PubSub for Socket.IO (Free Tier)** for robust real-time communication.
