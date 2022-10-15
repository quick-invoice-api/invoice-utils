class InvoicingInputError(Exception):
    def __init__(self, file_name: str):
        super().__init__(self)
        self.__message = self._construct_message(file_name)

    def _construct_message(self, file_name):
        return f"file '{file_name}' not found"

    def __str__(self):
        return self.__message


class InvoicingInputFormatError(InvoicingInputError):
    def _construct_message(self, file_name):
        return f"file '{file_name}' not does not contain valid json"
