import pytest
import requests_mock
from unittest import mock
from api.utils import download_docx_file, convert_docx_to_pdf, log_to_ftp

@pytest.fixture
def docx_file():
    return "https://capcertification.com/wp-content/uploads/audit/2021/11361/11361-Contrat-CAPCERT-20240328-174118.docx"

@pytest.fixture
def docx_path():
    return "/fake/path/document.docx"

@pytest.fixture
def pdf_path():
    return "/fake/path/document.pdf"

def test_download_docx_file(docx_file):
    with requests_mock.Mocker() as m:
        m.get(docx_file, content=b"Fake docx file content")
        temp_file_path = download_docx_file(docx_file)
        # Assurez-vous que le fichier existe et contient le bon contenu
        with open(temp_file_path, "rb") as f:
            assert f.read() == b"Fake docx file content"

@mock.patch("subprocess.run")
@mock.patch("os.path.exists")
def test_convert_docx_to_pdf(mock_exists, mock_run, docx_path, pdf_path):
    # Simuler le succès de la commande libreoffice et l'existence du fichier PDF
    mock_run.return_value = mock.Mock(returncode=0)
    mock_exists.return_value = True  # Simule que le fichier PDF existe après la conversion

    # Appel de la fonction testée
    result_path = convert_docx_to_pdf(docx_path)

    # Assertions
    assert result_path == pdf_path
    mock_run.assert_called_once()  # Vérifie que la commande de conversion a été exécutée
    mock_exists.assert_called_with(pdf_path)  # Vérifie que le chemin du fichier PDF est vérifié

@mock.patch("api.utils.FTP")
def test_log_to_ftp(mock_ftp):
    # Simuler une instance FTP et ses méthodes
    mock_ftp_instance = mock_ftp.return_value.__enter__.return_value
    log_message = "Test log message"
    log_to_ftp("ftp.example.com", "user", "pass", log_message)

    # Vérifiez si storbinary a été appelé avec le bon chemin et contenu de fichier
    mock_ftp_instance.cwd.assert_called_with('/logs')
    mock_ftp_instance.storbinary.assert_called()