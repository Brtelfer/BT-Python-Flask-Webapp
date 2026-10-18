import os
from datetime import datetime
import mysql.connector
import whisper
import fitz
import pypandoc
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pydub import AudioSegment
from pytubefix import YouTube
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "AS*#ncAKE#*$F25")

# ---- Directories ----
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---- Database ----
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "test1234"),
        database=os.getenv("DB_NAME", "BTDB"),
    )

def init_db():
    with get_db() as db:
        cur = db.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS `media_type` (`type_id` int AUTO_INCREMENT PRIMARY KEY, `type_name` varchar(50) UNIQUE NOT NULL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS `format` (`format_id` int AUTO_INCREMENT PRIMARY KEY, `format_name` varchar(20) UNIQUE NOT NULL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS `tag` (`tag_id` int AUTO_INCREMENT PRIMARY KEY, `tag_name` varchar(50) UNIQUE NOT NULL)""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS `media` (
                `media_id` int AUTO_INCREMENT PRIMARY KEY,
                `file_name` varchar(255) NOT NULL,
                `media_link` varchar(500) NOT NULL,
                `type_id` int NOT NULL,
                `date_of_creation` datetime NOT NULL,
                `notes` text,
                `stored_at` varchar(500),
                `is_downloaded` boolean NOT NULL,
                FOREIGN KEY (`type_id`) REFERENCES `media_type`(`type_id`)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS `media_tag` (
                `media_id` int NOT NULL,
                `tag_id` int NOT NULL,
                PRIMARY KEY (`media_id`, `tag_id`),
                FOREIGN KEY (`media_id`) REFERENCES `media`(`media_id`),
                FOREIGN KEY (`tag_id`) REFERENCES `tag`(`tag_id`)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS `conversion` (
                `conversion_id` int AUTO_INCREMENT PRIMARY KEY,
                `media_id` int NOT NULL,
                `format_id` int NOT NULL,
                `output_path` varchar(500),
                `converted_at` datetime NOT NULL,
                `file_size_mb` decimal(10,2),
                FOREIGN KEY (`media_id`) REFERENCES `media`(`media_id`),
                FOREIGN KEY (`format_id`) REFERENCES `format`(`format_id`)
            )
        """)
        db.commit()
        cur.close()

# ---- Conversions ----
def mp3_to_txt(mp3_file_path: str) -> str:
    model = whisper.load_model("base") 
    output = model.transcribe(
        mp3_file_path, fp16=False, language="en",
        condition_on_previous_text=False, beam_size=5,
        temperature=0.0, no_speech_threshold=0.7,
    )
    return output["text"]

def mp4_to_mp3(mp4_file_path: str, mp3_file_path: str) -> str:
    AudioSegment.from_file(mp4_file_path, format="mp4").export(mp3_file_path, format="mp3")
    return mp3_file_path

def pdf_to_epub(pdf_file_path: str, epub_file_path: str) -> str:
    doc = fitz.open(pdf_file_path)
    html_content = "".join(page.get_text("xhtml") for page in doc)
    doc.close()
    pypandoc.convert_text(
        html_content, "epub", format="html", outputfile=epub_file_path,
        extra_args=["--metadata", "title=Converted Document"],
    )
    return epub_file_path

def youtube_to_mp3(youtube_url: str, output_dir: str) -> str:
    yt = YouTube(youtube_url)
    stream = yt.streams.get_audio_only()
    return stream.download(output_path=output_dir)

# ---- Routes ----
@app.route("/")
def index():
    return render_template("index.html", toggle_on=session.get("toggle", False))

@app.route("/toggle", methods=["POST"])
def toggle():
    session["toggle"] = not session.get("toggle", False)
    return jsonify(state=session["toggle"])

@app.route("/convert", methods=["POST"])
def convert():
    conv_type = request.form.get("conversion_type")
    file = request.files.get("file")
    
    if not file or file.filename == '':
        return jsonify(error="No file uploaded"), 400

    filename = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_DIR, filename)
    file.save(input_path)

    try:
        if conv_type == "mp3_txt":
            output_filename = filename.rsplit('.', 1)[0] + ".txt"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            text = mp3_to_txt(input_path)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
                
        elif conv_type == "mp4_mp3":
            output_filename = filename.rsplit('.', 1)[0] + ".mp3"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            mp4_to_mp3(input_path, output_path)
            
        elif conv_type == "pdf_epub":
            output_filename = filename.rsplit('.', 1)[0] + ".epub"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            pdf_to_epub(input_path, output_path)
            
        else:
            return jsonify(error="Invalid conversion type"), 400

        return jsonify(ok=True, output=output_filename)

    except Exception as e:
        print(f"Conversion Error: {e}")
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    try:
        init_db()
        print("✅ Database initialized successfully.")
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")
        
    app.run(debug=True)