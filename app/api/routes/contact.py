import smtplib
import ssl
from email.message import EmailMessage

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.dependencies import DBSession, require_admin_user
from app.models.contact_message import ContactMessage
from app.schemas.contact import (
    ContactMessageCreate,
    ContactMessageRead,
    ContactMessageUpdateStatus,
)
from app.services.shared.logger import get_logger


router = APIRouter()
admin_router = APIRouter()
logger = get_logger(__name__)


def _send_contact_notification(message: ContactMessage) -> None:
    return _send_contact_confirmation(message)

    receiver = (settings.CONTACT_RECEIVER_EMAIL or "team.solaiai26@gmail.com").strip()
    smtp_host = str(settings.SMTP_HOST or "").strip()
    smtp_port = settings.SMTP_PORT
    smtp_user = str(settings.SMTP_USER or "").strip()
    smtp_password = str(settings.SMTP_PASSWORD or "").strip()
    from_email = str(settings.SMTP_FROM_EMAIL or "").strip() or smtp_user
    

    if not (smtp_host and smtp_port and smtp_user and smtp_password and from_email):
        logger.warning(
            "Contact email notification skipped: SMTP not configured for receiver %s.",
            receiver,
        )
        return

    subject_text = str(message.subject or "").strip() or "Sans sujet"
    email = EmailMessage()
    email["Subject"] = f"[SolarAI] Nouveau message de contact: {subject_text}"
    email["From"] = from_email
    email["To"] = receiver
    email["Reply-To"] = message.email
    email.set_content(
        "\n".join(
            [
                "Un nouveau message a été soumis via le formulaire de contact SolarAI.",
                "",
                f"Nom: {message.name}",
                f"Email: {message.email}",
                f"Sujet: {subject_text}",
                "",
                "Message:",
                message.message,
            ]
        )
    )

    try:
        if smtp_port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=15) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(email)
        else:
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                try:
                    server.starttls(context=context)
                    server.ehlo()
                except smtplib.SMTPException:
                    logger.info("Contact email SMTP server did not accept STARTTLS; continuing without TLS.")
                server.login(smtp_user, smtp_password)
                server.send_message(email)

        logger.info("Contact notification email sent to %s.", receiver)
    except Exception as exc:
        logger.warning("Failed to send contact notification email to %s: %s", receiver, exc)


def _send_contact_confirmation(message: ContactMessage) -> None:
    receiver = (settings.CONTACT_RECEIVER_EMAIL or "team.solaiai26@gmail.com").strip()
    smtp_host = str(settings.SMTP_HOST or "").strip()
    smtp_port = settings.SMTP_PORT
    smtp_user = str(settings.SMTP_USER or "").strip()
    smtp_password = str(settings.SMTP_PASSWORD or "").strip()
    from_email = str(settings.SMTP_FROM_EMAIL or "").strip() or smtp_user

    if not (smtp_host and smtp_port and smtp_user and smtp_password and from_email):
        logger.warning(
            "Contact confirmation skipped: SMTP not configured for receiver %s.",
            receiver,
        )
        return

    subject_text = str(message.subject or "").strip() or "Sans sujet"
    email = EmailMessage()
    email["Subject"] = f"[SolarAI] Nouveau message de contact: {subject_text}"
    print("waaaaaaaaaaaaaaaaaaaaa ", message.email)
    email["From"] = message.email
    print("waaaaaaaaaaaaaaaaaaaaa ", receiver)
    email["To"] = receiver
    email["Reply-To"] = message.email
    email.set_content(
        "\n".join(
            [
                "Un nouveau message a été soumis via le formulaire de contact SolarAI.",
                "",
                f"Nom: {message.name}",
                f"Email: {message.email}",
                f"Sujet: {subject_text}",
                "",
                "Message:",
                message.message,
            ]
        )
    )

    try:
        if smtp_port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=15) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(email)
        else:
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                try:
                    server.starttls(context=context)
                    server.ehlo()
                except smtplib.SMTPException:
                    logger.info("Contact email SMTP server did not accept STARTTLS; continuing without TLS.")
                server.login(smtp_user, smtp_password)
                server.send_message(email)

        logger.info("Contact notification email sent to %s.", receiver)
    except Exception as exc:
        logger.warning("Failed to send contact notification email to %s: %s", receiver, exc)


@router.post("", status_code=status.HTTP_200_OK)
def create_contact_message(payload: ContactMessageCreate, db: DBSession):
    name = payload.name.strip()
    message_text = payload.message.strip()
    if not name or not message_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid contact message")

    message = ContactMessage(
        name=name,
        email=payload.email,
        subject=payload.subject.strip() if isinstance(payload.subject, str) and payload.subject.strip() else None,
        message=message_text,
        status="new",
    )

    db.add(message)
    db.commit()
    db.refresh(message)
    _send_contact_confirmation(message)

    return {
        "success": True,
        "message": "Message sent successfully",
    }


@admin_router.get("/contact-messages", response_model=list[ContactMessageRead], status_code=status.HTTP_200_OK)
def list_contact_messages(db: DBSession, admin_user=Depends(require_admin_user)):
    del admin_user
    return db.query(ContactMessage).order_by(ContactMessage.created_at.desc()).all()


@admin_router.get("/contact-messages/{message_id}", response_model=ContactMessageRead, status_code=status.HTTP_200_OK)
def get_contact_message(message_id: int, db: DBSession, admin_user=Depends(require_admin_user)):
    del admin_user
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact message not found")
    return message


@admin_router.patch(
    "/contact-messages/{message_id}/status",
    response_model=ContactMessageRead,
    status_code=status.HTTP_200_OK,
)
def update_contact_message_status(
    message_id: int,
    payload: ContactMessageUpdateStatus,
    db: DBSession,
    admin_user=Depends(require_admin_user),
):
    del admin_user
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact message not found")

    message.status = payload.status
    db.commit()
    db.refresh(message)
    return message


@admin_router.delete("/contact-messages/{message_id}", status_code=status.HTTP_200_OK)
def delete_contact_message(message_id: int, db: DBSession, admin_user=Depends(require_admin_user)):
    del admin_user
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact message not found")

    db.delete(message)
    db.commit()
    return {"success": True, "message": "Contact message deleted successfully"}
