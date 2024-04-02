from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
import subprocess
import requests
from tempfile import NamedTemporaryFile
from ftplib import FTP
import os

from fastapi import BackgroundTasks

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



app = FastAPI()

@app.get("/convert/")
async def convert_endpoint(docx_url: str = Query(...)):
    try:
        docx_path = download_docx_file(docx_url)
        pdf_path = convert_docx_to_pdf(docx_path)
        return FileResponse(pdf_path, media_type='application/pdf', filename=os.path.basename(pdf_path))
    finally:
        clean_up_files([docx_path, pdf_path])

@app.get("/convert-store/")
async def convert_store(background_tasks: BackgroundTasks, docx_url: str = Query(...), output_path: str = Query(...)):
    try:
        docx_path = download_docx_file(docx_url)
        pdf_path = convert_docx_to_pdf(docx_path)
        # Ajouter une tâche en arrière-plan pour le téléversement sans attendre sa complétion
        background_tasks.add_task(upload_file_ftp, pdf_path, os.getenv("FTP_HOST"), os.getenv("FTP_USERNAME"), os.getenv("FTP_PASSWORD"), output_path)
        return {"message": "Conversion initiée. Le fichier sera téléversé sur le FTP."}
    finally:
        clean_up_files([docx_path, pdf_path])
