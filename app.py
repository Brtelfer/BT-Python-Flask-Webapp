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

load_dotenv()  

# ---- App & config ----
app = Flask(__name__)

# ---- Database ----
def get_db():
    """Return a fresh connection. Short-lived, per-request."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "test1234"),
        database=os.getenv("DB_NAME", "BTDB"),
    )

# ---- Schema ----
def init_db():
    """Creates the database schema if it doesn't exist."""
    with get_db() as db:
        cur = db.cursor()
        
        # 1. Independent tables first
        cur.execute("""
            CREATE TABLE IF NOT EXISTS `media_type` (
                `type_id` int AUTO_INCREMENT PRIMARY KEY,
                `type_name` varchar(50) UNIQUE NOT NULL
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS `format` (
                `format_id` int AUTO_INCREMENT PRIMARY KEY,
                `format_name` varchar(20) UNIQUE NOT NULL
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS `tag` (
                `tag_id` int AUTO_INCREMENT PRIMARY KEY,
                `tag_name` varchar(50) UNIQUE NOT NULL
            )
        """)

        # 2. Tables with Foreign Keys
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
    model = whisper.load_model("medium")
    output = model.transcribe(
        mp3_file_path,
        fp16=False,                       
        language="en",
        condition_on_previous_text=False,
        beam_size=5,
        temperature=0.0,
        no_speech_threshold=0.7,
    )
    return output["text"]

def mp4_to_mp3(mp4_file_path: str, mp3_file_path: str) -> str:
    AudioSegment.from_file(mp4_file_path, format="mp4") \
        .export(mp3_file_path, format="mp3")
    return mp3_file_path

def pdf_to_epub(pdf_file_path: str, epub_file_path: str) -> str:
    doc = fitz.open(pdf_file_path)
    html_content = "".join(page.get_text("xhtml") for page in doc)
    doc.close()

    pypandoc.convert_text(
        html_content,
        "epub",
        format="html",
        outputfile=epub_file_path,
        extra_args=["--metadata", "title=Converted Document"],
    )
    return epub_file_path

def youtube_to_mp3(youtube_url: str, output_dir: str) -> str:
    """Download audio-only stream. Returns the actual saved file path."""
    yt = YouTube(youtube_url)
    stream = yt.streams.get_audio_only()
    saved_path = stream.download(output_path=output_dir)
    return saved_path

# ---- Routes ----
@app.route("/")
def index():
    return render_template("index.html", toggle_on=session.get("toggle", False))

@app.route("/toggle", methods=["POST"])
def toggle():
    session["toggle"] = not session.get("toggle", False)
    return jsonify(state=session["toggle"])

# ---- Bootstrap ----
if __name__ == "__main__":
    init_db()                # schema creation only when actually running
    app.run(debug=True)