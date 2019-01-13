from smtplib import SMTP
from email.mime.text import MIMEText

import skyscraper.settings


def send_treshold_warning_mail(
        destination, namespace, spider,
        actual_count, threshold, warntype):
    server = skyscraper.settings.MAIL_SERVER
    username = skyscraper.settings.MAIL_USER
    password = skyscraper.settings.MAIL_PASSWORD
    sender = skyscraper.settings.MAIL_FROM

    subject = 'Scraping: Spider %s/%s does not seem to run (%s)' \
        % (namespace, spider, warntype)
    content = 'The spider %s/%s did only write %d elements, but the ' \
        % (namespace, spider, actual_count) \
        + 'threshold for %s was set to %d elements.' \
        % (warntype, threshold)

    msg = MIMEText(content, 'plain')
    msg['Subject'] = subject
    msg['From'] = sender

    conn = SMTP(server)
    conn.starttls()
    conn.set_debuglevel(False)
    conn.login(username, password)
    try:
        conn.sendmail(sender, destination, msg.as_string())
    finally:
        conn.quit()
