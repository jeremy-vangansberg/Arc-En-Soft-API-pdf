import pytz
from datetime import datetime
import os
from ftplib import FTP
from fastapi import FastAPI, HTTPException, Query, Request
from starlette.responses import JSONResponse
from tempfile import NamedTemporaryFile
import subprocess
import requests

import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_to_ftp(ftp_host: str, ftp_username: str, ftp_password: str, log_message: str, log_folder: str = "logs"):
    """
    Enregistre un message de log dans un dossier spécifié sur un serveur FTP.
    """
    tz = pytz.timezone('Europe/Paris')
    now = datetime.now(tz)
    log_filename = f"log_{now.strftime('%Y%m%d_%H%M%S')}.txt"
    log_file_path = os.path.join(log_folder, log_filename).replace('\\', '/')
    
    logging.info(f"Tentative de log FTP dans : {log_file_path}")
    
    with NamedTemporaryFile("w", delete=False) as temp_log_file:
        temp_log_file.write(log_message)
        temp_log_path = temp_log_file.name

    try:
        with FTP(ftp_host, ftp_username, ftp_password) as ftp:
            logging.info(f"Connexion établie avec {ftp_host}")
            ftp.cwd('/')  # Assurez-vous d'être à la racine
            if log_folder != '/':
                ensure_ftp_path(ftp, log_folder)
            with open(temp_log_path, 'rb') as file:
                ftp.storbinary(f'STOR {log_file_path}', file)
                logging.info(f"Fichier {log_file_path} téléversé avec succès.")
    except Exception as e:
        logging.error(f"Erreur lors du téléversement du log sur FTP : {e}")
    finally:
        os.remove(temp_log_path)  # Nettoyage du fichier temporaire
        logging.info("Fichier temporaire supprimé.")

def ensure_ftp_path(ftp, path):
    """
    Crée récursivement le chemin sur le serveur FTP si nécessaire.
    """
    path = path.lstrip('/')  # Supprime le slash initial pour éviter les chemins absolus
    directories = path.split('/')
    
    current_path = ''
    for directory in directories:
        if directory:  # Ignore les chaînes vides
            current_path += "/" + directory
            try:
                ftp.cwd(current_path)
                logging.info(f"Navigué vers {current_path}.")
            except Exception:
                ftp.mkd(current_path)  # Crée le dossier s'il n'existe pas
                ftp.cwd(current_path)  # Navigue dans le dossier nouvellement créé
                logging.info(f"Dossier {current_path} créé et navigation vers ce dossier.")

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
        log_message = f"Erreur lors du traitement du fichier : {str(e)}"
        print(log_message)
        # Appel à la fonction log_to_ftp pour enregistrer le message d'erreur sur le serveur FTP
        log_to_ftp(
            ftp_host=ftp_host,
            ftp_username=ftp_username,
            ftp_password=ftp_password,
            log_message=log_message,
            log_folder="/log_folder"  # Assurez-vous d'ajuster ce chemin au dossier de logs souhaité
        )
    finally:
        # Nettoyage des fichiers temporaires
        clean_up_files([docx_path, pdf_path])
