# Utilise une image de base Ubuntu
FROM ubuntu:latest

# Met à jour les paquets et installe LibreOffice et autres dépendances nécessaires
RUN apt-get update && \
    apt-get install -y libreoffice python3 python3-pip python3-venv

# Copie les fichiers de l'application dans le conteneur
WORKDIR /app

COPY requirements.txt requirements.txt

# Crée un environnement virtuel et installe les dépendances de l'application FastAPI
RUN python3 -m venv /opt/venv
RUN /opt/venv/bin/pip install --upgrade pip
RUN /opt/venv/bin/pip install -r requirements.txt

COPY . /app

# Expose le port sur lequel l'API va écouter
EXPOSE 80

# Commande pour exécuter l'application
CMD ["/opt/venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--log-level",  "info"]
