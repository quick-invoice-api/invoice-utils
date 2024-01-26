# invoice-utils

> [!NOTE]
> **Note on allowing your Google account to send mails with SMTP:**
> 
> If you're not using app passwords already, go to [Google Account Security](https://myaccount.google.com/security?hl=en&nlr=1). If you have 2-step authentication enabled, then search for "App Passwords" and create a new password. You'll need to use this password for:
> 
> ```sh
> INVOICE_UTILS_MAIL_LOGIN_PASSWORD = "app password"
> INVOICE_UTILS_MAIL_LOGIN_USER = "e-mail address"
> ```
