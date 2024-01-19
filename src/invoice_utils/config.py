import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MAIL_HOST = "smtp.gmail.com"
DEFAULT_PORT = 587

INVOICE_UTILS_MAIL_HOST = os.getenv("INVOICE_UTILS_MAIL_HOST", DEFAULT_MAIL_HOST)
INVOICE_UTILS_MAIL_PORT = os.getenv("INVOICE_UTILS_MAIL_PORT", DEFAULT_PORT)
INVOICE_UTILS_MAIL_LOGIN_USER = os.getenv("INVOICE_UTILS_MAIL_LOGIN_USER")
INVOICE_UTILS_MAIL_LOGIN_PASSWORD = os.getenv("INVOICE_UTILS_MAIL_LOGIN_PASSWORD")
INVOICE_UTILS_SENDER_EMAIL = os.getenv("INVOICE_UTILS_SENDER_EMAIL")
INVOICE_UTILS_MAIL_SUBJECT = "Invoice generated with invoice-utils"
