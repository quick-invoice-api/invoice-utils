from starlette.responses import JSONResponse

from ._request import InvoiceRequest


class InvoiceRequestInputError(Exception):
    def __init__(self, message: str):
        self.message = message


class InvoiceRequestEmailError(Exception):
    def __init__(self, message: str):
        self.message = message


def input_error_handler(_: InvoiceRequest, exc: InvoiceRequestInputError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"message": f"{exc.message}"},
    )


def email_error_handler(_: InvoiceRequest, exc: InvoiceRequestEmailError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"message": f"{exc.message}"})

