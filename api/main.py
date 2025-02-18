from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi import BackgroundTasks
from typing import List
from utils import *
from celery_worker import celery_app

app = FastAPI()

# Liste des adresses IP autorisées, '*' permet l'accès à toutes les IP
ALLOWED_IPS = ["*"]

@app.middleware("http")
async def ip_filter_middleware(request: Request, call_next):
    # Si '*' est dans ALLOWED_IPS, on autorise toutes les IP
    if "*" in ALLOWED_IPS:
        response = await call_next(request)
        return response
    
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    client_ip = x_forwarded_for.split(",")[0] if x_forwarded_for else request.client.host

    if client_ip not in ALLOWED_IPS:
        return JSONResponse(status_code=403, content={"detail": f"Accès non autorisé. ip: {client_ip}"})

    response = await call_next(request)
    return response

@app.get("/convert/")
async def convert_endpoint(docx_url: str = Query(...)):
    try:
        docx_path = download_docx_file(docx_url)
        pdf_path = convert_docx_to_pdf(docx_path)
        return FileResponse(pdf_path, media_type='application/pdf', filename=os.path.basename(pdf_path))
    finally:
        clean_up_files([docx_path, pdf_path])

@app.get("/convert-store/")
async def convert_store_background(
    docx_url: str = Query('https%253A%252F%252Fcapcertification.com%252Fwp-content%252Fuploads%252Faudit%252F2021%252F11361%252F11361-Contrat-CAPCERT-20240328-174118.docx'), 
    output_path: str = Query('test/exemple.pdf'),
    ftp_host : str = Query('ftp.hefa8773.odns.fr')):
    # Envoie la tâche à Celery pour une exécution en arrière-plan
    # et passe toutes les informations nécessaires, y compris les paramètres FTP
    task = celery_app.send_task(
        "tasks.convert_and_upload_task", 
        args=[
            docx_url, 
            output_path, 
            ftp_host, 
            os.getenv("FTP_USERNAME"), 
            os.getenv("FTP_PASSWORD")
        ]
    )
    
    # Renvoie immédiatement une réponse indiquant que le processus a été initié
    return {"message": "Le processus de conversion et de téléversement a été initié en arrière-plan.", "task_id": task.id}



