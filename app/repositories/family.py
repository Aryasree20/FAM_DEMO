"""Family and member repository.

TODO:
- Implement family/member lookup and demo-household persistence queries.
- Return domain data without HTTP or model-provider concerns.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.family import Family
from app.models.family_member import FamilyMember


async def create_family(
    db: AsyncSession,
    name: str,
    timezone: str = "Asia/Kolkata",
) -> Family:
    family = Family(
        name=name,
        timezone=timezone,
    )

    db.add(family)
    await db.commit()
    await db.refresh(family)

    return family


async def get_families(
    db: AsyncSession,
) -> list[Family]:
    result = await db.execute(
        select(Family).order_by(Family.created_at.desc())
    )

    return list(result.scalars().all())


async def get_family(
    db: AsyncSession,
    family_id: UUID,
) -> Family | None:
    result = await db.execute(
        select(Family).where(Family.id == family_id)
    )

    return result.scalar_one_or_none()


async def create_family_member(
    db: AsyncSession,
    family_id: UUID,
    name: str,
    relationship: str,
    role: str | None = None,
) -> FamilyMember:
    member = FamilyMember(
        family_id=family_id,
        name=name,
        relationship=relationship,
        role=role,
    )

    db.add(member)
    await db.commit()
    await db.refresh(member)

    return member


async def get_family_members(
    db: AsyncSession,
    family_id: UUID,
) -> list[FamilyMember]:
    result = await db.execute(
        select(FamilyMember)
        .where(FamilyMember.family_id == family_id)
        .order_by(FamilyMember.created_at)
    )

    return list(result.scalars().all())