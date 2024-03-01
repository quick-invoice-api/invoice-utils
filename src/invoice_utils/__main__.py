from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
import invoice_utils.depends as di
load_dotenv()
import invoice_utils.config as config
from invoice_utils.api import *


@asynccontextmanager
async def lifespan(_: FastAPI):
    repo = di.template_repo()

    if not repo.exists(config.DEFAULT_RULE_TEMPLATE_NAME):
        raise Exception()
    if not repo.exists(config.INVOICE_UTILS_RULE_TEMPLATE_NAME):
        config.INVOICE_UTILS_RULE_TEMPLATE_NAME = config.DEFAULT_RULE_TEMPLATE_NAME
    yield


# API setup
API_PATH_PREFIX = "/api/v1"
app = FastAPI(lifespan=lifespan)
app.include_router(template_router, prefix=API_PATH_PREFIX)
app.include_router(templates_router, prefix=API_PATH_PREFIX)
app.include_router(invoices_router, prefix=API_PATH_PREFIX)

app.add_exception_handler(InvoiceRequestInputError, input_error_handler)
app.add_exception_handler(InvoiceRequestEmailError, email_error_handler)
