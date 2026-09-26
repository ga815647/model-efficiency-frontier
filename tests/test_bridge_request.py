import json
import unittest

from bridge.request import RequestError, decode_request, validate_request


SHA = "a" * 40
ID = "c49aef65-50dd-4fc2-b2f2-8ecccf4ff24d"


def request_data():
    return {"schema_version": 1, "request_id": ID,
            "created_at": "2026-09-26T12:00:00+00:00", "product_sha": SHA,
            "operation": "refresh", "parameters": {"gpt_factor": 18, "grok_factor": 16,
            "min_score": 0, "min_score_reason": "full-candidate comparison", "max_cost": None}}


def validate(data, *, branch=None, parent_sha=SHA, changed_paths=None):
    return validate_request(data, branch=branch if branch is not None else "efficiency-run/" + ID,
                            parent_sha=parent_sha,
                            changed_paths=changed_paths if changed_paths is not None else
                            [("A", "bridge/requests/" + ID + ".json")])


class RequestTests(unittest.TestCase):
    def test_valid_refresh_is_normalized(self):
        self.assertEqual(validate(request_data()), request_data())

    def test_boolean_factor_is_not_a_number(self):
        r = request_data()
        r["parameters"]["grok_factor"] = True
        with self.assertRaises(RequestError):
            validate(r)

    def test_boolean_min_score_is_not_a_number(self):
        r = request_data()
        r['parameters']['min_score'] = True
        with self.assertRaises(RequestError):
            validate(r)

    def test_decode_rejects_duplicate_keys_at_any_depth(self):
        for text in ('{"a":1,"a":2}', '{"parameters":{"x":1,"x":2}}'):
            with self.subTest(text=text), self.assertRaises(RequestError):
                decode_request(text)

    def test_decode_rejects_nonfinite_constants_and_nonobject(self):
        for text in ('{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '[]', '{'):
            with self.subTest(text=text), self.assertRaises(RequestError):
                decode_request(text)

    def test_decode_returns_object(self):
        self.assertEqual(decode_request(json.dumps(request_data())), request_data())

    def test_exact_field_sets(self):
        for location, key, value in (("root", "unexpected", 1), ("root", "operation", None),
                                     ("parameters", "eps_score", 2), ("parameters", "min_score", None)):
            with self.subTest(location=location, key=key, value=value):
                r = request_data()
                target = r if location == "root" else r["parameters"]
                if value is None:
                    del target[key]
                else:
                    target[key] = value
                with self.assertRaises(RequestError):
                    validate(r)

    def test_invalid_identity_and_time(self):
        for field, value in (("schema_version", True), ("schema_version", 2),
                             ("request_id", "C49AEF65-50DD-4FC2-B2F2-8ECCCF4FF24D"),
                             ("request_id", "c49aef65-50dd-1fc2-b2f2-8ecccf4ff24d"),
                             ("product_sha", "a" * 39), ("product_sha", "g" * 40),
                             ("created_at", "2026-09-26T12:00:00"),
                             ("created_at", "2026-09-26T12:00:00Z garbage"),
                             ("operation", "run; rm -rf /")):
            with self.subTest(field=field, value=value):
                r = request_data()
                r[field] = value
                with self.assertRaises(RequestError):
                    validate(r)

    def test_offset_time_and_old_timestamp_are_accepted(self):
        r = request_data()
        r["created_at"] = "2020-01-01T12:00:00-05:00"
        self.assertEqual(validate(r)["created_at"], r["created_at"])

    def test_numeric_rejections(self):
        for key, value in (("gpt_factor", 0), ("grok_factor", -1), ("min_score", -1),
                           ("max_cost", 0), ("max_cost", True), ("gpt_factor", "18"),
                           ("min_score", float("nan")), ("grok_factor", float("inf")),
                           ("max_cost", float("-inf"))):
            with self.subTest(key=key, value=value):
                r = request_data()
                r["parameters"][key] = value
                with self.assertRaises(RequestError):
                    validate(r)

    def test_whitespace_reason_rejected(self):
        r = request_data()
        r["parameters"]["min_score_reason"] = " \n\t "
        with self.assertRaises(RequestError):
            validate(r)

    def test_transport_must_be_single_added_matching_file(self):
        variants = ({"branch": "efficiency-run/" + ID + "/extra"},
                    {"branch": "efficiency-run/other"},
                    {"parent_sha": "b" * 40},
                    {"changed_paths": [("M", "bridge/requests/" + ID + ".json")]},
                    {"changed_paths": [("A", "bridge/requests/other.json")]},
                    {"changed_paths": [("A", "bridge/requests/" + ID + ".json"),
                                       ("A", "scripts/new.py")]},
                    {"changed_paths": [("A", "bridge/requests/../" + ID + ".json")]})
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(RequestError):
                validate(request_data(), **variant)

    def test_recompute_archived_snapshot(self):
        r = request_data()
        r["operation"] = "recompute"
        r["source_snapshot"] = {"commit": "b" * 40,
                                "path": "runs/2026-09-26-general-grok16/candidates.csv"}
        self.assertEqual(validate(r), r)

    def test_recompute_success_result_snapshot_locator(self):
        r = request_data()
        r["operation"] = "recompute"
        r["source_snapshot"] = {"commit": "b" * 40,
                                "path": f"results/{ID}/12345-1/snapshot/candidates.csv"}
        self.assertEqual(validate(r), r)

    def test_recompute_requires_safe_fixed_locator(self):
        bad = (None, {}, {"commit": "b" * 39, "path": "runs/a/candidates.csv"},
               {"commit": "b" * 40, "path": "runs/../candidates.csv"},
               {"commit": "b" * 40, "path": "runs/a/../candidates.csv"},
               {"commit": "b" * 40, "path": "runs/a/other.csv"},
               {"commit": "b" * 40, "path": "https://example.com/candidates.csv"},
               {"commit": "b" * 40, "path": f"results/{ID}/12345-1/candidates.csv"},
               {"commit": "b" * 40, "path": f"results/{ID}/12345-1/snapshot/candidates.csv", "url": "x"})
        for locator in bad:
            with self.subTest(locator=locator):
                r = request_data()
                r["operation"] = "recompute"
                r["source_snapshot"] = locator
                with self.assertRaises(RequestError):
                    validate(r)

    def test_refresh_forbids_snapshot(self):
        r = request_data()
        r["source_snapshot"] = {"commit": "b" * 40, "path": "runs/a/candidates.csv"}
        with self.assertRaises(RequestError):
            validate(r)


if __name__ == "__main__":
    unittest.main()
