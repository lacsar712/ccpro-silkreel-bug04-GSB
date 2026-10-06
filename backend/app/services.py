"""缫丝盆门槛：标成已缫完须最近一次汤温落在 38～42℃。"""

from app.models import Basin

MIN_TEMP = 38.0
MAX_TEMP = 42.0


class RuleError(ValueError):
    pass


def latest_reading(basin: Basin):
    """时刻最晚的一条汤温记录；时刻并列时取 id 最大（最后登记）的那条。"""
    if not basin.readings:
        return None
    return max(basin.readings, key=lambda r: (r.taken_at, r.id))


def latest_temp(basin: Basin) -> float | None:
    latest = latest_reading(basin)
    return latest.water_temp_c if latest else None


def assert_can_set_status(basin: Basin, new_status: str) -> None:
    allowed = {Basin.STATUS_SOAKING, Basin.STATUS_REELING, Basin.STATUS_REELED}
    if new_status not in allowed:
        raise RuleError(f"无效状态：{new_status}")
    if new_status != Basin.STATUS_REELED:
        return
    temp = latest_temp(basin)
    if temp is None:
        raise RuleError("该盆尚无汤温记录，不能标已缫完")
    if temp < MIN_TEMP or temp > MAX_TEMP:
        raise RuleError(
            f"最近汤温 {temp}℃ 不在 {MIN_TEMP:.0f}～{MAX_TEMP:.0f}℃，不能标已缫完"
        )
