from utils import get_config, get_credentials
import logging
import smtplib, ssl
from email.message import EmailMessage
from API import API

def send_signal_email(symbol, target_rsi):
    port = 465  # For SSL
    password = get_credentials()['gmail']

    # Create a secure SSL context
    context = ssl.create_default_context()
    me = "faysalkhatri@gmail.com"
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(me, password)

        msg = EmailMessage()
        msg['Subject'] = f'Buy signal alert - {symbol}'
        msg['From'] = me
        msg['To'] = [me] 
        msg.set_content(f"""Buy {symbol} today, sell once 21-day RSI reaches 1.25 stds above mean ({target_rsi}).\n\n{API.get_profile_string(symbol)}""")

        server.send_message(msg)
        server.quit()