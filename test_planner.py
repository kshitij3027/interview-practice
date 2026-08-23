import csv
import io
import random
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from planner import Dependency, Service, load_dependencies, load_services, main, plan_recovery
from recovery import RecoveryPlanner


ROOT = Path(__file__).parent
SERVICES = ROOT / "fixtures" / "services.csv"
DEPENDENCIES = ROOT / "fixtures" / "dependencies.csv"


def fixture_planner(policy: str = "single_component") -> RecoveryPlanner:
    return RecoveryPlanner.from_paths(SERVICES, DEPENDENCIES, policy)


def names(planner: RecoveryPlanner, nodes: set[int]) -> set[str]:
    return {planner.table.ids[node] for node in nodes}


class StaticIndexTests(unittest.TestCase):
    def test_duplicate_edge_collapsed(self):
        planner = fixture_planner()
        checkout = planner.table.index["checkout"]
        pricing = planner.table.index["pricing"]
        self.assertEqual(list(planner.deps.neighbours(checkout)).count(pricing), 1)

    def test_soft_edges_absent_both_directions(self):
        planner = fixture_planner()
        orders = planner.table.index["orders"]
        notifications = planner.table.index["notifications"]
        self.assertNotIn(notifications, planner.dependents.neighbours(orders))
        self.assertNotIn(orders, planner.deps.neighbours(notifications))

    def test_malformed_rows_counted_once(self):
        self.assertEqual(fixture_planner().ignored_dependency_rows, 2)

    def test_malformed_soft_row_counted_and_unknown_kind_ignored(self):
        services = {"a": Service("a", 1, "r"), "b": Service("b", 1, "r")}
        dependencies = [Dependency("ghost", "a", "soft"), Dependency("a", "b", "weak")]
        planner = RecoveryPlanner.from_loaded(services, dependencies)
        self.assertEqual(planner.ignored_dependency_rows, 1)
        self.assertEqual(list(planner.deps.neighbours(planner.table.index["a"])), [])

    def test_csr_invariants_and_transpose(self):
        planner = fixture_planner()
        for graph in (planner.deps, planner.dependents):
            self.assertEqual(graph.offsets[0], 0)
            self.assertEqual(graph.offsets[-1], len(graph.targets))
            self.assertEqual(list(graph.offsets), sorted(graph.offsets))
            for node in range(len(planner.table.ids)):
                neighbours = list(graph.neighbours(node))
                self.assertEqual(neighbours, sorted(set(neighbours)))
        forward = {
            (source, target)
            for source in range(len(planner.table.ids))
            for target in planner.deps.neighbours(source)
        }
        reverse = {
            (source, target)
            for target in range(len(planner.table.ids))
            for source in planner.dependents.neighbours(target)
        }
        self.assertEqual(forward, reverse)

    def test_from_paths_matches_from_loaded(self):
        streamed = fixture_planner()
        loaded = RecoveryPlanner.from_loaded(
            load_services(SERVICES), load_dependencies(DEPENDENCIES)
        )
        self.assertEqual(streamed.table, loaded.table)
        self.assertEqual(streamed.deps, loaded.deps)
        self.assertEqual(streamed.dependents, loaded.dependents)

    def test_duplicate_service_overwrites_slot_and_self_edge_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            service_path = Path(tmp) / "services.csv"
            dependency_path = Path(tmp) / "dependencies.csv"
            service_path.write_text(
                "service_id,tier,region\na,2,east\na,0,west\n", encoding="utf-8"
            )
            dependency_path.write_text(
                "service_id,depends_on,kind\na,a,hard\n", encoding="utf-8"
            )
            planner = RecoveryPlanner.from_paths(service_path, dependency_path)
        self.assertEqual(planner.table.ids, ["a"])
        self.assertEqual(planner.table.tier[0], 0)
        self.assertEqual(planner.table.region_of[0], planner.table.region_ids["west"])
        self.assertEqual(list(planner.deps.neighbours(0)), [0])


