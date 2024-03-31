from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
import subprocess
import requests
from tempfile import NamedTemporaryFile
import os
from ftplib import FTP

def upload_file_ftp(file_path, ftp_host, ftp_username, ftp_password, ftp_directory, output_name):
    with FTP(ftp_host, ftp_username, ftp_password) as ftp:
        ftp.cwd(ftp_directory)
        with open(file_path, 'rb') as file:
            # Utilisez output_name pour le nom du fichier sur le serveur FTP
            ftp.storbinary(f'STOR {os.path.basename(output_name)}', file)



app = FastAPI()

@app.get("/convert/")
async def convert_docx_to_pdf(docx_url: str = Query(..., description="The URL of the .docx file to be converted")):
    docx_path = None  # Initialise à None pour être accessible dans le bloc finally
    pdf_path = None   # Initialise à None pour être accessible dans le bloc finally
    
    try:
        # Télécharge le fichier .docx depuis l'URL fournie
        response = requests.get(docx_url)
        response.raise_for_status()

        # Crée un fichier temporaire pour le document .docx téléchargé
        with NamedTemporaryFile(delete=False, suffix=".docx") as temp_docx:
            temp_docx.write(response.content)
            docx_path = temp_docx.name  # Chemin du fichier temporaire .docx

        # Chemin prévu du fichier PDF de sortie
        pdf_path = docx_path.replace(".docx", ".pdf")

        print(pdf_path)

        # Commande LibreOffice pour la conversion, avec paramètres pour la qualité des images
        cmd = [
            "libreoffice", "--headless", "--convert-to", 
            "pdf:writer_pdf_Export:UseLosslessCompression=true,MaxImageResolution=300",
            "--outdir", os.path.dirname(pdf_path), docx_path
        ]
 
        # Exécute la commande de conversion
        subprocess.run(cmd, check=True)

        # Vérifie si le fichier PDF a été créé
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="Failed to create PDF file.")

        # Retourne le fichier PDF généré
        return FileResponse(pdf_path, media_type='application/pdf', filename="converted.pdf", headers={"Content-Disposition": "attachment; filename=converted.pdf"})
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error downloading the file: {e}")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail="Error converting the file.")
    finally:
        # Nettoie le fichier temporaire .docx
        if docx_path and os.path.exists(docx_path):
            os.remove(docx_path)
        # Ici, on ne supprime pas le PDF dans finally pour permettre son téléchargement

@app.get("/convert-store/")
async def convert_store(
    docx_url: str = Query(..., description="The URL of the .docx file to be converted"), 
    output_name: str = Query("converted.pdf", description="The desired output PDF file name"),
    ftp_directory = str = Query("pdf", description="The desired output folder")):
    docx_path = None
    pdf_path = None
    try:
        # Télécharge le fichier .docx depuis l'URL fournie
        response = requests.get(docx_url)
        response.raise_for_status()

        with NamedTemporaryFile(delete=False, suffix=".docx") as temp_docx:
            temp_docx.write(response.content)
            docx_path = temp_docx.name


        if not output_name.lower().endswith('.pdf'):
            output_name += '.pdf'

        pdf_path = docx_path.replace(".docx", ".pdf")

        cmd = ["libreoffice", "--headless", "--convert-to", "pdf:writer_pdf_Export:UseLosslessCompression=true,MaxImageResolution=300", "--outdir", os.path.dirname(pdf_path), docx_path]
        subprocess.run(cmd, check=True)

        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="Failed to create PDF file.")

        # Lire les informations FTP depuis les variables d'environnement
        ftp_host = os.getenv("FTP_HOST")
        ftp_username = os.getenv("FTP_USERNAME")
        ftp_password = os.getenv("FTP_PASSWORD")
        # ftp_directory = os.getenv("FTP_DIRECTORY")

        # Vérifier que toutes les informations nécessaires sont présentes
        if not all([ftp_host, ftp_username, ftp_password, ftp_directory]):
            raise HTTPException(status_code=500, detail="FTP credentials are not fully configured.")

        # Téléverse le fichier PDF sur le serveur FTP
        upload_file_ftp(pdf_path, ftp_host, ftp_username, ftp_password, ftp_directory, output_name)

        return {"message": "Fichier converti et téléversé avec succès sur FTP."}
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error downloading the file: {e}")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail="Error converting the file.")
    finally:
        # Nettoyage: supprimer les fichiers temporaires
        if docx_path and os.path.exists(docx_path):
            os.remove(docx_path)
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)


