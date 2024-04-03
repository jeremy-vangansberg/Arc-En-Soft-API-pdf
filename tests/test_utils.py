import pytest
import requests_mock
from unittest import mock
from api.utils import download_docx_file, convert_docx_to_pdf, log_to_ftp

@pytest.fixture
def mock_ftp_server():
    # Cette fixture peut démarrer un vrai serveur FTP en utilisant pyftpdlib
    # ou simplement simuler les interactions FTP avec unittest.mock
    pass

def test_download_docx_file():
    with requests_mock.Mocker() as m:
        m.get("https://example.com/document.docx", content=b"Fake docx file content")
        temp_file_path = download_docx_file("https://example.com/document.docx")
        # Assurez-vous que le fichier existe et contient le bon contenu
        with open(temp_file_path, "rb") as f:
            assert f.read() == b"Fake docx file content"

@mock.patch("subprocess.run")
def test_convert_docx_to_pdf(mock_run):
    # Simuler le succès de la commande libreoffice
    mock_run.return_value = mock.Mock(returncode=0)
    docx_path = "/fake/path/document.docx"
    pdf_path = convert_docx_to_pdf(docx_path)
    assert pdf_path == "/fake/path/document.pdf"
    mock_run.assert_called_once()

@mock.patch("ftplib.FTP")
def test_log_to_ftp(mock_ftp):
    # Simuler une instance FTP et ses méthodes
    mock_ftp_instance = mock_ftp.return_value
    mock_ftp_instance.cwd.return_value = None
    mock_ftp_instance.storbinary.return_value = None

    log_message = "Test log message"
    log_to_ftp("ftp.example.com", "user", "pass", log_message)

    # Vérifiez si storbinary a été appelé avec le bon chemin et contenu de fichier
    mock_ftp_instance.cwd.assert_called_with('/')
    mock_ftp_instance.storbinary.assert_called()

# Ici vous pouvez ajouter d'autres tests pour les fonctions restantes
