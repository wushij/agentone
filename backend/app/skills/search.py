"""app/skills/search.py — 搜索技能"""

from typing import Any

from app.skills.base import BaseSkill, SkillResult
from app.tools.network.search import SearchTool


class SearchSkill(BaseSkill):
    name = "search"
    description = "网络搜索技能"

    async def execute(self, query: str = "", **kwargs: Any) -> SkillResult:
        result = await SearchTool().run(query=query or kwargs.get("input") or "")
        if result.error:
            return SkillResult(error=result.error)
        return SkillResult(output=result.output, metadata={"duration_ms": result.duration_ms})