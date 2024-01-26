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

> [!NOTE]
> **Note on allowing your Google account to send mails with SMTP:**
> 
> If you're not using app passwords already, go to [Google Account Security](https://myaccount.google.com/security?hl=en&nlr=1). If you have 2-step authentication enabled, then search for "App Passwords" and create a new password. You'll need to use this password for:
> 
> ```sh
> INVOICE_UTILS_MAIL_LOGIN_PASSWORD = "app password"
> INVOICE_UTILS_MAIL_LOGIN_USER = "e-mail address"
> ```