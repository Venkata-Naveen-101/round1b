FROM --platform=linux/amd64 python:3.9-slim

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Optional but recommended to disable HuggingFace hub network

# Install OS dependencies
RUN apt-get update || true
RUN apt-get install -y tesseract-ocr
RUN apt-get install -y libtesseract-dev
RUN apt-get install -y poppler-utils
RUN apt-get install -y fonts-dejavu
RUN apt-get install -y build-essential
RUN apt-get install -y libgl1
RUN apt-get install -y libxext6
RUN apt-get install -y libxrender-dev
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy code and model files
COPY . /app
COPY local_model /app/local_model

# Install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Run the main script
CMD ["python", "challenge1b_semantic.py"]
