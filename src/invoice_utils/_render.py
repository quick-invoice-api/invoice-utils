from pathlib import Path

import jinja2
import weasyprint


def datetime_format(value, fmt="%Y-%m-%d"):
    return value.strftime(fmt)


class Renderer:
    def __init__(self, template_name: str):
        self.__templates_path = Path(__file__).parent / "templates"
        self.__jinja_template = template_name + ".jinja"
        self.__css_file = template_name + ".css"

    def render(self, context: dict):
        loader = jinja2.FileSystemLoader(searchpath=self.__templates_path)
        jinja_env = jinja2.Environment(loader=loader)
        jinja_env.filters["datetime_format"] = datetime_format
        html_template = jinja_env.get_template(self.__jinja_template)

        items_by_currency = {}
        for item in context["items"]:
            item_no = item["item_no"]
            currency_data = items_by_currency.get(item_no, [])
            currency_data.append(item)
            items_by_currency[item_no] = currency_data

        printer = weasyprint.HTML(string=html_template.render(
            by_currency=items_by_currency, **context
        ))
        css_file_path = self.__templates_path / self.__css_file
        stylesheet = weasyprint.CSS(filename=css_file_path)
        document = printer.render(stylesheets=[stylesheet])
        with open(self.__templates_path.parent/"out.pdf", "wb") as f:
            content = document.write_pdf()
            f.write(content)
