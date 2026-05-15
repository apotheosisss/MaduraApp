import uuid
from datetime import UTC, datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan_entity import ScanEntity
from app.schemas.scan_result import ScanResult


class HistoryService:
    async def save(
        self, scan: ScanResult, user_token: str, session: AsyncSession
    ) -> ScanEntity:
        entity = ScanEntity(
            scan_id=str(uuid.uuid4()),
            user_token=user_token,
            fruit_type=scan.fruit_type,
            maturity_label=scan.maturity_label,
            confidence=scan.confidence,
            bbox=scan.bbox,
            recommendation=scan.recommendation,
            color_code=scan.color_code,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        session.add(entity)
        await session.commit()
        await session.refresh(entity)
        return entity

    async def get_all(
        self,
        user_token: str,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ScanResult], int]:
        total: int = (
            await session.execute(
                select(func.count())
                .select_from(ScanEntity)
                .where(ScanEntity.user_token == user_token)
            )
        ).scalar_one()

        rows = (
            await session.execute(
                select(ScanEntity)
                .where(ScanEntity.user_token == user_token)
                .order_by(ScanEntity.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        ).scalars().all()

        items = [
            ScanResult(
                fruit_type=e.fruit_type,
                maturity_label=e.maturity_label,
                confidence=e.confidence,
                bbox=e.bbox,
                recommendation=e.recommendation,
                color_code=e.color_code,
            )
            for e in rows
        ]
        return items, total
