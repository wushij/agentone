"""tests/test_skills.py — Skill 测试"""

import pytest

from app.skills.calc import CalcSkill
from app.skills.search import SearchSkill
from app.skills.summarize import SummarizeSkill
from app.skills.code import CodeSkill
from app.skills.translate import TranslateSkill
from app.skills.rag import RagSkill


class TestSkills:
    @pytest.mark.asyncio
    async def test_calc_skill(self):
        skill = CalcSkill()
        result = await skill.execute(expression="2 + 3")
        assert "5" in result.output

    @pytest.mark.asyncio
    async def test_search_skill(self):
        skill = SearchSkill()
        result = await skill.execute(query="test")
        assert "test" in result.output

    @pytest.mark.asyncio
    async def test_all_skills_have_name(self):
        skills = [CalcSkill(), SearchSkill(), SummarizeSkill(), CodeSkill(), TranslateSkill(), RagSkill()]
        for skill in skills:
            assert skill.name, f"{skill.__class__.__name__} missing name"
            assert skill.description, f"{skill.__class__.__name__} missing description"