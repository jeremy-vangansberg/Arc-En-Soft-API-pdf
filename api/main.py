from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
import subprocess
import requests
from tempfile import NamedTemporaryFile
from ftplib import FTP
import os
from fastapi import BackgroundTasks
from starlette.responses import JSONResponse
from typing import List

app = FastAPI()

# Liste des adresses IP autorisées
ALLOWED_IPS = ["192.168.1.1", "127.0.0.1", "45.81.84.133", '172.18.0.2']

@app.middleware("http")
async def ip_filter_middleware(request: Request, call_next):
    client_host = request.client.host
    if client_host not in ALLOWED_IPS:
        return JSONResponse(status_code=403, content={"detail": "Accès non autorisé."})
    response = await call_next(request)
    return response

def ensure_ftp_path(ftp, path):
    """Crée récursivement le chemin sur le serveur FTP si nécessaire."""
    path = path.lstrip('/')  # Supprime le slash initial pour éviter les chemins absolus
    directories = path.split('/')
    
    current_path = ''
    for directory in directories:
        if directory:  # Ignore les chaînes vides
            current_path += "/" + directory
            try:
                ftp.cwd(current_path)  # Tente de naviguer dans le dossier
            except Exception:
                ftp.mkd(current_path)  # Crée le dossier s'il n'existe pas
                ftp.cwd(current_path)  # Navigue dans le dossier nouvellement créé

def download_docx_file(url: str) -> str:
    """Télécharge un fichier DOCX depuis une URL et retourne le chemin du fichier temporaire."""
    response = requests.get(url)
    response.raise_for_status()

    with NamedTemporaryFile(delete=False, suffix=".docx") as temp_docx:
        temp_docx.write(response.content)
        return temp_docx.name

def convert_docx_to_pdf(docx_path: str) -> str:
    """Convertit un fichier DOCX en PDF et retourne le chemin du fichier PDF."""
    pdf_path = docx_path.replace(".docx", ".pdf")
    cmd = [
        "libreoffice", "--headless", "--convert-to", 
        "pdf:writer_pdf_Export:UseLosslessCompression=true,MaxImageResolution=300",
        "--outdir", os.path.dirname(pdf_path), docx_path
    ]
    subprocess.run(cmd, check=True)
    if not os.path.exists(pdf_path):
        raise Exception("Failed to create PDF file.")
    return pdf_path

def clean_up_files(file_paths: list):
    """Supprime les fichiers temporaires spécifiés."""
    for path in file_paths:
        if path and os.path.exists(path):
            os.remove(path)

def upload_file_ftp(file_path: str, ftp_host: str, ftp_username: str, ftp_password: str, output_path: str):
    """
    Téléverse un fichier sur un serveur FTP.

    Args:
    - file_path (str): Le chemin local du fichier à téléverser.
    - ftp_host (str): L'hôte du serveur FTP.
    - ftp_username (str): Le nom d'utilisateur pour se connecter au serveur FTP.
    - ftp_password (str): Le mot de passe pour se connecter au serveur FTP.
    - output_path (str): Le chemin complet sur le serveur FTP où le fichier doit être téléversé.

    Cette fonction assure que le chemin de destination existe sur le serveur FTP
    et téléverse le fichier spécifié à cet emplacement.
    """
    with FTP(ftp_host, ftp_username, ftp_password) as ftp:
        # Assure que le chemin du dossier existe sur le serveur FTP
        directory_path, filename = os.path.split(output_path)
        ensure_ftp_path(ftp, directory_path)
        
        # Construit le chemin complet du fichier sur le serveur FTP
        ftp.cwd('/')  # S'assure de partir de la racine
        complete_path = os.path.join(directory_path, filename).lstrip('/')
        
        # Téléverse le fichier
        with open(file_path, 'rb') as file:
            ftp.storbinary(f'STOR {complete_path}', file)



def process_docx_to_pdf_and_upload(docx_url: str, output_path: str, ftp_host: str, ftp_username: str, ftp_password: str):
    """
    Télécharge un fichier DOCX, le convertit en PDF, et téléverse le PDF sur FTP.
    Cette fonction gère l'ensemble du processus en une seule séquence.
    """
    docx_path = None
    pdf_path = None
    try:
        # Téléchargement du fichier DOCX
        docx_path = download_docx_file(docx_url)
        
        # Conversion en PDF
        pdf_path = convert_docx_to_pdf(docx_path)
        
        # Téléversement sur FTP
        upload_file_ftp(pdf_path, ftp_host, ftp_username, ftp_password, output_path)
        
    except Exception as e:
        print(f"Erreur lors du traitement du fichier : {e}")
    finally:
        # Nettoyage des fichiers temporaires
        clean_up_files([docx_path, pdf_path])




@app.get("/convert/")
async def convert_endpoint(docx_url: str = Query(...)):
    try:
        docx_path = download_docx_file(docx_url)
        pdf_path = convert_docx_to_pdf(docx_path)
        return FileResponse(pdf_path, media_type='application/pdf', filename=os.path.basename(pdf_path))
    finally:
        clean_up_files([docx_path, pdf_path])

@app.get("/convert-store/")
async def convert_store_background(background_tasks: BackgroundTasks, docx_url: str = Query(...), output_path: str = Query(...)):
    # Planifie l'exécution de la fonction d'opération complète en arrière-plan
    background_tasks.add_task(
        process_docx_to_pdf_and_upload,
        docx_url,
        output_path,
        os.getenv("FTP_HOST"),
        os.getenv("FTP_USERNAME"),
        os.getenv("FTP_PASSWORD")
    )
    
    # Renvoie immédiatement une réponse indiquant que le processus a été initié
    return {"message": "Le processus de conversion et de téléversement a été initié en arrière-plan."}

