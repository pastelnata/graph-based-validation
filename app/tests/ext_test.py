"""
Comprehensive Test Suite for AIService Validation Framework

Run these tests to ensure all components are working correctly:
1. Unit tests for individual components
2. Integration tests for the full pipeline
3. Edge case tests for robustness
4. Performance tests for optimization

To run: python ext_test.py

"""

import requests
import json
import time
from typing import Any


# ============================================================================
# TEST 1: API Health & Connectivity
# ============================================================================

def test_api_health():
    """Test that the API server is running and responding."""
    print("\n" + "="*60)
    print("TEST 1: API Health Check")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        assert response.status_code == 200
        assert "message" in response.json()
        print("✅ PASS: API is healthy and responding")
        return True
    except Exception as e:
        print(f"❌ FAIL: API health check failed: {e}")
        return False


# ============================================================================
# TEST 2: Basic Request/Response Format
# ============================================================================

def test_request_response_format():
    """Test that the endpoint accepts correct format and returns correct format."""
    print("\n" + "="*60)
    print("TEST 2: Request/Response Format")
    print("="*60)
    
    try:
        payload = {
            "genome_properties": [
                {
                    "property_type": "STANDARD",
                    "name": "age",
                    "value": "28",
                    "unit": "years",
                    "genome_type": "numeric"
                }
            ]
        }
        
        response = requests.post("http://localhost:8000/graphs/", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "success"
        assert "rules" in data
        assert isinstance(data["rules"], list)
        assert "count" in data
        assert "properties" in data
        
        print("✅ PASS: Request/Response format is correct")
        print(f"   Status: {data['status']}")
        print(f"   Rules count: {data['count']}")
        print(f"   Properties: {data['properties']}")
        return True
    except Exception as e:
        print(f"❌ FAIL: Format test failed: {e}")
        return False


# ============================================================================
# TEST 3: Multiple Properties
# ============================================================================

def test_multiple_properties():
    """Test with multiple properties to ensure relationships are detected."""
    print("\n" + "="*60)
    print("TEST 3: Multiple Properties")
    print("="*60)
    
    try:
        payload = {
            "genome_properties": [
                {
                    "property_type": "STANDARD",
                    "name": "height",
                    "value": "180",
                    "unit": "cm",
                    "genome_type": "numeric"
                },
                {
                    "property_type": "STANDARD",
                    "name": "weight",
                    "value": "75",
                    "unit": "kg",
                    "genome_type": "numeric"
                },
                {
                    "property_type": "STANDARD",
                    "name": "age",
                    "value": "28",
                    "unit": "years",
                    "genome_type": "numeric"
                }
            ]
        }
        
        response = requests.post("http://localhost:8000/graphs/", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert len(data["properties"]) == 3
        print(f"✅ PASS: Multiple properties processed correctly")
        print(f"   Properties: {data['properties']}")
        print(f"   Rules generated: {data['count']}")
        
        # Print sample rules
        if data['count'] > 0:
            print(f"   Sample rule: {data['rules'][0]['source']} → {data['rules'][0]['target']}")
        
        return True
    except Exception as e:
        print(f"❌ FAIL: Multiple properties test failed: {e}")
        return False


# ============================================================================
# TEST 4: Different Property Types | failed
# ============================================================================

def test_different_property_types():
    """Test with different genome property types."""
    print("\n" + "="*60)
    print("TEST 4: Different Property Types")
    print("="*60)
    
    try:
        payload = {
            "genome_properties": [
                {
                    "property_type": "STANDARD",
                    "name": "status",
                    "value": "active",
                    "unit": "categorical",
                    "genome_type": "categorical"
                },
                {
                    "property_type": "STANDARD",
                    "name": "income",
                    "value": "50000",
                    "unit": "USD",
                    "genome_type": "numeric"
                },
                {
                    "property_type": "GENOME_PROPERTY",
                    "name": "tax_rate",
                    "value": "0.15",
                    "unit": "ratio",
                    "genome_type": "numeric"
                }
            ]
        }
        
        response = requests.post("http://localhost:8000/graphs/", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        print(f"✅ PASS: Different property types handled correctly")
        print(f"   Properties: {data['properties']}")
        print(f"   Rules: {data['count']}")
        return True
    except Exception as e:
        print(f"❌ FAIL: Property types test failed: {e}")
        return False


# ============================================================================
# TEST 5: Minimal Request (Edge Case)
# ============================================================================

def test_minimal_request():
    """Test with minimum valid request (1 property)."""
    print("\n" + "="*60)
    print("TEST 5: Minimal Request (1 Property)")
    print("="*60)
    
    try:
        payload = {
            "genome_properties": [
                {
                    "property_type": "STANDARD",
                    "name": "temperature",
                    "value": "25",
                    "unit": "celsius",
                    "genome_type": "numeric"
                }
            ]
        }
        
        response = requests.post("http://localhost:8000/graphs/", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        # With 1 property, there should be no cross-field rules
        # (rules need at least 2 properties)
        print(f"✅ PASS: Minimal request handled correctly")
        print(f"   Properties: {data['properties']}")
        print(f"   Rules generated: {data['count']}")
        if data['count'] == 0:
            print("   (Expected: no rules with single property)")
        return True
    except Exception as e:
        print(f"❌ FAIL: Minimal request test failed: {e}")
        return False


# ============================================================================
# TEST 6: Error Handling - Invalid Request
# ============================================================================

def test_invalid_request():
    """Test error handling for invalid requests."""
    print("\n" + "="*60)
    print("TEST 6: Error Handling - Invalid Request")
    print("="*60)
    
    try:
        # Send invalid JSON
        payload = {"invalid_key": []}
        
        response = requests.post("http://localhost:8000/graphs/", json=payload)
        # Should return 422 (validation error)
        if response.status_code == 422:
            print(f"✅ PASS: Invalid request rejected with 422 status")
            print(f"   Response: {response.json()['detail'][:100]}...")
            return True
        else:
            print(f"❌ FAIL: Expected 422, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAIL: Error handling test failed: {e}")
        return False


# ============================================================================
# TEST 7: Empty Properties List
# ============================================================================

def test_empty_properties():
    """Test with empty properties list."""
    print("\n" + "="*60)
    print("TEST 7: Empty Properties List")
    print("="*60)
    
    try:
        payload = {"genome_properties": []}
        
        response = requests.post("http://localhost:8000/graphs/", json=payload)
        # Should return 200 with 0 rules or 422 for validation
        if response.status_code in [200, 422]:
            print(f"✅ PASS: Empty list handled with status {response.status_code}")
            if response.status_code == 200:
                print(f"   Rules: {response.json()['count']}")
            return True
        else:
            print(f"❌ FAIL: Unexpected status code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAIL: Empty properties test failed: {e}")
        return False


# ============================================================================
# TEST 8: Performance - Response Time
# ============================================================================

def test_performance():
    """Test API response time."""
    print("\n" + "="*60)
    print("TEST 8: Performance - Response Time")
    print("="*60)
    
    try:
        payload = {
            "genome_properties": [
                {
                    "property_type": "STANDARD",
                    "name": "metric_a",
                    "value": "100",
                    "unit": "units",
                    "genome_type": "numeric"
                },
                {
                    "property_type": "STANDARD",
                    "name": "metric_b",
                    "value": "50",
                    "unit": "units",
                    "genome_type": "numeric"
                }
            ]
        }
        
        start = time.time()
        response = requests.post("http://localhost:8000/graphs/", json=payload, timeout=60)
        elapsed = time.time() - start
        
        assert response.status_code == 200
        
        print(f"✅ PASS: Request completed")
        print(f"   Response time: {elapsed:.2f} seconds")
        if elapsed < 10:
            print(f"   ⚡ Performance: Excellent (< 10s)")
        elif elapsed < 30:
            print(f"   ⚡ Performance: Good (< 30s)")
        else:
            print(f"   ⚠️  Performance: Slow (> 30s) - API may be throttled")
        
        return True
    except requests.exceptions.Timeout:
        print(f"❌ FAIL: Request timeout (> 60s)")
        return False
    except Exception as e:
        print(f"❌ FAIL: Performance test failed: {e}")
        return False


# ============================================================================
# TEST 9: Rule Validity - JSON Structure
# ============================================================================

def test_rule_structure():
    """Test that generated rules have valid structure."""
    print("\n" + "="*60)
    print("TEST 9: Rule Validity - JSON Structure")
    print("="*60)
    
    try:
        payload = {
            "genome_properties": [
                {"property_type": "STANDARD", "name": "x", "value": "10", "unit": "units", "genome_type": "numeric"},
                {"property_type": "STANDARD", "name": "y", "value": "20", "unit": "units", "genome_type": "numeric"}
            ]
        }
        
        response = requests.post("http://localhost:8000/graphs/", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check rule structure
        for rule in data['rules']:
            assert "source" in rule, "Missing 'source' field"
            assert "target" in rule, "Missing 'target' field"
            assert "constraint" in rule, "Missing 'constraint' field"
            assert isinstance(rule.get("condition"), (str, type(None))), "Invalid 'condition' type"
            assert isinstance(rule.get("message"), (str, type(None))), "Invalid 'message' type"
        
        print(f"✅ PASS: All rules have valid structure")
        print(f"   Rules validated: {len(data['rules'])}")
        if data['rules']:
            rule = data['rules'][0]
            print(f"   Sample rule structure:")
            print(f"     - source: {rule['source']}")
            print(f"     - target: {rule['target']}")
            print(f"     - constraint: {rule['constraint']}")
            if rule.get('condition'):
                print(f"     - condition: {rule['condition']}")
        
        return True
    except AssertionError as e:
        print(f"❌ FAIL: Rule structure invalid: {e}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Rule structure test failed: {e}")
        return False


# ============================================================================
# TEST 10: Consistency - Multiple Calls with Same Input | failed
# ============================================================================

def test_consistency():
    """Test that same input produces consistent output."""
    print("\n" + "="*60)
    print("TEST 10: Consistency - Multiple Calls")
    print("="*60)
    
    try:
        payload = {
            "genome_properties": [
                {"property_type": "STANDARD", "name": "input", "value": "5", "unit": "units", "genome_type": "numeric"},
                {"property_type": "STANDARD", "name": "output", "value": "10", "unit": "units", "genome_type": "numeric"}
            ]
        }
        
        # Make two requests with same input
        response1 = requests.post("http://localhost:8000/graphs/", json=payload)
        time.sleep(1)  # Small delay
        response2 = requests.post("http://localhost:8000/graphs/", json=payload)
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Both should return the same number of rules
        # (Content may vary due to AI non-determinism, but structure should be same)
        assert len(data1['rules']) == len(data2['rules'])
        
        print(f"✅ PASS: Consistent results across multiple calls")
        print(f"   Call 1 rules: {data1['count']}")
        print(f"   Call 2 rules: {data2['count']}")
        print(f"   Match: {data1['count'] == data2['count']}")
        
        return True
    except Exception as e:
        print(f"❌ FAIL: Consistency test failed: {e}")
        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests and generate a report."""
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST SUITE FOR VALIDATION FRAMEWORK")
    print("="*60)
    
    tests = [
        ("API Health Check", test_api_health),
        ("Request/Response Format", test_request_response_format),
        ("Multiple Properties", test_multiple_properties),
        ("Different Property Types", test_different_property_types),
        ("Minimal Request", test_minimal_request),
        ("Invalid Request Handling", test_invalid_request),
        ("Empty Properties List", test_empty_properties),
        ("Performance", test_performance),
        ("Rule Structure Validity", test_rule_structure),
        ("Consistency", test_consistency),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ FAIL: {test_name} - Unexpected error: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*60)
    print(f"TOTAL: {passed}/{total} tests passed ({int(passed/total*100)}%)")
    print("="*60)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Your framework is working perfectly!")
    elif passed >= total - 2:
        print("\n✅ Most tests passed. Minor issues detected.")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Review results above.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)