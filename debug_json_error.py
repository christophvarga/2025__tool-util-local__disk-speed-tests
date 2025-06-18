#!/usr/bin/env python3
"""
Debug script to identify which API endpoint is returning malformed JSON.
This will help us pinpoint the exact source of the JSON parsing error.
"""

import requests
import json
import sys

def test_api_endpoint(url, endpoint_name):
    """Test a single API endpoint and analyze the response."""
    print(f"\n{'='*60}")
    print(f"Testing: {endpoint_name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'Not set')}")
        print(f"Content-Length: {len(response.text)} characters")
        
        # Show raw response (first 500 chars)
        print(f"\nRaw Response (first 500 chars):")
        print("-" * 40)
        print(repr(response.text[:500]))
        print("-" * 40)
        
        # Try to parse as JSON
        try:
            json_data = response.json()
            print(f"✅ JSON parsing: SUCCESS")
            print(f"JSON keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'Not a dict'}")
            return True, None
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing: FAILED")
            print(f"Error: {e}")
            print(f"Error position: line {e.lineno}, column {e.colno}")
            
            # Show the problematic line
            lines = response.text.split('\n')
            if e.lineno <= len(lines):
                problematic_line = lines[e.lineno - 1]
                print(f"Problematic line {e.lineno}: {repr(problematic_line)}")
                if e.colno <= len(problematic_line):
                    print(f"Character at position {e.colno}: {repr(problematic_line[e.colno-1:e.colno])}")
            
            return False, e
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False, e
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False, e

def main():
    """Test all API endpoints to find the problematic one."""
    base_url = "http://localhost:8765"
    
    # List of API endpoints to test
    endpoints = [
        ("/api/disks", "List Disks"),
        ("/api/status", "System Status"),
        ("/api/version", "Version Info"),
        ("/api/validate", "System Validation"),
        ("/api/setup/validate", "Setup Validation"),
        ("/api/test-fio", "FIO Test"),
        ("/api/fio/detect-shm", "FIO SHM Detection"),
        ("/api/background-tests", "Background Tests"),
    ]
    
    print("🔍 JSON Error Debugging Tool")
    print("Testing all API endpoints to identify malformed JSON responses...")
    
    failed_endpoints = []
    
    for endpoint, name in endpoints:
        url = base_url + endpoint
        success, error = test_api_endpoint(url, name)
        
        if not success:
            failed_endpoints.append((endpoint, name, error))
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if failed_endpoints:
        print(f"❌ Found {len(failed_endpoints)} problematic endpoints:")
        for endpoint, name, error in failed_endpoints:
            print(f"  - {name} ({endpoint}): {error}")
        
        # Focus on the first failed endpoint
        if failed_endpoints:
            endpoint, name, error = failed_endpoints[0]
            print(f"\n🎯 FOCUS: First failed endpoint - {name}")
            print(f"This is likely the cause of the 'line 19 column 30' error.")
            
            # Test it again with more detail
            url = base_url + endpoint
            print(f"\nDetailed analysis of {url}:")
            try:
                response = requests.get(url, timeout=10)
                lines = response.text.split('\n')
                print(f"Total lines: {len(lines)}")
                
                if len(lines) >= 19:
                    line19 = lines[18]  # 0-indexed
                    print(f"Line 19 content: {repr(line19)}")
                    if len(line19) >= 30:
                        char30 = line19[29]  # 0-indexed
                        print(f"Character at position 30: {repr(char30)} (ASCII: {ord(char30)})")
                    else:
                        print(f"Line 19 is only {len(line19)} characters long")
                
                # Show all lines for context
                print(f"\nAll response lines:")
                for i, line in enumerate(lines[:25], 1):  # Show first 25 lines
                    marker = " <<<< PROBLEM LINE" if i == 19 else ""
                    print(f"{i:2d}: {repr(line)}{marker}")
                    
            except Exception as e:
                print(f"Detailed analysis failed: {e}")
    else:
        print("✅ All endpoints returned valid JSON!")
        print("The error might be intermittent or in a different endpoint.")

if __name__ == "__main__":
    main()
