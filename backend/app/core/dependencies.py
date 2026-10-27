from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.session import get_db

from app.modules.identity.models import User

from app.modules.farmer.models import Farmer
from app.modules.farmer.repository import FarmerRepository

from app.shared.exceptions import FarmerProfileNotFoundError


def get_current_farmer(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Farmer:
    repository = FarmerRepository(db)

    farmer = repository.get_by_user_id(current_user.id)

    if farmer is None:
        raise FarmerProfileNotFoundError()

    return farmer