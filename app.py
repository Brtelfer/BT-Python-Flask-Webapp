from flask import (Flask, render_template, request, redirect, url_for)
from psycopg2 import pool as po import os from dotenv
import load_dotenv

load_dotenv()
