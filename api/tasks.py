# tasks.py
from celery import shared_task
from utils import process_docx_to_pdf_and_upload


@shared_task
def convert_and_upload_task(docx_url: str, output_path: str, ftp_host: str, ftp_username: str, ftp_password: str):
    """
    Une tâche pour télécharger un fichier DOCX, le convertir en PDF, et l'uploader sur FTP.
    """
    # Appelle votre fonction existante pour réaliser ces étapes.
    # Assurez-vous que votre fonction gère correctement les exceptions.
    process_docx_to_pdf_and_upload(
        docx_url,
        output_path, 
        ftp_host, 
        ftp_username, 
        ftp_password
        )
