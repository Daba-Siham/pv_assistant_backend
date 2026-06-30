from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import DBSession, require_admin_user
from app.models.contact_message import ContactMessage
from app.schemas.contact import (
    ContactMessageCreate,
    ContactMessageRead,
    ContactMessageUpdateStatus,
)


router = APIRouter()
admin_router = APIRouter()


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
