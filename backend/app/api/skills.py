from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.skill import Skill
from app.schemas.skill import SkillOut

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[SkillOut])
def list_skills(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
) -> list[Skill]:
    return list(db.scalars(select(Skill).order_by(Skill.name)).all())
