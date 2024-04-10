# Utilise une image de base Ubuntu
FROM ubuntu:latest

# Met à jour les paquets et installe LibreOffice
RUN apt-get update && \
    apt-get install -y libreoffice

# Installe Python et pip
RUN apt-get install -y python3 python3-pip

# Copie les fichiers de l'application dans le conteneur
WORKDIR /app

COPY requirements.txt requirements.txt
# Installe les dépendances de l'application FastAPI
RUN pip install -r requirements.txt

COPY . /app

# Expose le port sur lequel l'API va écouter
EXPOSE 80

# Commande pour exécuter l'application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--log-level",  "info"]