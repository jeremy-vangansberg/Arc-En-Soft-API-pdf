from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
import subprocess
import requests
from tempfile import NamedTemporaryFile
import os

app = FastAPI()

def download_file(url):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
            for chunk in response.iter_content(1024):
                temp_file.write(chunk)
            return temp_file.name
    else:
        raise Exception(f"Échec du téléchargement du fichier. Statut HTTP : {response.status_code}")


@app.get("/convert/")
async def convert_docx_to_pdf(docx_url: str = Query(..., description="The URL of the .docx file to be converted")):
    docx_path = None  # Initialise à None pour être accessible dans le bloc finally
    pdf_path = None   # Initialise à None pour être accessible dans le bloc finally
    
    try:
        docx_path = download_file(docx_url)
        print(f"Fichier téléchargé et sauvegardé sous : {docx_path}")

        # Chemin prévu du fichier PDF de sortie
        pdf_path = docx_path.replace(".docx", ".pdf")

        # Commande LibreOffice pour la conversion, avec paramètres pour la qualité des images
        subprocess.run(["pandoc", docx_path, "-o", pdf_path, "--pdf-engine=pdflatex"], check=True)



        # Vérifie si le fichier PDF a été créé
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="Failed to create PDF file.")

        # Retourne le fichier PDF généré
        return FileResponse(pdf_path, media_type='application/pdf', filename="converted.pdf")
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error downloading the file: {e}")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error converting the file: {e.stderr}")
    finally:
        # Nettoie le fichier temporaire .docx
        if docx_path and os.path.exists(docx_path):
            os.remove(docx_path)
        # Ici, on ne supprime pas le PDF dans finally pour permettre son téléchargement
