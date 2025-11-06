# ==========================================
# EURO_GOALS Unified – Docker Build
# ==========================================
FROM python:3.12.6-slim

# Ορίζουμε τον φάκελο εργασίας
WORKDIR /app

# Αντιγραφή όλων των αρχείων του project στο container
COPY . .

# Εγκατάσταση όλων των απαιτούμενων βιβλιοθηκών
RUN pip install --no-cache-dir -r requirements.txt

# Άνοιγμα της θύρας 10000 (που απαιτεί το Render)
EXPOSE 10000

# Εκκίνηση εφαρμογής FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
