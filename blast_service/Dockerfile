FROM python:3.9-slim

# Install BLAST+ dependencies
RUN apt-get update && apt-get install -y \
    wget \
    libgomp1 \
    libidn2-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install BLAST+
RUN wget ftp://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/ncbi-blast-2.14.1+-x64-linux.tar.gz \
    && tar -xzf ncbi-blast-2.14.1+-x64-linux.tar.gz \
    && cp ncbi-blast-2.14.1+/bin/* /usr/local/bin/ \
    && rm -rf ncbi-blast-2.14.1+-x64-linux.tar.gz ncbi-blast-2.14.1+

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create directories
RUN mkdir -p db uploads

# Expose the port the app runs on
EXPOSE 5001

# Command to run the application
CMD ["python", "app.py"]
