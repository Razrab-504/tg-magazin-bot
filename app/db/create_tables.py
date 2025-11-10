from app.db.session import engine, Base
from app.db import models

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("Таблицы успешно удалины и созданы!")
