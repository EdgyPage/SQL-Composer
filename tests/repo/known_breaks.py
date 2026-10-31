"""Each break of the standard (docs/agents/standards.md) known when Toolbox 8.0's ticket 01
turned its rules on, by file and rule: a ruff code, or a tree rule test_standard.py reads.

The counts may only fall. Toolbox 8.0's phase 2, the refactor, empties the list; a file it
brings to the standard leaves it. Written by hand, never regenerated to let a break in.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

# The rules test_standard.py reads from the code tree; every other key below is a ruff code.
TREE_RULES = frozenset({"long body", "chained conditional", "next with a default",
                        "dense comprehension", "walrus", "lambda", "private name twice"})

KNOWN_BREAKS: dict[str, dict[str, int]] = {
    "sqlglot_composer/__init__.py": {"E501": 1},
    "sqlglot_composer/comparisons.py": {
        "E501": 7, "dense comprehension": 5, "next with a default": 2, "private name twice": 1},
    "sqlglot_composer/example_database.py": {"E501": 1, "dense comprehension": 2, "lambda": 1},
    "sqlglot_composer/lineage.py": {
        "E501": 28, "chained conditional": 2, "dense comprehension": 10, "lambda": 2,
        "next with a default": 1},
    "sqlglot_composer/running.py": {
        "E501": 3, "dense comprehension": 3, "next with a default": 1, "private name twice": 1},
    "tests/conftest.py": {"E501": 1},
    "tests/escaping_cases.py": {"E501": 2},
    "tests/hive_corpus_cases.py": {"E501": 10},
    "tests/hive_literals.py": {"E501": 1},
    "tests/offline_trap.py": {"E501": 1},
    "tests/repo/test_code_audit.py": {"E501": 1},
    "tests/repo/test_dead_code.py": {"E501": 2},
    "tests/repo/test_export_clean.py": {"E501": 10},
    "tests/repo/test_hooks.py": {"E501": 3},
    "tests/repo/test_levels.py": {"PLR0911": 1},
    "tests/repo/test_offline_hook.py": {"E501": 9},
    "tests/repo/test_offline_policy.py": {"E501": 5},
    "tests/repo/test_pointers.py": {"E501": 1},
    "tests/repo/test_toolbox_checks.py": {"E501": 7},
    "tests/sqlglot_checks/test_sqlglot_escaping_toolbox.py": {"E501": 4},
    "tests/sqlglot_checks/test_sqlglot_example_database.py": {"E501": 3},
    "tests/sqlglot_checks/test_sqlglot_example_database_windows.py": {"E501": 2},
    "tests/sqlglot_checks/test_sqlglot_example_gallery.py": {"E501": 1},
    "tests/sqlglot_checks/test_sqlglot_import_self_check.py": {"E501": 5},
    "tests/sqlglot_checks/test_sqlglot_statements.py": {"E501": 1},
    "tests/test_admin_log.py": {"E501": 2},
    "tests/test_admin_module.py": {"E501": 11},
    "tests/test_comparisons.py": {"E501": 3},
    "tests/test_conversion_chart.py": {"E501": 5},
    "tests/test_conversions.py": {"E501": 9},
    "tests/test_converting.py": {"E501": 34},
    "tests/test_copilot_files.py": {"E501": 1},
    "tests/test_describe.py": {"E501": 2},
    "tests/test_example_database.py": {"E501": 3},
    "tests/test_example_database_intermediate.py": {"E501": 3},
    "tests/test_example_database_kinds.py": {"E501": 3},
    "tests/test_example_gallery.py": {"E501": 5},
    "tests/test_example_projects.py": {"E501": 1},
    "tests/test_excel_eval.py": {"E501": 4},
    "tests/test_first_match_and_mapped.py": {"E501": 4},
    "tests/test_formula_workbook.py": {"E501": 2},
    "tests/test_how_tos.py": {"E501": 7},
    "tests/test_import_self_check.py": {"E501": 7},
    "tests/test_join_guards.py": {"E501": 2},
    "tests/test_joins.py": {"E501": 3},
    "tests/test_keys.py": {"E501": 6},
    "tests/test_lineage.py": {"E501": 6},
    "tests/test_misuse_refusals.py": {"E501": 4},
    "tests/test_mix_ups.py": {"E501": 2},
    "tests/test_partitions.py": {"E501": 3},
    "tests/test_placement.py": {"E501": 7},
    "tests/test_project.py": {"E501": 16},
    "tests/test_project_files.py": {"E501": 3},
    "tests/test_project_templates.py": {"E501": 3},
    "tests/test_python_steps.py": {"E501": 11},
    "tests/test_refusals.py": {"E501": 6},
    "tests/test_saved_table_storage.py": {"E501": 4},
    "tests/test_show_hive.py": {"E501": 1},
    "tests/test_stacking.py": {"E501": 3},
    "tests/test_statements.py": {"E501": 6},
    "tests/test_style_b_statements.py": {"E501": 2},
    "tests/test_tables.py": {"E501": 7},
    "tests/test_trees.py": {"E501": 1},
    "tests/test_unchecked_expressions.py": {"E501": 5},
    "tests/test_unchecked_statements.py": {"E501": 2},
    "tests/test_unpartitioned_writes.py": {"E501": 3},
    "tests/test_upgrades.py": {"E501": 14},
    "tests/test_upkeep.py": {"E501": 1},
    "tests/test_windows.py": {"E501": 9},
    "tests/test_worked_example_repeated_rows.py": {"E501": 1},
    "tests/test_worked_example_saved_table.py": {"E501": 1},
    "tools/code_audit.py": {"E501": 9, "dense comprehension": 5},
    "tools/copilot_eval.py": {
        "E501": 3, "chained conditional": 1, "dense comprehension": 5,
        "next with a default": 2},
    "tools/copilot_eval_tasks.py": {"E501": 20},
    "tools/copilot_files.py": {"E501": 3, "lambda": 1},
    "tools/example_gallery.py": {
        "E501": 15, "PLR0911": 1, "dense comprehension": 3, "lambda": 1},
    "tools/example_project.py": {"E501": 3, "dense comprehension": 1, "lambda": 4},
    "tools/excel_eval.py": {"E501": 6, "dense comprehension": 10, "lambda": 6},
    "tools/excel_eval_tasks.py": {"E501": 98},
    "tools/export_clean.py": {"E501": 11, "dense comprehension": 2},
    "tools/formula_workbook.py": {
        "E501": 14, "chained conditional": 1, "dense comprehension": 2,
        "next with a default": 1},
    "tools/formula_workbook_examples.py": {"E501": 7},
    "tools/hive_corpus.py": {"E501": 9, "dense comprehension": 1, "lambda": 1},
    "tools/how_to_page.py": {"E501": 11, "chained conditional": 1, "lambda": 4},
    "tools/merge_copilot_files.py": {"E501": 1},
    "tools/offline_policy.py": {"E501": 13, "PLR0911": 1, "dense comprehension": 2},
    "tools/toolbox_registry.py": {"E501": 2},
    "tools/usage_report.py": {"E501": 3},
    "worked_examples/how_to/01_start_a_project.py": {"E501": 6},
    "worked_examples/how_to/02_add_your_tables_references.py": {"E501": 14},
    "worked_examples/how_to/03_build_and_run_a_first_statement.py": {"E501": 11},
    "worked_examples/how_to/04_count_join_and_stay_safe.py": {"E501": 12},
    "worked_examples/how_to/05_share_building_blocks.py": {"E501": 7},
    "worked_examples/how_to/06_save_a_table.py": {"E501": 36},
    "worked_examples/how_to/07_follow_lineage.py": {"E501": 17},
    "worked_examples/how_to/08_keep_the_project_in_order.py": {"E501": 12},
    "worked_examples/how_to/09_describe_a_table_by_hand.py": {"E501": 7},
    "worked_examples/how_to/10_latest_row_of_each_group.py": {"E501": 3},
    "worked_examples/how_to/11_generate_statements_and_references.py": {"E501": 4},
    "worked_examples/how_to/12_rewrite_some_partitions.py": {"E501": 4},
    "worked_examples/how_to/13_look_things_up_as_of_a_day.py": {"E501": 3},
    "worked_examples/how_to/14_rollups_and_subtotals.py": {"E501": 4},
    "worked_examples/how_to/15_check_data_quality.py": {"E501": 4},
    "worked_examples/how_to/16_call_other_hive_functions.py": {"E501": 2},
    "worked_examples/how_to/17_look_across_rows.py": {"E501": 2},
    "worked_examples/how_to/18_review_and_test_a_change.py": {"E501": 20},
    "worked_examples/how_to/19_choose_how_a_saved_table_is_stored.py": {"E501": 7},
    "worked_examples/how_to/20_keys.py": {"E501": 8},
    "worked_examples/how_to/21_semi_anti_and_full_joins.py": {"E501": 4},
    "worked_examples/how_to/22_move_a_saved_table_to_its_own_folder.py": {"E501": 4},
    "worked_examples/how_to/23_reconcile_two_tables.py": {"E501": 2},
    "worked_examples/how_to/24_keep_reads_and_joins_fast.py": {"E501": 6},
    "worked_examples/how_to/25_declare_a_change_made_in_python.py": {"E501": 16},
    "worked_examples/how_to/26_hand_written_hive_with_your_table_references.py": {"E501": 6},
    "worked_examples/how_to/27_convert_someone_elses_hive.py": {"E501": 16},
    "worked_examples/how_to/28_upgrade_your_project_to_a_new_toolbox_version.py": {"E501": 5},
    "worked_examples/statements/groups_and_top_n.py": {"E501": 1},
    "worked_examples/statements/latest_and_top_n.py": {"E501": 1},
    "worked_examples/statements/repeated_rows.py": {"E501": 1},
    "worked_examples/statements/saved_table.py": {"E501": 1},
}



def is_tree_rule(rule: str) -> bool:
    """Whether a rule is one test_standard.py reads from the code tree."""
    return rule in TREE_RULES


def is_ruff_code(rule: str) -> bool:
    """Whether a rule is ruff's, the rules test_toolbox_checks.py runs ruff for."""
    return rule not in TREE_RULES


