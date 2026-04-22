from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.db import get_db
from ovejitas.core.pagination import PageParams

DBSession = Annotated[AsyncSession, Depends(get_db)]
PageDep = Annotated[PageParams, Query()]
