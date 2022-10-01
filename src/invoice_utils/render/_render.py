from pathlib import Path

import jinja2
import weasyprint


def datetime_format(value, fmt="%Y-%m-%d"):
    return value.strftime(fmt)


def number_format(value, fmt="%.2f"):
    return fmt % float(value)


class PdfInvoiceRenderer:
    def __init__(self, template_name: str):
        self.__templates_path = Path(__file__).parent / "templates"
        self.__jinja_template = template_name + ".jinja"
        self.__css_file = template_name + ".css"

    def render(self, context: dict, output_path: str):
        loader = jinja2.FileSystemLoader(searchpath=self.__templates_path)
        jinja_env = jinja2.Environment(loader=loader)
        jinja_env.filters["datetime_format"] = datetime_format
        jinja_env.filters["number_format"] = number_format
        html_template = jinja_env.get_template(self.__jinja_template)

        printer = weasyprint.HTML(string=html_template.render(
            **context
        ))
        css_file_path = self.__templates_path / self.__css_file
        stylesheet = weasyprint.CSS(filename=css_file_path)
        document = printer.render(stylesheets=[stylesheet])
        with open(output_path, "wb") as f:
            content = document.write_pdf()
            f.write(content)