class AffectedSetTests(unittest.TestCase):
    def test_identity_and_soft_dependent(self):
        planner = fixture_planner()
        affected, unknown = planner._affected(["identity"], None)
        self.assertEqual(
            names(planner, affected),
            {"identity", "profile", "checkout", "fraud", "orders", "payments", "analytics"},
        )
        self.assertNotIn("notifications", names(planner, affected))
        self.assertEqual(unknown, [])

    def test_region_unknowns_duplicates_cycle_and_empty(self):
        planner = fixture_planner()
        affected, _ = planner._affected(["inventory"], "us-west")
        self.assertEqual(names(planner, affected), {"inventory", "shipping", "routing", "returns"})
        once = planner._affected(["identity"], None)[0]
        twice = planner._affected(["identity", "identity"], None)[0]
        self.assertEqual(once, twice)
        cycle, _ = planner._affected(["legacy-sync"], None)
        self.assertEqual(names(planner, cycle), {"legacy-sync", "partner-feed"})
        self.assertEqual(planner._affected([], None), (set(), []))
        self.assertEqual(planner._affected(["x", "x", "y"], None), (set(), ["x", "y"]))
        self.assertEqual(planner._affected(["identity"], "unknown"), (set(), []))

    def test_region_filters_output_after_full_propagation(self):
        services = {
            "east-a": Service("east-a", 1, "east"),
            "west-b": Service("west-b", 1, "west"),
            "east-c": Service("east-c", 1, "east"),
        }
        dependencies = [
            Dependency("east-a", "west-b", "hard"),
            Dependency("west-b", "east-c", "hard"),
        ]
        planner = RecoveryPlanner.from_loaded(services, dependencies)
        affected, _ = planner._affected(["east-c"], "east")
        self.assertEqual(names(planner, affected), {"east-a", "east-c"})

    def test_out_of_region_seed_propagates(self):
        services = {
            "east-a": Service("east-a", 1, "east"),
            "west-b": Service("west-b", 1, "west"),
        }
        dependencies = [Dependency("east-a", "west-b", "hard")]
        planner = RecoveryPlanner.from_loaded(services, dependencies)

        # Region scopes output, not propagation; seed filtering would hide east-a.
        affected, _ = planner._affected(["west-b"], "east")
        self.assertEqual(names(planner, affected), {"east-a"})


