# Étape 1: Utiliser l'image pandoc/latex comme base pour obtenir Pandoc et LaTeX
FROM pandoc/latex:latest as pandoc-latex-stage

# Étape 2: Construire l'image finale basée sur Ubuntu
FROM ubuntu:latest

# Définir le répertoire de travail
WORKDIR /app

# Installer Python et pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copier Pandoc et ses dépendances depuis l'étape pandoc-latex-stage
COPY --from=pandoc-latex-stage /usr/local/bin/pandoc /usr/local/bin/pandoc
COPY --from=pandoc-latex-stage /opt /opt

# Installer les dépendances Python
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Copier les fichiers de l'application dans le conteneur
COPY . /app

# Exposer le port sur lequel l'API va écouter
EXPOSE 8000

# Commande pour exécuter l'application
CMD ["uvicorn", "main_ok:app", "--host", "0.0.0.0", "--port", "8000"]
