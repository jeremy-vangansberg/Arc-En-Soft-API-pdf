# Utilise l'image officielle de Pandoc avec LaTeX
FROM pandoc/latex:latest-ubuntu

WORKDIR /app

# Met à jour les paquets, installe Python et pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-distutils python3-apt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Installe les dépendances Python
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Copie les fichiers de l'application dans le conteneur
COPY . /app

# Expose le port sur lequel l'API va écouter
EXPOSE 8000

# Commande pour exécuter l'application
CMD ["uvicorn", "main_ok:app", "--host", "0.0.0.0", "--port", "8000"]
