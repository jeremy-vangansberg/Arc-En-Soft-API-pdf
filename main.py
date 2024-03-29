from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
import subprocess
import requests
from tempfile import NamedTemporaryFile
import os

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
        return FileResponse(pdf_path, media_type='application/pdf', filename="converted.pdf")
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error downloading the file: {e}")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail="Error converting the file.")
    finally:
        # Nettoie le fichier temporaire .docx
        if docx_path and os.path.exists(docx_path):
            os.remove(docx_path)
        # Ici, on ne supprime pas le PDF dans finally pour permettre son téléchargement



# @app.get("/convert/")
# async def convert_docx_to_pdf(docx_url: str = Query(...)):
#     # Votre logique existante pour télécharger et convertir le fichier...
    
#     # Chemin du fichier PDF de sortie (assurez-vous que ce soit le bon chemin)
#     pdf_path = "chemin/vers/votre/fichier.pdf"

#     # Paramètres du serveur FTP
#     ftp_host = "adresse_du_serveur_ftp"
#     ftp_username = "votre_nom_d'utilisateur"
#     ftp_password = "votre_mot_de_passe"
#     ftp_directory = "répertoire_sur_ftp"

#     # Téléverse le fichier sur le serveur FTP
#     upload_file_ftp(pdf_path, ftp_host, ftp_username, ftp_password, ftp_directory)

#     # Retourne la réponse (ou ajustez selon vos besoins)
#     return {"message": "Fichier converti et téléversé avec succès."}
