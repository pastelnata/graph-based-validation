
#!/usr/bin/env python3
"""
Simplified Validation Framework Test Suite

Purpose:
- Verify FastAPI server is running
- Verify Gemini API responds correctly
- Verify valid JSON rules are returned
- Verify request validation works

Run:
    python api_tests.py
"""

import json
import sys
import time

import requests


BASE_URL = "http://localhost:8000"
GRAPH_ENDPOINT = f"{BASE_URL}/graphs/"


# ============================================================================
# TEST 1: API HEALTH CHECK
# ============================================================================

def test_api_health():
    """Check if FastAPI server is running."""

    print("\n" + "=" * 60)
    print("TEST 1: API HEALTH CHECK")
    print("=" * 60)

    try:
        response = requests.get(BASE_URL, timeout=5)

        assert response.status_code == 200

        print("✅ PASS: API is running")
        print(f"   Status code: {response.status_code}")

        return True

    except Exception as error:
        print(f"❌ FAIL: API health check failed")
        print(f"   Error: {error}")

        print("\nMake sure the API is running with:")
        print("python -m uvicorn app.main:app --reload")

        return False


# ============================================================================
# TEST 2: VALID REQUEST + RULE GENERATION
# ============================================================================

def test_rule_generation():
    """
    Test full AI pipeline:
    - request schema
    - Gemini response
    - JSON parsing
    - rule generation
    """

    print("\n" + "=" * 60)
    print("TEST 2: RULE GENERATION")
    print("=" * 60)

    payload = {
        "properties": [
            {
                "property_type": "STANDARD",
                "name": "voltage",
                "value": "220",
                "unit": "V",
                "genome_type": "numeric",
            },
            {
                "property_type": "STANDARD",
                "name": "current",
                "value": "10",
                "unit": "A",
                "genome_type": "numeric",
            },
            {
                "property_type": "STANDARD",
                "name": "power",
                "value": "2200",
                "unit": "W",
                "genome_type": "numeric",
            },
        ]
    }

    try:
        start_time = time.time()

        response = requests.post(
            GRAPH_ENDPOINT,
            json=payload,
            timeout=60,
        )

        elapsed = time.time() - start_time

        assert response.status_code == 200

        data = response.json()

        # Basic structure validation
        assert data["status"] == "success"
        assert "rules" in data
        assert isinstance(data["rules"], list)
        assert "count" in data
        assert "properties" in data

        print("✅ PASS: Rule generation successful")
        print(f"   Response time: {elapsed:.2f}s")
        print(f"   Properties: {data['properties']}")
        print(f"   Rules generated: {data['count']}")

        # Print sample rule if available
        if data["rules"]:
            sample_rule = data["rules"][0]

            print("\n   Sample rule:")
            print(json.dumps(sample_rule, indent=4))

        return True

    except Exception as error:
        print("❌ FAIL: Rule generation failed")
        print(f"   Error: {error}")

        try:
            print("\nResponse:")
            print(response.text)
        except Exception:
            pass

        return False


# ============================================================================
# TEST 3: RULE JSON STRUCTURE VALIDATION
# ============================================================================

def test_rule_structure():
    """
    Ensure returned rules match Rule schema.
    """

    print("\n" + "=" * 60)
    print("TEST 3: RULE STRUCTURE VALIDATION")
    print("=" * 60)

    payload = {
        "properties": [
            {
                "property_type": "STANDARD",
                "name": "input_voltage",
                "value": "220",
                "unit": "V",
                "genome_type": "numeric",
            },
            {
                "property_type": "STANDARD",
                "name": "output_voltage",
                "value": "110",
                "unit": "V",
                "genome_type": "numeric",
            },
        ]
    }

    try:
        response = requests.post(
            GRAPH_ENDPOINT,
            json=payload,
            timeout=60,
        )

        assert response.status_code == 200

        data = response.json()

        for rule in data["rules"]:

            # Top-level fields
            assert "source" in rule
            assert "target" in rule
            assert "rule_details" in rule

            # Nested rule details
            details = rule["rule_details"]

            assert "constraint" in details

            if "condition" in details:
                assert isinstance(
                    details["condition"],
                    (str, type(None)),
                )

            if "message" in details:
                assert isinstance(
                    details["message"],
                    (str, type(None)),
                )

        print("✅ PASS: Rule structure is valid")
        print(f"   Rules validated: {len(data['rules'])}")

        return True

    except Exception as error:
        print("❌ FAIL: Rule structure validation failed")
        print(f"   Error: {error}")

        return False


# ============================================================================
# TEST 4: INVALID REQUEST HANDLING
# ============================================================================

def test_invalid_request():
    """
    Ensure invalid payloads return validation errors.
    """

    print("\n" + "=" * 60)
    print("TEST 4: INVALID REQUEST HANDLING")
    print("=" * 60)

    invalid_payload = {
        "invalid_key": []
    }

    try:
        response = requests.post(
            GRAPH_ENDPOINT,
            json=invalid_payload,
            timeout=10,
        )

        assert response.status_code == 422

        print("✅ PASS: Invalid request correctly rejected")
        print(f"   Status code: {response.status_code}")

        return True

    except Exception as error:
        print("❌ FAIL: Invalid request test failed")
        print(f"   Error: {error}")

        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests."""

    print("\n" + "=" * 60)
    print("VALIDATION FRAMEWORK TEST SUITE")
    print("=" * 60)

    tests = [
        ("API Health Check", test_api_health),
        ("Rule Generation", test_rule_generation),
        ("Rule Structure Validation", test_rule_structure),
        ("Invalid Request Handling", test_invalid_request),
    ]

    results = {}

    for test_name, test_function in tests:
        try:
            results[test_name] = test_function()

        except Exception as error:
            print(f"\n❌ FAIL: {test_name}")
            print(f"   Unexpected error: {error}")

            results[test_name] = False

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():

        status = "✅ PASS" if result else "❌ FAIL"

        print(f"{status}: {test_name}")

    print("\n" + "=" * 60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 ALL TESTS PASSED")
        print("Your validation framework is working correctly.")

    else:
        print("\n⚠️ Some tests failed.")
        print("Review the errors above.")

    return passed == total


if __name__ == "__main__":

    success = run_all_tests()

    sys.exit(0 if success else 1)

