import os
from dotenv import load_dotenv

load_dotenv()

MAIL_HOST = os.getenv("MAIL_HOST")
MAIL_PORT = os.getenv("MAIL_PORT")
MAIL_LOGIN_USER = os.getenv("MAIL_LOGIN_USER")
MAIL_LOGIN_PASSWORD = os.getenv("MAIL_LOGIN_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
MAIL_SUBJECT = "Invoice generated with invoice-utils"
