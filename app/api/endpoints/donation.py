from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.user import current_superuser, current_user
from app.crud.charity_project import charity_project_crud
from app.crud.donation import donation_crud
from app.models.user import User
from app.schemas.donation import DonationCreate, DonationDB, DonationFullInfoDB
from app.services.investment import invest

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUser = Annotated[User, Depends(current_user)]
CurrentSuperuser = Annotated[User, Depends(current_superuser)]


@router.get(
    '/',
    response_model=list[DonationFullInfoDB],
    response_model_exclude_none=True,
)
async def get_all_donations(
    session: SessionDep,
    user: CurrentSuperuser,
):
    return await donation_crud.get_multi(session)


@router.get(
    '/my',
    response_model=list[DonationDB],
    response_model_exclude_none=True,
)
async def get_my_donations(
    session: SessionDep,
    user: CurrentUser,
):
    return await donation_crud.get_by_user(
        user.id,
        session,
    )


@router.post(
    '/',
    response_model=DonationDB,
    response_model_exclude_none=True,
)
async def create_donation(
    donation_in: DonationCreate,
    session: SessionDep,
    user: CurrentUser,
):
    donation = await donation_crud.create(
        donation_in,
        session,
        user.id,
    )

    projects = await charity_project_crud.get_not_fully_invested(session)
    invest(donation, projects)

    await session.commit()
    await session.refresh(donation)

    return donation
