# invoice-utils

## Building

We use [Docker](https://www.docker.com) containers to package the invoicing app.
The Docker image has two target stages:

 * `test` - is used for building and running our automated test suite
 * `runtime` - is used for building and running our app

To build the `test` image, run:

```shell
$ docker build --target test --tag <your-tag-here> .
```

To build the `runtime` image, run:
```shell
$ docker build --target runtime --tag <your-tag-here> .
```

To run the app, you need to build the `runtime` image and then run that via
`docker run`.
To run the app's automated test suite you need to build the `test` image and
run that using `docker run`.

## Environment

| Variable Name                      | Description                                                                                                                                                       | Example                               |
|------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| `INVOICE_UTILS_MAIL_HOST`         | Hostname of the SMTP server used for sending emails. Default value is `smtp.gmail.com`.                                                                           | `"smtp.gmail.com"`                    |
| `INVOICE_UTILS_MAIL_PORT`         | Port number of the SMTP server. Default value is `587`.                                                                                                           | `587`                                 |
| `INVOICE_UTILS_MAIL_SUBJECT`      | Default subject line for the email containing the generated invoice.                                                                                               | `"Invoice generated with invoice-utils"` |
| `INVOICE_UTILS_MAIL_LOGIN_USER`   | Username for authenticating with the SMTP server.                                                                                                                  | `"example@gmail.com"`                 |
| `INVOICE_UTILS_MAIL_LOGIN_PASSWORD`| Password for authenticating with the SMTP server.                                                                                                                  | `"password123"`                       |
| `INVOICE_UTILS_SENDER_EMAIL`      | Email address of the sender.                                                                                                                                      | `"sender@example.com"`                |
| `INVOICE_UTILS_SMTP_TLS`          | Boolean indicating whether TLS (Transport Layer Security) should be used for the SMTP connection. Default is `True`.                                             | `True` or `False`                     |
| `INVOICE_UTILS_BODY_TEMPLATE_NAME`| Name of the HTML template file for the email body. Default is `"default_template.html"`.                                                                           | `"invoice_template.html"`             |
| `INVOICE_UTILS_BODY_TEMPLATE_PACKAGE` | Python package where the body template file is located. Default is `"invoice_utils"`.                                                                          | `"custom_email_templates"`            |
| `INVOICE_UTILS_INVOICE_DIR`       | Directory where the generated invoice files are stored. Default is `"invoices"`.                                                                                   | `"custom_invoice_directory"`          |
| `INVOICE_UTILS_TEMPLATES_DIR`     | Directory containing the email template files. Default is `"email_templates"`.                                                                                    | `"templates"`                         |
| `INVOICE_UTILS_RULE_TEMPLATE_NAME`| Name of the rule template file for processing invoices.                                                                                                             | `"basic"`                             |


> [!NOTE]
> **Note on allowing your Google account to send mails with SMTP:**
> 
> If you're not using app passwords already, go to [Google Account Security](https://myaccount.google.com/security?hl=en&nlr=1). If you have 2-step authentication enabled, then search for "App Passwords" and create a new password. You'll need to use this password for:
> 
> ```sh
> INVOICE_UTILS_MAIL_LOGIN_PASSWORD = "app password"
> INVOICE_UTILS_MAIL_LOGIN_USER = "e-mail address"
> ```