FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Light theme before app.py's CSS loads (prevents dark flash on first page load)
ENV STREAMLIT_SERVER_ENABLE_STATIC_SERVING=true \
    STREAMLIT_THEME_BASE=light \
    STREAMLIT_THEME_PRIMARY_COLOR="#0064D9" \
    STREAMLIT_THEME_BACKGROUND_COLOR="#ffffff" \
    STREAMLIT_THEME_SECONDARY_BACKGROUND_COLOR="#f0f3f8" \
    STREAMLIT_THEME_TEXT_COLOR="#17243a"

CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true"]