def counts_of_rules(breaks: Mapping[str, Mapping[str, int]], is_kind: Callable[[str], bool]
                    ) -> dict[str, dict[str, int]]:
    """`breaks`, by file, with only the rules `is_kind` picks."""
    picked: dict[str, dict[str, int]] = {}
    for path, rules in breaks.items():
        for rule, count in rules.items():
            if is_kind(rule):
                picked.setdefault(path, {})[rule] = count
    return picked


def rose_and_fell(found: Mapping[str, Mapping[str, int]], is_kind: Callable[[str], bool]
                  ) -> tuple[list[str], list[str]]:
    """Each count of the rules `is_kind` picks that rose above the list, and each that fell
    below it: one line per file and rule."""
    now_of, known_of = counts_of_rules(found, is_kind), counts_of_rules(KNOWN_BREAKS, is_kind)
    rose, fell = [], []
    for path in sorted(set(now_of) | set(known_of)):
        now, known = now_of.get(path, {}), known_of.get(path, {})
        for rule in sorted(set(now) | set(known)):
            was, is_now = known.get(rule, 0), now.get(rule, 0)
            if is_now > was:
                rose.append(f"{path}: {rule}, {was} known, {is_now} now")
            elif is_now < was:
                fell.append(f"{path}: {rule}, {was} known, {is_now} now")
    return rose, fell
