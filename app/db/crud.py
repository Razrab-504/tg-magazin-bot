from sqlalchemy.orm import Session
from app.db import models
from datetime import datetime

def list_active_products(db: Session):
    return db.query(models.Product).filter(models.Product.active == True).all()

def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def create_product(db: Session, title: str, bank_card: int, description: str = "", price: int = 0, file_id: str = None, active: bool = True):
    p = models.Product(
        title=title,
        description=description,
        price=price,
        file_id=file_id,
        active=active,
        bank_card=bank_card,
        created_at=datetime.utcnow()
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def get_or_create_user(db: Session, tg_id: int, name: str = None, phone: str = None):
    user = db.query(models.User).filter(models.User.tg_id == tg_id).first()
    if user:
        if phone and (user.phone is None or user.phone == ""):
            user.phone = phone
            db.commit()
            db.refresh(user)
        return user

    user = models.User(
        tg_id=tg_id,
        name=name,
        phone=phone,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_order(db: Session, user_id: int, product_id: int, proof: str = None):
    o = models.Order(
        user_id=user_id,
        product_id=product_id,
        proof=proof,
        status="pending",
        created_at=datetime.utcnow()
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return o

def update_order_status(db: Session, order_id: int, status: str):
    o = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not o:
        return None
    o.status = status
    db.commit()
    db.refresh(o)
    return o


def get_user_orders_by_tg(db: Session, tg_id: int):
    user = db.query(models.User).filter(models.User.tg_id == tg_id).first()
    if not user:
        return []
    return db.query(models.Order).filter(models.Order.user_id == user.id).all()


def list_pending_orders(db: Session):
    return db.query(models.Order).filter(models.Order.status == "pending").all()


def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id==order_id).first()

