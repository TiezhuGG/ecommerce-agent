import sys
import unittest
import os
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.service import get_agent_run_detail, list_recent_agent_runs, run_agent_chat
from app.config import settings
from app.db.models import AgentRunRecord, ProductRecord
from app.db.repositories import get_repositories
from app.db.service import initialize_database, reset_db_runtime_state, session_scope
from app.faq.service import ask_faq
from app.intent.service import parse_intent
from app.llm.service import LLMServiceUnavailableError


class IntentFallbackTests(unittest.TestCase):
    def test_parse_intent_falls_back_to_local_rules(self) -> None:
        query = "帮我推荐2000元以内适合通勤和开会的蓝牙耳机，优先降噪和舒适"

        with patch(
            "app.intent.service.request_json_object",
            side_effect=LLMServiceUnavailableError("openai unavailable"),
        ):
            result = parse_intent(query)

        self.assertEqual(result.search_filters.category, "蓝牙耳机")
        self.assertEqual(result.search_filters.max_price, 2000)
        self.assertEqual(result.search_filters.keyword, "蓝牙耳机")
        self.assertIn(result.scenario, {"通勤 / 办公 / 会议", "通勤 / 办公 / 会议"})
        self.assertIn("Local rules fallback", result.provider)
        self.assertIn("预算上限：￥2000", result.applied_filters)


class FaqRetrievalTests(unittest.TestCase):
    def test_faq_citations_are_deduplicated_by_entry(self) -> None:
        with patch(
            "app.faq.service.request_text",
            side_effect=LLMServiceUnavailableError("openai unavailable"),
        ):
            result = ask_faq("支持开发票吗")

        self.assertGreaterEqual(len(result.citations), 1)
        entry_ids = [citation.entry_id for citation in result.citations]
        self.assertEqual(len(entry_ids), len(set(entry_ids)))


class AgentRuntimeTests(unittest.TestCase):
    def test_agent_shopping_route_returns_candidates_with_local_fallback(self) -> None:
        with patch(
            "app.agent.service._classify_route_with_llm",
            side_effect=LLMServiceUnavailableError("routing unavailable"),
        ), patch(
            "app.intent.service.request_json_object",
            side_effect=LLMServiceUnavailableError("intent unavailable"),
        ), patch(
            "app.agent.service.request_text",
            side_effect=LLMServiceUnavailableError("summary unavailable"),
        ):
            result = run_agent_chat("帮我推荐2000元以内适合通勤和开会的蓝牙耳机", [])

        self.assertEqual(result.route, "shopping")
        self.assertIsNotNone(result.parsed_intent)
        assert result.parsed_intent is not None
        self.assertEqual(result.parsed_intent.search_filters.category, "蓝牙耳机")
        self.assertEqual(result.parsed_intent.search_filters.max_price, 2000)
        self.assertGreater(len(result.recommended_product_ids), 0)
        self.assertIn("Sony", result.final_answer)

    def test_agent_faq_route_keeps_unique_reference_lines(self) -> None:
        with patch(
            "app.faq.service.request_text",
            side_effect=LLMServiceUnavailableError("faq unavailable"),
        ):
            result = run_agent_chat("支持开发票吗", [])

        self.assertEqual(result.route, "faq")
        self.assertIsNotNone(result.faq_result)
        assert result.faq_result is not None
        titles = [citation.title for citation in result.faq_result.citations]
        self.assertEqual(len(result.faq_result.citations), len(set(titles)))

    def test_agent_compare_route_still_returns_compare_summary(self) -> None:
        result = run_agent_chat("对比 Sony WF-1000XM5 和 Apple AirPods Pro (第 2 代)", [])

        self.assertEqual(result.route, "compare")
        self.assertIsNotNone(result.compare_result)
        self.assertIn("关键结论", result.final_answer)

    def test_agent_run_is_not_persisted_on_seed_backend(self) -> None:
        result = run_agent_chat("支持开发票吗", [])

        self.assertFalse(result.persisted)
        self.assertIsNone(result.run_id)

    def test_agent_chat_response_includes_selected_product_ids(self) -> None:
        result = run_agent_chat(
            "对比 Sony WF-1000XM5 和 Apple AirPods Pro (第 2 代)",
            ["earbuds-sony-wf1000xm5", "earbuds-apple-airpods-pro-2"],
        )

        self.assertEqual(
            result.selected_product_ids,
            ["earbuds-sony-wf1000xm5", "earbuds-apple-airpods-pro-2"],
        )

    def test_agent_run_history_is_disabled_on_seed_backend(self) -> None:
        result = list_recent_agent_runs()

        self.assertEqual(result.backend, "disabled")
        self.assertEqual(result.items, [])


class RepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_database_url = os.environ.get("DATABASE_URL")
        self.original_settings_database_url = settings.database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

    def tearDown(self) -> None:
        if self.original_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self.original_database_url
        settings.database_url = self.original_settings_database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

    def test_default_repository_backend_uses_seed_storage(self) -> None:
        os.environ.pop("DATABASE_URL", None)
        settings.database_url = ""
        get_repositories.cache_clear()
        reset_db_runtime_state()
        repositories = get_repositories()

        self.assertEqual(repositories.backend, "in-memory-seed")
        self.assertGreater(len(repositories.products.list_products()), 0)
        self.assertGreater(len(repositories.faq.list_entries()), 0)

    def test_initialize_database_returns_false_without_database_url(self) -> None:
        os.environ.pop("DATABASE_URL", None)
        settings.database_url = ""
        get_repositories.cache_clear()
        reset_db_runtime_state()
        ok, message = initialize_database()

        self.assertFalse(ok)
        self.assertTrue(
            "DATABASE_URL" in message or "SQLAlchemy" in message,
            msg=message,
        )

    def test_repository_backend_switches_to_sqlite_when_database_url_is_set(self) -> None:
        database_path = ROOT / ".tmp" / "test-runtime.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        repositories = get_repositories()

        self.assertEqual(repositories.backend, "sqlalchemy-sqlite")
        self.assertGreater(len(repositories.products.list_products()), 0)

    def test_agent_run_is_persisted_when_sqlite_backend_is_enabled(self) -> None:
        database_path = ROOT / ".tmp" / "test-agent-runs.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        result = run_agent_chat("支持开发票吗", [])

        self.assertTrue(result.persisted)
        self.assertIsNotNone(result.run_id)
        self.assertIsNotNone(AgentRunRecord)
        self.assertIsNotNone(ProductRecord)
        with session_scope() as session:
            stored = session.get(AgentRunRecord, result.run_id)
            self.assertIsNotNone(stored)
            assert stored is not None
            self.assertEqual(stored.route, "faq")
            self.assertTrue(stored.created_at)

    def test_recent_agent_runs_are_listed_when_sqlite_backend_is_enabled(self) -> None:
        database_path = ROOT / ".tmp" / "test-agent-runs.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        run_agent_chat("支持开发票吗", [])
        history = list_recent_agent_runs(limit=5)

        self.assertEqual(history.backend, "sqlalchemy-sqlite")
        self.assertGreaterEqual(len(history.items), 1)
        self.assertEqual(history.items[0].route, "faq")
        self.assertGreaterEqual(history.items[0].tool_call_count, 1)

    def test_agent_run_detail_is_available_when_sqlite_backend_is_enabled(self) -> None:
        database_path = ROOT / ".tmp" / "test-agent-run-detail.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        result = run_agent_chat("支持开发票吗", [])
        assert result.run_id is not None

        detail = get_agent_run_detail(result.run_id)

        self.assertEqual(detail.run_id, result.run_id)
        self.assertEqual(detail.route, "faq")
        self.assertTrue(detail.persisted)
        self.assertGreaterEqual(len(detail.tool_calls), 1)


if __name__ == "__main__":
    unittest.main()
