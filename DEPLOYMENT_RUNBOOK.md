# Deployment Runbook

This runbook is designed for a fast and safe go-live for UEL CDT students.

## 1) Render Deployment Walkthrough (Click-by-click)

### Prerequisites
- GitHub repository contains latest project updates
- Render account with access to create a Web Service
- Repository includes render.yaml and requirements.txt

### Steps in Render UI
1. Open Render dashboard.
2. Click New +.
3. Click Blueprint.
4. Connect GitHub account (if not already connected).
5. Select this repository.
6. Render detects render.yaml automatically.
7. Review the service settings shown from the blueprint:
   - Service type: Web Service
   - Environment: Python
   - Build command: pip install -r requirements.txt
   - Start command: streamlit run src/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
8. Choose plan (Starter is enough for classroom pilot).
9. Click Apply and wait for build and deploy.
10. Open the generated URL from Render.

### Post-deploy checks on Render
1. Open Logs and confirm startup line includes Streamlit listening on 0.0.0.0 and the assigned PORT.
2. Open the public URL and verify homepage loads.
3. Run one sample analysis in the app and confirm result panels render.
4. Keep the Render URL in your session notes for students.

## 2) Azure Container Apps Deployment (Using Dockerfile)

### Prerequisites
- Azure subscription
- Azure CLI installed and signed in
- Docker installed locally
- Resource Group and Container Registry permissions

### Variables to set first (PowerShell)
~~~powershell
$LOCATION = "uksouth"
$RESOURCE_GROUP = "rg-prompts-cdt"
$ACR_NAME = "acrcdtprompts001"
$ENV_NAME = "acae-prompts-cdt"
$APP_NAME = "aca-prompts-collection"
$IMAGE_NAME = "prompts-collection"
$IMAGE_TAG = "v1"
~~~

### Step A: Create Azure resources
~~~powershell
az group create --name $RESOURCE_GROUP --location $LOCATION
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
az containerapp env create --name $ENV_NAME --resource-group $RESOURCE_GROUP --location $LOCATION
~~~

### Step B: Build and push image to ACR
~~~powershell
az acr login --name $ACR_NAME
docker build -t "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$IMAGE_TAG" .
docker push "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$IMAGE_TAG"
~~~

### Step C: Deploy Container App
~~~powershell
az containerapp create `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --environment $ENV_NAME `
  --image "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$IMAGE_TAG" `
  --target-port 8501 `
  --ingress external `
  --registry-server "$ACR_NAME.azurecr.io" `
  --query properties.configuration.ingress.fqdn
~~~

### Step D: Assign pull permission from ACR to Container App Managed Identity
~~~powershell
$APP_ID = az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query identity.principalId -o tsv
$ACR_ID = az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query id -o tsv
az role assignment create --assignee-object-id $APP_ID --assignee-principal-type ServicePrincipal --role AcrPull --scope $ACR_ID
~~~

### Step E: Update app revision to use managed identity pull
~~~powershell
az containerapp update --name $APP_NAME --resource-group $RESOURCE_GROUP --set configuration.registries[0].identity=system
~~~

### Step F: Get live URL
~~~powershell
$FQDN = az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv
"https://$FQDN"
~~~

### Health checks after Azure deploy
1. Open the URL and confirm app loads.
2. Test one full prompt analysis.
3. Review Container App logs for startup errors.

## 3) Classroom-Ready Launch Checklist

### T-7 to T-3 days
1. Confirm chosen primary platform (Render or Azure).
2. Confirm secondary fallback platform is also deployed and tested.
3. Verify all prompt categories are visible in app sidebar.
4. Confirm no secrets or local-only files are required.
5. Run 10 sample prompts across different categories and record response quality.

### T-2 to T-1 days
1. Load test with at least 10 to 20 concurrent users (light classroom simulation).
2. Confirm cold start time under acceptable threshold for class flow.
3. Share final URL and backup URL with teaching staff.
4. Prepare one-page student quick start (how to use, expected output, troubleshooting).

### Launch day
1. Open app 30 minutes before session start.
2. Verify URL from campus network and one mobile hotspot.
3. Keep logs page open during first 20 minutes.
4. Use predefined sample prompt if students report confusion.
5. Announce backup URL if latency or outages appear.

## 4) Rollback Plan

### Render rollback
1. Open Render service.
2. Go to Events or Deploys.
3. Select last known good deploy.
4. Use rollback or redeploy previous commit.
5. Confirm URL health before notifying class.

### Azure rollback
1. In Container Apps, switch traffic to previous healthy revision.
2. Keep failed revision at 0 percent traffic.
3. If needed, redeploy previous image tag.
4. Validate URL health after revision switch.

## 5) Contingency Plan (If primary deployment fails)

### Priority order
1. Primary hosted URL (Render or Azure)
2. Secondary hosted URL (other platform)
3. Instructor local fallback run from laptop on stable hotspot

### Local fallback run command
~~~powershell
& "c:/Users/Gabriele/OneDrive - University of East London/Documents/Github/05_Dev_Tools_Automation/Prompts-Collection/.venv/Scripts/python.exe" main.py
~~~

### Communication template for students
- If there is a short outage, ask students to continue drafting prompts offline for 5 to 10 minutes.
- Share backup URL in Teams or classroom chat.
- Resume live analysis once service stabilizes.

## 6) Ownership During Session
- One person monitors app logs.
- One person supports student usage questions.
- One person is ready to trigger rollback.

This separation avoids delayed response during the first 15 minutes of class.