class WavePlanningTests(unittest.TestCase):
    def test_cli_builds_static_graph_once_for_all_incidents(self):
        fake_planner = Mock()
        fake_planner.plan.side_effect = [
            {"incident_id": "one", "waves": [], "service_count": 0},
            {"incident_id": "two", "waves": [], "service_count": 0},
        ]
        incidents = [
            {"incident_id": "one", "failed_services": []},
            {"incident_id": "two", "failed_services": []},
        ]
        argv = [
            "planner.py",
            "--services",
            "services.csv",
            "--dependencies",
            "dependencies.csv",
            "--incidents",
            "incidents.jsonl",
        ]
        with (
            patch.object(sys, "argv", argv),
            patch("planner.RecoveryPlanner.from_paths", return_value=fake_planner) as build,
            patch("planner.load_incidents", return_value=iter(incidents)),
            patch("sys.stdout", new_callable=io.StringIO),
        ):
            self.assertEqual(main(), 0)
        build.assert_called_once_with("services.csv", "dependencies.csv")
        self.assertEqual(fake_planner.plan.call_count, 2)

    def test_identity_golden_and_back_compatibility_wrapper(self):
        incident = {"incident_id": "inc-identity", "failed_services": ["identity"]}
        expected_waves = [
            ["identity"],
            ["checkout"],
            ["fraud"],
            ["orders"],
            ["payments"],
            ["profile"],
            ["analytics"],
        ]
        result = fixture_planner().plan(incident)
        self.assertEqual(result["waves"], expected_waves)
        self.assertEqual(result["service_count"], 7)
        self.assertEqual(result["ignored_dependency_rows"], 2)
        self.assertEqual(
            plan_recovery(load_services(SERVICES), load_dependencies(DEPENDENCIES), incident),
            result,
        )

    def test_cycles_share_a_wave_and_self_loop_is_placed_once(self):
        planner = fixture_planner()
        loop = planner.plan({"incident_id": "loop", "failed_services": ["legacy-sync"]})
        self.assertEqual(loop["waves"], [["legacy-sync", "partner-feed"]])
        search = planner.plan({"incident_id": "search", "failed_services": ["catalog"]})
        flattened = sum(search["waves"], [])
        self.assertEqual(flattened.count("search"), 1)

    def test_dependency_order_sorting_counts_and_unknowns(self):
        planner = fixture_planner()
        incidents = [
            {"incident_id": "identity", "failed_services": ["identity"]},
            {"incident_id": "west", "failed_services": ["inventory"], "region": "us-west"},
            {"incident_id": "loop", "failed_services": ["legacy-sync"]},
            {"incident_id": "mixed", "failed_services": ["catalog", "does-not-exist"]},
        ]
        for incident in incidents:
            result = planner.plan(incident)
            flattened = sum(result["waves"], [])
            self.assertEqual(result["service_count"], len(flattened))
            self.assertEqual(len(flattened), len(set(flattened)))
            self.assertTrue(all(wave == sorted(wave) for wave in result["waves"]))
            wave_of = {service_id: wave for wave, ids in enumerate(result["waves"]) for service_id in ids}
            for source_id, source in planner.table.index.items():
                for target in planner.deps.neighbours(source):
                    target_id = planner.table.ids[target]
                    if source_id in wave_of and target_id in wave_of and wave_of[source_id] != wave_of[target_id]:
                        self.assertLess(wave_of[target_id], wave_of[source_id])
        self.assertEqual(planner.plan(incidents[-1])["unknown_services"], ["does-not-exist"])

    def test_tier_controls_single_component_but_not_maximal_policy(self):
        services = load_services(SERVICES)
        dependencies = load_dependencies(DEPENDENCIES)
        incident = {"incident_id": "i", "failed_services": ["identity"]}
        normal = RecoveryPlanner.from_loaded(services, dependencies).plan(incident)["waves"]
        services["profile"] = Service("profile", 0, "us-east")
        changed = RecoveryPlanner.from_loaded(services, dependencies).plan(incident)["waves"]
        self.assertEqual(normal[5], ["profile"])
        self.assertEqual(changed[1], ["profile"])

        maximal_before = fixture_planner("maximal").plan(incident)["waves"]
        maximal_after = RecoveryPlanner.from_loaded(services, dependencies, "maximal").plan(incident)["waves"]
        self.assertEqual(maximal_before, maximal_after)
        self.assertEqual(set(sum(normal, [])), set(sum(maximal_before, [])))

    def test_shuffled_rows_produce_identical_output(self):
        expected = fixture_planner().plan({"incident_id": "i", "failed_services": ["identity"]})
        with open(SERVICES, newline="", encoding="utf-8") as handle:
            service_rows = list(csv.DictReader(handle))
            service_fields = list(service_rows[0])
        with open(DEPENDENCIES, newline="", encoding="utf-8") as handle:
            dependency_rows = list(csv.DictReader(handle))
            dependency_fields = list(dependency_rows[0])
        random.Random(42).shuffle(service_rows)
        random.Random(17).shuffle(dependency_rows)
        with tempfile.TemporaryDirectory() as tmp:
            service_path = Path(tmp) / "services.csv"
            dependency_path = Path(tmp) / "dependencies.csv"
            with open(service_path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=service_fields)
                writer.writeheader()
                writer.writerows(service_rows)
            with open(dependency_path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=dependency_fields)
                writer.writeheader()
                writer.writerows(dependency_rows)
            actual = RecoveryPlanner.from_paths(service_path, dependency_path).plan(
                {"incident_id": "i", "failed_services": ["identity"]}
            )
        self.assertEqual(actual, expected)

    def test_region_split_cycle_is_ordered_after_retention(self):
        services = {
            "a": Service("a", 1, "east"),
            "b": Service("b", 1, "west"),
            "c": Service("c", 1, "east"),
        }
        dependencies = [
            Dependency("a", "b", "hard"),
            Dependency("b", "a", "hard"),
            Dependency("c", "a", "hard"),
        ]
        result = RecoveryPlanner.from_loaded(services, dependencies).plan(
            {"incident_id": "i", "failed_services": ["a"], "region": "east"}
        )
        self.assertEqual(result["waves"], [["a"], ["c"]])

    def test_planner_reuse_is_stateless(self):
        planner = fixture_planner()
        incidents = [
            {"incident_id": "identity", "failed_services": ["identity"]},
            {
                "incident_id": "west",
                "failed_services": ["inventory"],
                "region": "us-west",
            },
            {"incident_id": "loop", "failed_services": ["legacy-sync"]},
            {
                "incident_id": "mixed",
                "failed_services": ["catalog", "does-not-exist"],
            },
        ]
        expected = [planner.plan(incident) for incident in incidents]
        interleaved = [incidents[2], incidents[0], incidents[3], incidents[1]]
        actual_by_id = {
            result["incident_id"]: result
            for incident in interleaved
            for result in [planner.plan(incident)]
        }
        self.assertEqual(
            [actual_by_id[result["incident_id"]] for result in expected], expected
        )
        self.assertEqual([planner.plan(incident) for incident in incidents], expected)

    def test_incident_order_does_not_affect_results(self):
        planner = fixture_planner()
        incidents = [
            {"incident_id": "a", "failed_services": ["identity"]},
            {"incident_id": "b", "failed_services": ["catalog"]},
            {"incident_id": "c", "failed_services": ["legacy-sync"]},
        ]
        forward = {result["incident_id"]: result for result in map(planner.plan, incidents)}
        reverse = {
            result["incident_id"]: result
            for result in map(planner.plan, reversed(incidents))
        }
        self.assertEqual(reverse, forward)

    def test_incident_without_failed_services_key(self):
        result = fixture_planner().plan({"incident_id": "empty"})
        self.assertEqual(result["waves"], [])
        self.assertEqual(result["service_count"], 0)

    def test_explicit_null_region_matches_absent_region(self):
        planner = fixture_planner()
        absent = planner.plan({"incident_id": "i", "failed_services": ["identity"]})
        explicit = planner.plan(
            {"incident_id": "i", "failed_services": ["identity"], "region": None}
        )
        self.assertEqual(explicit, absent)

    def test_missing_incident_id_is_null(self):
        result = fixture_planner().plan({"failed_services": []})
        self.assertIsNone(result["incident_id"])

    def test_plan_level_unknown_region_is_empty_without_graph_traversal(self):
        planner = fixture_planner()
        incident = {
            "incident_id": "i",
            "failed_services": ["identity", "does-not-exist"],
            "region": "moon",
        }
        with patch.object(
            planner.dependents,
            "neighbours",
            side_effect=AssertionError("unknown region must not traverse the graph"),
        ):
            result = planner.plan(incident)
        self.assertEqual(result["waves"], [])
        self.assertEqual(result["service_count"], 0)
        self.assertEqual(result["unknown_services"], ["does-not-exist"])

    def test_plan_level_all_unknown_services(self):
        result = fixture_planner().plan(
            {"incident_id": "i", "failed_services": ["z", "x", "z"]}
        )
        self.assertEqual(result["waves"], [])
        self.assertEqual(result["service_count"], 0)
        self.assertEqual(result["unknown_services"], ["x", "z"])

    def test_maximal_policy_golden_all_incidents(self):
        planner = fixture_planner("maximal")
        incidents = [
            {"incident_id": "inc-identity", "failed_services": ["identity"]},
            {
                "incident_id": "inc-shipping-west",
                "failed_services": ["inventory"],
                "region": "us-west",
            },
            {"incident_id": "inc-legacy-loop", "failed_services": ["legacy-sync"]},
            {
                "incident_id": "inc-mixed",
                "failed_services": ["catalog", "does-not-exist"],
            },
        ]
        expected = [
            [
                ["identity"],
                ["checkout", "fraud", "profile"],
                ["orders"],
                ["analytics", "payments"],
            ],
            [["inventory"], ["routing", "shipping"], ["returns"]],
            [["legacy-sync", "partner-feed"]],
            [["catalog"], ["search"], ["recommendations"]],
        ]
        self.assertEqual(
            [planner.plan(incident)["waves"] for incident in incidents], expected
        )


if __name__ == "__main__":
    unittest.main()
