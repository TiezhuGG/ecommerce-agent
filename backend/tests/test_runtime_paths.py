import sys
import unittest
import os
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.service import (
    get_agent_precheck,
    get_agent_run_detail,
    get_agent_thread_detail,
    list_recent_agent_runs,
    list_recent_agent_threads,
    run_agent_chat,
)
from app.config import settings
from app.db.models import AgentRunRecord, FaqEntryRecord, ProductRecord
from app.db.repositories import get_database_runtime_info, get_repositories
from app.db.runtime_verifier import run_database_smoke_checks
from app.db.service import (
    initialize_database,
    normalize_database_url,
    reset_db_runtime_state,
    seed_database_if_empty,
    session_scope,
)
from app.catalog.service import (
    create_product,
    delete_product,
    export_products,
    infer_product_ids_from_text,
    import_products,
    list_products_admin,
    search_products,
    update_product,
)
from app.faq.service import (
    ask_faq,
    create_faq_entry,
    delete_faq_entry,
    export_faq_entries,
    import_faq_entries,
    list_faq_entries_admin,
    update_faq_entry,
)
from app.schemas.agent import AgentConversationTurn
from app.schemas.faq import FaqEntryImportItem, FaqEntryImportRequest, FaqEntryUpsertRequest
from app.schemas.products import ProductImportItem, ProductImportRequest, ProductUpsertRequest
from app.intent.service import parse_intent
from app.llm.service import LLMServiceUnavailableError
from app.main import app


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

    def test_seed_faq_aliases_match_common_question_variants(self) -> None:
        with patch(
            "app.faq.service.request_text",
            side_effect=LLMServiceUnavailableError("openai unavailable"),
        ):
            result = ask_faq("发票怎么开")

        self.assertIsNotNone(result.matched_entry)
        assert result.matched_entry is not None
        self.assertEqual(result.matched_entry.id, "kb-invoice-general")
        self.assertTrue(any(signal.kind == "question_alias" for signal in result.match_signals))

    def test_seed_faq_aliases_cover_multiple_high_frequency_variants(self) -> None:
        scenarios = [
            ("保修多久", "kb-warranty-general"),
            ("退货运费谁出", "kb-return-freight"),
            ("收到商品后多久内可以退货", "kb-return-time-limit"),
            ("发票抬头写错了还能改吗", "kb-invoice-modify"),
            ("一个订单能分开发票吗", "kb-invoice-separate"),
            ("保修需要准备什么", "kb-warranty-serial-number"),
            ("下单后还能取消吗", "kb-order-cancel"),
        ]

        for question, expected_id in scenarios:
            with self.subTest(question=question), patch(
                "app.faq.service.request_text",
                side_effect=LLMServiceUnavailableError("openai unavailable"),
            ):
                result = ask_faq(question)

            self.assertIsNotNone(result.matched_entry)
            assert result.matched_entry is not None
            self.assertEqual(result.matched_entry.id, expected_id)

    def test_faq_no_match_returns_empty_match_signals(self) -> None:
        with patch(
            "app.faq.service.request_text",
            side_effect=LLMServiceUnavailableError("openai unavailable"),
        ):
            result = ask_faq("这家店老板今天心情怎么样")

        self.assertIsNone(result.matched_entry)
        self.assertEqual(result.match_signals, [])


class AgentRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_database_url = os.environ.get("DATABASE_URL")
        self.original_settings_database_url = settings.database_url
        os.environ.pop("DATABASE_URL", None)
        settings.database_url = ""
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
        self.assertEqual(result.providers.retrieval_provider, "knowledge-rag-v1-local-retrieval")
        self.assertTrue(result.providers.answer_provider)

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
        self.assertTrue(result.providers.route_provider)

    def test_agent_run_history_is_disabled_on_seed_backend(self) -> None:
        result = list_recent_agent_runs()

        self.assertEqual(result.backend, "disabled")
        self.assertEqual(result.items, [])

    def test_agent_thread_history_is_disabled_on_seed_backend(self) -> None:
        result = list_recent_agent_threads()

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

    def test_normalize_database_url_resolves_relative_sqlite_path_from_backend_dir(self) -> None:
        normalized = normalize_database_url("sqlite:///./.tmp/ecommerce-agent-dev.db")

        self.assertTrue(normalized.startswith("sqlite:///"))
        self.assertIn("/backend/.tmp/ecommerce-agent-dev.db", normalized)

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

    def test_database_runtime_info_reports_seed_only_when_database_url_is_missing(self) -> None:
        os.environ.pop("DATABASE_URL", None)
        settings.database_url = ""
        get_repositories.cache_clear()
        reset_db_runtime_state()

        info = get_database_runtime_info()

        self.assertEqual(info.configured_backend, "not-configured")
        self.assertEqual(info.runtime_backend, "in-memory-seed")
        self.assertEqual(info.status, "seed-only")
        self.assertFalse(info.persistence_enabled)
        self.assertIn("不会保留", info.message)

    def test_database_runtime_info_reports_ready_when_sqlite_is_available(self) -> None:
        database_path = ROOT / ".tmp" / "test-runtime-info-ready.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        info = get_database_runtime_info()

        self.assertEqual(info.configured_backend, "sqlite")
        self.assertEqual(info.runtime_backend, "sqlalchemy-sqlite")
        self.assertEqual(info.status, "ready")
        self.assertTrue(info.persistence_enabled)
        self.assertIn("SQLite", info.message)

    def test_agent_precheck_includes_database_runtime_fields_for_sqlite(self) -> None:
        database_path = ROOT / ".tmp" / "test-agent-precheck-sqlite.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        precheck = get_agent_precheck()

        self.assertEqual(precheck.data_backend, "sqlalchemy-sqlite")
        self.assertEqual(precheck.database_configured_backend, "sqlite")
        self.assertEqual(precheck.database_runtime_status, "ready")
        self.assertTrue(precheck.database_persistence_enabled)
        self.assertIn("SQLite", precheck.database_runtime_message)
        self.assertTrue(any("PostgreSQL" in warning for warning in precheck.warnings))

    def test_search_products_supports_alias_and_model_shorthand_matching(self) -> None:
        results = search_products(keyword="WF1000XM5")
        self.assertTrue(any(item.id == "earbuds-sony-wf1000xm5" for item in results.items))

        compare_results = search_products(keyword="AirPods Pro 2")
        self.assertTrue(any(item.id == "earbuds-apple-airpods-pro-2" for item in compare_results.items))

    def test_infer_product_ids_from_text_supports_alias_and_model_shorthand(self) -> None:
        matched = infer_product_ids_from_text("帮我对比 WF1000XM5 和 AirPods Pro 2，主要看通勤。")

        self.assertIn("earbuds-sony-wf1000xm5", matched)
        self.assertIn("earbuds-apple-airpods-pro-2", matched)

    def test_database_smoke_verifier_passes_on_sqlite_backend(self) -> None:
        database_path = ROOT / ".tmp" / "test-database-smoke.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        report = run_database_smoke_checks(expect_backend="sqlite")

        self.assertEqual(report.configured_backend, "sqlite")
        self.assertEqual(report.runtime_backend, "sqlalchemy-sqlite")
        self.assertEqual(report.runtime_status, "ready")
        self.assertTrue(report.persistence_enabled)
        self.assertGreater(report.product_total, 0)
        self.assertGreater(report.faq_total, 0)
        self.assertTrue(report.created_product_id)
        self.assertTrue(report.created_faq_entry_id)
        self.assertTrue(report.persisted_run_id)

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
        self.assertTrue(result.thread_id.startswith("thread-"))
        self.assertIsNotNone(AgentRunRecord)
        self.assertIsNotNone(ProductRecord)
        with session_scope() as session:
            stored = session.get(AgentRunRecord, result.run_id)
            self.assertIsNotNone(stored)
            assert stored is not None
            self.assertEqual(stored.route, "faq")
            self.assertTrue(stored.created_at)
            self.assertEqual(stored.thread_id, result.thread_id)

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
        self.assertTrue(history.items[0].thread_id)

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
        self.assertEqual(detail.providers.retrieval_provider, "knowledge-rag-v1-local-retrieval")
        self.assertEqual(detail.thread_id, result.thread_id)

    def test_agent_thread_can_be_continued_and_restored_from_history(self) -> None:
        database_path = ROOT / ".tmp" / "test-agent-thread-history.db"
        database_path.parent.mkdir(parents=True, exist_ok=True)
        if database_path.exists():
            database_path.unlink()
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        first = run_agent_chat("帮我推荐 2000 元内适合通勤的蓝牙耳机", [])
        self.assertTrue(first.persisted)
        self.assertTrue(first.thread_id.startswith("thread-"))

        second = run_agent_chat(
            "继续刚才那组里，更适合苹果生态的是哪个？",
            [],
            [
                AgentConversationTurn(
                    user_message=first.message,
                    agent_answer=first.final_answer,
                    route=first.route,
                    selected_product_ids=first.selected_product_ids,
                    recommended_product_ids=first.recommended_product_ids,
                )
            ],
            first.thread_id,
        )

        self.assertTrue(second.persisted)
        self.assertEqual(second.thread_id, first.thread_id)
        self.assertIsNotNone(second.run_id)

        history = list_recent_agent_runs(limit=10)
        matching = [item for item in history.items if item.run_id == second.run_id]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].thread_id, first.thread_id)

        assert second.run_id is not None
        detail = get_agent_run_detail(second.run_id)
        self.assertEqual(detail.thread_id, first.thread_id)
        self.assertEqual(len(detail.conversation_context), 1)
        self.assertEqual(detail.conversation_context[0].user_message, first.message)

    def test_agent_can_rebuild_conversation_context_from_thread_history(self) -> None:
        database_path = ROOT / ".tmp" / "test-agent-thread-rebuild-context.db"
        database_path.parent.mkdir(parents=True, exist_ok=True)
        if database_path.exists():
            database_path.unlink()
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        first = run_agent_chat("帮我推荐适合通勤的蓝牙耳机", [])
        self.assertTrue(first.persisted)

        second = run_agent_chat(
            "继续刚才那组里，更适合苹果生态的是哪个？",
            [],
            [],
            first.thread_id,
        )

        self.assertEqual(second.thread_id, first.thread_id)
        self.assertEqual(len(second.conversation_context), 1)
        self.assertEqual(second.conversation_context[0].user_message, first.message)
        self.assertIsNotNone(second.thread_state)
        assert second.thread_state is not None
        self.assertGreaterEqual(len(second.thread_state.candidate_product_ids), 1)
        assert second.run_id is not None

        detail = get_agent_run_detail(second.run_id)
        self.assertEqual(len(detail.conversation_context), 1)
        self.assertEqual(detail.conversation_context[0].user_message, first.message)
        self.assertIsNotNone(detail.thread_state)

    def test_recent_agent_threads_are_grouped_when_sqlite_backend_is_enabled(self) -> None:
        database_path = ROOT / ".tmp" / "test-agent-thread-list.db"
        database_path.parent.mkdir(parents=True, exist_ok=True)
        if database_path.exists():
            database_path.unlink()
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        first = run_agent_chat("支持开发票吗", [])
        run_agent_chat(
            "那电子发票多久开出来？",
            [],
            [
                AgentConversationTurn(
                    user_message=first.message,
                    agent_answer=first.final_answer,
                    route=first.route,
                    selected_product_ids=first.selected_product_ids,
                    recommended_product_ids=first.recommended_product_ids,
                )
            ],
            first.thread_id,
        )
        third = run_agent_chat("对比 Sony WF-1000XM5 和 Apple AirPods Pro 2", [])

        history = list_recent_agent_threads(limit=10)

        self.assertEqual(history.backend, "sqlalchemy-sqlite")
        self.assertEqual(len(history.items), 2)
        self.assertEqual(history.items[0].thread_id, third.thread_id)
        self.assertEqual(history.items[0].run_count, 1)
        self.assertEqual(history.items[1].thread_id, first.thread_id)
        self.assertEqual(history.items[1].run_count, 2)
        self.assertIn("faq", history.items[1].routes)

    def test_agent_thread_detail_returns_timeline_when_sqlite_backend_is_enabled(self) -> None:
        database_path = ROOT / ".tmp" / "test-agent-thread-detail.db"
        database_path.parent.mkdir(parents=True, exist_ok=True)
        if database_path.exists():
            database_path.unlink()
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        first = run_agent_chat("帮我推荐适合通勤的蓝牙耳机", [])
        second = run_agent_chat(
            "继续刚才那组里，预算放宽到 2500 再看",
            [],
            [
                AgentConversationTurn(
                    user_message=first.message,
                    agent_answer=first.final_answer,
                    route=first.route,
                    selected_product_ids=first.selected_product_ids,
                    recommended_product_ids=first.recommended_product_ids,
                )
            ],
            first.thread_id,
        )

        detail = get_agent_thread_detail(first.thread_id)

        self.assertEqual(detail.thread_id, first.thread_id)
        self.assertEqual(detail.latest_run_id, second.run_id)
        self.assertEqual(detail.run_count, 2)
        self.assertEqual(len(detail.items), 2)
        self.assertEqual(detail.items[0].run_id, second.run_id)
        self.assertEqual(detail.items[1].run_id, first.run_id)
        self.assertIn("shopping", detail.routes)
        self.assertIsNotNone(detail.thread_state)

    def test_compare_can_fallback_to_thread_state_candidates(self) -> None:
        database_path = ROOT / ".tmp" / "test-agent-thread-state-compare.db"
        database_path.parent.mkdir(parents=True, exist_ok=True)
        if database_path.exists():
            database_path.unlink()
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        first = run_agent_chat("帮我推荐适合通勤的蓝牙耳机", [])
        self.assertTrue(first.recommended_product_ids)

        current_thread_id = first.thread_id
        for question in [
            "支持开发票吗",
            "电子发票多久开",
            "退货规则是什么",
            "保修多久",
        ]:
            follow_up = run_agent_chat(question, [], [], current_thread_id)
            current_thread_id = follow_up.thread_id

        compare_result = run_agent_chat("继续比较刚才那两款，哪个更适合苹果生态？", [], [], current_thread_id)

        self.assertEqual(compare_result.route, "compare")
        self.assertIsNotNone(compare_result.compare_result)
        self.assertIsNotNone(compare_result.thread_state)
        assert compare_result.thread_state is not None
        self.assertGreaterEqual(len(compare_result.thread_state.candidate_product_ids), 2)

    def test_seed_database_inserts_missing_faq_entries_into_existing_sqlite(self) -> None:
        database_path = ROOT / ".tmp" / "test-seed-sync.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        ok, _ = initialize_database()
        self.assertTrue(ok)
        assert FaqEntryRecord is not None

        with session_scope() as session:
            row = session.get(FaqEntryRecord, "kb-price-protect")
            if row is not None:
                session.delete(row)
                session.commit()

        seed_database_if_empty()

        with session_scope() as session:
            restored = session.get(FaqEntryRecord, "kb-price-protect")
            self.assertIsNotNone(restored)

    def test_faq_admin_crud_works_on_sqlite_backend(self) -> None:
        database_path = ROOT / ".tmp" / "test-faq-admin.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        ok, _ = initialize_database()
        self.assertTrue(ok)

        created = create_faq_entry(
            FaqEntryUpsertRequest(
                topic="活动",
                question="测试条目可以新增吗？",
                answer="可以，这是一条测试知识文档。",
                source_label="测试来源",
                keywords=["测试", "新增"],
                body="这条文档用于验证 SQLite 下的知识库管理 CRUD。",
            )
        )

        listed = list_faq_entries_admin()
        self.assertTrue(any(item.id == created.id for item in listed.items))

        updated = update_faq_entry(
            created.id,
            FaqEntryUpsertRequest(
                topic="活动",
                question="测试条目可以更新吗？",
                answer="可以，这条测试文档已经更新。",
                source_label="测试来源",
                keywords=["测试", "更新"],
                body="更新后的正文。",
            ),
        )
        self.assertEqual(updated.question, "测试条目可以更新吗？")

        deleted = delete_faq_entry(created.id)
        self.assertTrue(deleted.deleted)

        listed_after_delete = list_faq_entries_admin()
        self.assertFalse(any(item.id == created.id for item in listed_after_delete.items))

    def test_faq_admin_import_export_works_on_sqlite_backend(self) -> None:
        database_path = ROOT / ".tmp" / "test-faq-import-export.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        ok, _ = initialize_database()
        self.assertTrue(ok)

        exported = export_faq_entries()
        self.assertGreater(len(exported.items), 0)

        target = exported.items[0]
        imported = import_faq_entries(
            FaqEntryImportRequest(
                mode="upsert",
                items=[
                    FaqEntryImportItem(
                        id=target.id,
                        topic=target.topic,
                        question=target.question,
                        answer="导入后的测试答案",
                        source_label=target.source_label,
                        keywords=target.keywords,
                        body=target.body,
                    )
                ],
            )
        )
        self.assertEqual(imported.updated_count, 1)

        listed = list_faq_entries_admin()
        updated = next(item for item in listed.items if item.id == target.id)
        self.assertEqual(updated.answer, "导入后的测试答案")

    def test_faq_aliases_are_persisted_and_retrievable_on_sqlite_backend(self) -> None:
        database_path = ROOT / ".tmp" / "test-faq-aliases.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        ok, _ = initialize_database()
        self.assertTrue(ok)

        created = create_faq_entry(
            FaqEntryUpsertRequest(
                topic="Invoice",
                question="Can I get an invoice?",
                answer="Yes. You can apply for an invoice after placing the order.",
                source_label="Alias Test",
                question_aliases=["How do I issue an invoice?", "Can you open an invoice?"],
                keywords=["invoice", "billing"],
                body="Alias persistence test body.",
            )
        )
        self.assertIn("How do I issue an invoice?", created.question_aliases)

        updated = update_faq_entry(
            created.id,
            FaqEntryUpsertRequest(
                topic="Invoice",
                question="Can I get an invoice?",
                answer="Yes. Invoice requests can be submitted from the order detail page.",
                source_label="Alias Test",
                question_aliases=["How do I issue an invoice?", "Invoice application process"],
                keywords=["invoice", "billing"],
                body="Alias persistence test body updated.",
            ),
        )
        self.assertIn("Invoice application process", updated.question_aliases)

        result = ask_faq("How do I issue an invoice?")
        self.assertIsNotNone(result.matched_entry)
        assert result.matched_entry is not None
        self.assertEqual(result.matched_entry.id, created.id)
        self.assertEqual(result.source_label, "Alias Test")

        imported = import_faq_entries(
            FaqEntryImportRequest(
                mode="upsert",
                items=[
                    FaqEntryImportItem(
                        id=created.id,
                        topic="Invoice",
                        question="Can I get an invoice?",
                        answer="Imported answer for alias regression test.",
                        source_label="Alias Test",
                        question_aliases=["Invoice application process", "Need invoice after purchase"],
                        keywords=["invoice", "billing"],
                        body="Imported alias persistence test body.",
                    )
                ],
            )
        )
        self.assertEqual(imported.updated_count, 1)

        listed = list_faq_entries_admin()
        imported_entry = next(item for item in listed.items if item.id == created.id)
        self.assertIn("Need invoice after purchase", imported_entry.question_aliases)

    def test_product_admin_crud_works_on_sqlite_backend(self) -> None:
        database_path = ROOT / ".tmp" / "test-product-admin.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        ok, _ = initialize_database()
        self.assertTrue(ok)

        created = create_product(
            ProductUpsertRequest(
                name="Test Product",
                category="Headphones",
                brand="Demo",
                price=999,
                price_note="Display price",
                summary="Created during sqlite CRUD test.",
                scenario="Commute / Office",
                aliases=["Demo One", "Test Product 1"],
                tags=["demo", "noise cancelling"],
                specs=["Bluetooth 5.4", "40-hour battery"],
                official_url="https://example.com/test-product",
            )
        )

        listed = list_products_admin()
        self.assertTrue(any(item.id == created.id for item in listed.items))

        updated = update_product(
            created.id,
            ProductUpsertRequest(
                name="Test Product Updated",
                category="Headphones",
                brand="Demo",
                price=1099,
                price_note="Updated display price",
                summary="Updated during sqlite CRUD test.",
                scenario="Commute / Hybrid work",
                aliases=["Demo Pro", "Test Product 2"],
                tags=["demo", "long battery"],
                specs=["Bluetooth 5.4", "42-hour battery"],
                official_url="https://example.com/test-product-updated",
            ),
        )
        self.assertEqual(updated.name, "Test Product Updated")
        self.assertIn("Demo Pro", updated.aliases)

        deleted = delete_product(created.id)
        self.assertTrue(deleted.deleted)

        listed_after_delete = list_products_admin()
        self.assertFalse(any(item.id == created.id for item in listed_after_delete.items))

    def test_product_admin_import_export_works_on_sqlite_backend(self) -> None:
        database_path = ROOT / ".tmp" / "test-product-import-export.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        get_repositories.cache_clear()
        reset_db_runtime_state()

        ok, _ = initialize_database()
        self.assertTrue(ok)

        exported = export_products()
        self.assertGreater(len(exported.items), 0)

        target = exported.items[0]
        imported = import_products(
            ProductImportRequest(
                mode="upsert",
                items=[
                    ProductImportItem(
                        id=target.id,
                        name=target.name,
                        category=target.category,
                        brand=target.brand,
                        price=target.price + 100,
                        price_note=target.price_note,
                        summary="Updated from import test.",
                        scenario=target.scenario,
                        aliases=[*target.aliases, "Import Alias"],
                        tags=target.tags,
                        specs=target.specs,
                        official_url=target.official_url,
                    )
                ],
            )
        )
        self.assertEqual(imported.updated_count, 1)

        listed = list_products_admin()
        updated = next(item for item in listed.items if item.id == target.id)
        self.assertEqual(updated.summary, "Updated from import test.")
        self.assertIn("Import Alias", updated.aliases)


class AdminApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_database_url = os.environ.get("DATABASE_URL")
        self.original_settings_database_url = settings.database_url
        self.original_admin_access_code = settings.admin_access_code
        get_repositories.cache_clear()
        reset_db_runtime_state()

    def tearDown(self) -> None:
        if self.original_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self.original_database_url
        settings.database_url = self.original_settings_database_url
        settings.admin_access_code = self.original_admin_access_code
        get_repositories.cache_clear()
        reset_db_runtime_state()

    def test_admin_database_smoke_check_endpoint_returns_report_on_sqlite(self) -> None:
        database_path = ROOT / ".tmp" / "test-admin-smoke-endpoint.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["DATABASE_URL"] = database_url
        settings.database_url = database_url
        settings.admin_access_code = ""
        get_repositories.cache_clear()
        reset_db_runtime_state()

        with TestClient(app) as client:
            response = client.post("/admin/database/smoke-check?expect_backend=sqlite")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["configured_backend"], "sqlite")
        self.assertEqual(data["runtime_backend"], "sqlalchemy-sqlite")
        self.assertEqual(data["runtime_status"], "ready")
        self.assertTrue(data["persistence_enabled"])
        self.assertTrue(data["created_product_id"])
        self.assertTrue(data["created_faq_entry_id"])
        self.assertTrue(data["persisted_run_id"])

    def test_admin_database_smoke_check_endpoint_rejects_invalid_expect_backend(self) -> None:
        settings.admin_access_code = ""

        with TestClient(app) as client:
            response = client.post("/admin/database/smoke-check?expect_backend=mysql")

        self.assertEqual(response.status_code, 400)
        self.assertIn("sqlite", response.json()["detail"])

    def test_admin_database_smoke_check_endpoint_requires_access_code_when_enabled(self) -> None:
        settings.admin_access_code = "secret-code"

        with TestClient(app) as client:
            response = client.post("/admin/database/smoke-check")

        self.assertEqual(response.status_code, 401)
        self.assertIn("管理员访问码", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
