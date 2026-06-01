from src.ai.schemas import ParsedTask, SearchRewrite


def test_parsed_task_valid():
    t = ParsedTask(message="Submit report", priority=3, category="Work", due_date="2026-06-05")
    assert t.priority == 3


def test_search_rewrite_keywords():
    s = SearchRewrite(keywords=["proposal", "budget"], incomplete_only=True)
    assert "proposal" in s.keywords
