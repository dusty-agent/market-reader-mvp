# send_email.py

from __future__ import annotations

import os
import smtplib

from email.message import EmailMessage
from pathlib import Path


def send_video_email(
    video_path: Path,
    subject: str,
) -> None:

    sender = os.environ["MAIL_SENDER"]
    password = os.environ["MAIL_APP_PASSWORD"]
    recipient = os.environ["MAIL_RECIPIENT"]

    msg = EmailMessage()

    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject

    msg.set_content(
        "오늘의 환율 전광판 영상이 생성되었습니다.\n\n"
        "첨부파일을 확인해주세요."
    )

    with video_path.open("rb") as f:

        msg.add_attachment(
            f.read(),
            maintype="video",
            subtype="mp4",
            filename=video_path.name,
        )

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465,
    ) as smtp:

        smtp.login(
            sender,
            password,
        )

        smtp.send_message(msg)

    print(
        f"[OK] EMAIL  : {recipient}"
    )