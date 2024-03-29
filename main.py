from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import io
from docx2pdf import convert
import os

app = FastAPI()

class DocxToPdf(BaseModel):
    url: str

@app.get("/convert")
async def convert_docx_to_pdf(data: DocxToPdf):
    try:
        response = requests.get(data.url)
        response.raise_for_status()

        with open("document.docx", "wb") as f:
            f.write(response.content)

        convert("document.docx", "document.pdf")

        with open("document.pdf", "rb") as f:
            pdf_content = f.read()

        os.remove("document.docx")
        os.remove("document.pdf")

        return {"pdf": pdf_content}

    except requests.exceptions.HTTPError as errh:
        raise HTTPException(status_code=500, detail="An HTTP error occurred when getting the document.")
    except requests.exceptions.ConnectionError as errc:
        raise HTTPException(status_code=500, detail="A Connection error occurred when getting the document.")
    except requests.exceptions.Timeout as errt:
        raise HTTPException(status_code=500, detail="A Timeout error occurred when getting the document.")
    except requests.exceptions.RequestException as err:
        raise HTTPException(status_code=500, detail="An Unknown error occurred when getting the document.")
