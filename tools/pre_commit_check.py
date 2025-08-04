#!/usr/bin/env python3
"""
Pre-commit regression check - prevents commits that break core functionality.
Run this before any commit to ensure no regressions.
"""
import sys
import subprocess
import os
from pathlib import Path

def run_smoke_tests():
    """Run critical smoke tests."""
    print("🔍 Running smoke tests to prevent regressions...")
    
    project_root = Path(__file__).parent.parent
    smoke_test_path = project_root / "tests" / "test_core_smoke.py"
    
    if not smoke_test_path.exists():
        print("❌ Smoke tests not found - this is a critical error!")
        return False
    
    try:
        # Run smoke tests
        result = subprocess.run([
            sys.executable, str(smoke_test_path)
        ], capture_output=True, text=True, cwd=project_root)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Failed to run smoke tests: {e}")
        return False

def check_critical_files():
    """Check that critical files haven't been accidentally deleted."""
    project_root = Path(__file__).parent.parent
    
    critical_files = [
        "supervisor/supervisor.py",
        "agents/base_agent.py", 
        "utils/prompt_manager.py",
        "utils/project_context.py",
        "unified_api_server.py",
        "prompts/user_story_decomposer.txt"
    ]
    
    missing_files = []
    for file_path in critical_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ CRITICAL FILES MISSING: {missing_files}")
        return False
    
    print("✅ All critical files present")
    return True

def validate_template_integrity():
    """Ensure template files are valid."""
    project_root = Path(__file__).parent.parent
    prompts_dir = project_root / "prompts"
    
    if not prompts_dir.exists():
        print("❌ Prompts directory missing!")
        return False
    
    template_files = list(prompts_dir.glob("*.txt"))
    if len(template_files) < 5:  # Should have at least 5 agent templates
        print(f"❌ Too few template files found: {len(template_files)}")
        return False
    
    # Check user_story_decomposer specifically since it's been problematic
    user_story_template = prompts_dir / "user_story_decomposer.txt"
    if not user_story_template.exists():
        print("❌ user_story_decomposer.txt template missing!")
        return False
    
    # Check that it contains product_vision variable
    template_content = user_story_template.read_text()
    if "${product_vision}" not in template_content:
        print("❌ user_story_decomposer.txt missing ${product_vision} variable!")
        return False
    
    print("✅ Template integrity validated")
    return True

def main():
    """Run all pre-commit checks."""
    print("🛡️  PRE-COMMIT REGRESSION CHECK")
    print("=" * 50)
    
    checks = [
        ("Critical File Check", check_critical_files),
        ("Template Integrity", validate_template_integrity), 
        ("Smoke Tests", run_smoke_tests)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n🔍 Running {check_name}...")
        try:
            if not check_func():
                print(f"❌ {check_name} FAILED")
                all_passed = False
            else:
                print(f"✅ {check_name} PASSED")
        except Exception as e:
            print(f"❌ {check_name} FAILED with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ ALL PRE-COMMIT CHECKS PASSED - Safe to commit")
        return 0
    else:
        print("❌ PRE-COMMIT CHECKS FAILED - DO NOT COMMIT")
        print("\n🚨 CRITICAL: Fix all issues before committing to prevent regressions!")
        return 1

if __name__ == "__main__":
    sys.exit(main())