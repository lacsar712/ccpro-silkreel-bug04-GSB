from datetime import timedelta

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Basin, BathReading, Filature, User, utcnow
from app.security import hash_password


async def seed_demo() -> None:
    async with SessionLocal() as session:
        existing = await session.execute(select(User).where(User.username == "admin"))
        admin = existing.scalar_one_or_none()
        if admin is None:
            admin = User(username="admin", password_hash=hash_password("123456"), role="admin")
            session.add(admin)
        else:
            admin.password_hash = hash_password("123456")
            admin.role = "admin"

        existing_w = await session.execute(select(User).where(User.username == "worker"))
        worker = existing_w.scalar_one_or_none()
        if worker is None:
            session.add(User(username="worker", password_hash=hash_password("123456"), role="worker"))
        else:
            worker.password_hash = hash_password("123456")
            worker.role = "worker"

        mill = (await session.execute(select(Filature))).scalars().first()
        if mill:
            await session.commit()
            return

        mill = Filature(name="江口缫丝坞", riverside="东津渡")
        session.add(mill)
        await session.flush()
        now = utcnow()
        specs = [
            ("甲-1", Basin.STATUS_REELING, 40.5, 0),
            ("甲-2", Basin.STATUS_SOAKING, None, 1),
            ("乙-1", Basin.STATUS_REELED, 39.2, 2),
            ("乙-2", Basin.STATUS_REELING, 36.0, 3),
            ("丙-1", Basin.STATUS_SOAKING, None, 4),
            ("丙-2", Basin.STATUS_REELED, 41.0, 5),
        ]
        for code, status, temp, idx in specs:
            basin = Basin(filature_id=mill.id, code=code, status=status, ring_index=idx)
            session.add(basin)
            await session.flush()
            if temp is not None:
                session.add(
                    BathReading(
                        basin_id=basin.id,
                        water_temp_c=temp,
                        operator="worker",
                        taken_at=now - timedelta(hours=2),
                    )
                )
        # 额外双读：最早在带/最近出带，以及最早出带/最近在带
        extra = await session.execute(select(Basin).where(Basin.code.in_(["甲-2", "乙-2"])))
        by_code = {b.code: b for b in extra.scalars().all()}
        if "甲-2" in by_code:
            session.add(
                BathReading(
                    basin_id=by_code["甲-2"].id,
                    water_temp_c=40.0,
                    operator="admin",
                    taken_at=now - timedelta(hours=5),
                )
            )
            session.add(
                BathReading(
                    basin_id=by_code["甲-2"].id,
                    water_temp_c=45.0,
                    operator="worker",
                    taken_at=now - timedelta(minutes=30),
                )
            )
            by_code["甲-2"].status = Basin.STATUS_REELING
        if "乙-2" in by_code:
            session.add(
                BathReading(
                    basin_id=by_code["乙-2"].id,
                    water_temp_c=36.0,
                    operator="admin",
                    taken_at=now - timedelta(hours=5),
                )
            )
            session.add(
                BathReading(
                    basin_id=by_code["乙-2"].id,
                    water_temp_c=40.0,
                    operator="worker",
                    taken_at=now - timedelta(minutes=20),
                )
            )
            by_code["乙-2"].status = Basin.STATUS_REELING
        await session.commit()
