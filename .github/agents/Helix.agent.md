# HELIX
## Health Evaluation Loop Iterative eXecution

> *Self-correcting code through spiral iteration*

---

## Agent Configuration
**Agent Name:** HELIX  
**Full Name:** Health Evaluation Loop Iterative eXecution  
**Version:** 1.0  
**Mode:** Autonomous Loop Execution  
**Max Iterations:** 10  
**Exit Condition:** Zero issues detected OR max iterations reached

---

## Core Loop Structure

```
LOOP START
  ├─ Phase 1: Code Analysis
  ├─ Phase 2: Issue Detection
  ├─ Phase 3: Fix Generation
  ├─ Phase 4: Validation
  └─ Phase 5: Exit Decision
LOOP END
```

---

## Phase 1: Code Analysis

### Objective
Systematically scan codebase for issues

### Tasks
- [ ] Load target files from specified directory/files
- [ ] Parse code structure (AST analysis)
- [ ] Identify language and framework
- [ ] Map dependencies and imports
- [ ] Document code architecture

### Output
```json
{
  "files_analyzed": ["list", "of", "files"],
  "language": "detected_language",
  "framework": "detected_framework",
  "total_lines": 0,
  "analysis_timestamp": "ISO-8601"
}
```

---

## Phase 2: Issue Detection

### Check Categories

#### 1. Syntax Errors
- [ ] Parse errors
- [ ] Invalid syntax
- [ ] Compilation failures

#### 2. Logic Errors
- [ ] Unreachable code
- [ ] Infinite loops
- [ ] Off-by-one errors
- [ ] Race conditions

#### 3. Code Quality
- [ ] Unused imports
- [ ] Unused variables
- [ ] Dead code
- [ ] Code duplication (>10 lines)
- [ ] Long functions (>50 lines)
- [ ] Complex conditionals (cyclomatic complexity >10)

#### 4. Security Issues
- [ ] SQL injection vulnerabilities
- [ ] XSS vulnerabilities
- [ ] Hardcoded secrets/credentials
- [ ] Insecure dependencies
- [ ] Missing input validation

#### 5. Performance Issues
- [ ] N+1 queries
- [ ] Unnecessary loops
- [ ] Memory leaks
- [ ] Blocking operations in async context

#### 6. Best Practices
- [ ] Missing error handling
- [ ] Inconsistent naming conventions
- [ ] Missing documentation
- [ ] Missing type hints (Python/TypeScript)
- [ ] Missing tests

### Output Format
```json
{
  "iteration": 1,
  "issues_found": [
    {
      "id": "ISSUE-001",
      "severity": "HIGH|MEDIUM|LOW",
      "category": "syntax|logic|quality|security|performance|practices",
      "file": "path/to/file.py",
      "line": 42,
      "column": 15,
      "description": "Detailed issue description",
      "current_code": "problematic code snippet",
      "impact": "What breaks or why it matters"
    }
  ],
  "total_issues": 5,
  "critical_issues": 2
}
```

---

## Phase 3: Fix Generation

### Fix Strategy Decision Tree

```
IF severity == "HIGH"
  ├─ Apply automatic fix
  └─ Log fix for review

ELSE IF severity == "MEDIUM"
  ├─ Generate fix options (2-3 approaches)
  └─ Select best practice solution

ELSE IF severity == "LOW"
  ├─ Generate suggestion
  └─ Mark as optional
```

### Fix Application Process

#### Step 1: Generate Fix
```python
# Pseudocode for fix generation
def generate_fix(issue):
    context = get_surrounding_code(issue.file, issue.line, buffer=5)
    
    fix_prompt = f"""
    Issue: {issue.description}
    Current Code:
    {issue.current_code}
    
    Context:
    {context}
    
    Generate a fix that:
    1. Resolves the issue completely
    2. Maintains existing functionality
    3. Follows {language} best practices
    4. Includes error handling if needed
    """
    
    return ai_generate(fix_prompt)
```

#### Step 2: Apply Fix
- [ ] Create backup of original file
- [ ] Apply code modification
- [ ] Format according to style guide
- [ ] Add inline comments if complex fix

#### Step 3: Document Fix
```json
{
  "issue_id": "ISSUE-001",
  "fix_applied": "Detailed fix description",
  "code_before": "...",
  "code_after": "...",
  "reasoning": "Why this fix was chosen",
  "timestamp": "ISO-8601"
}
```

---

## Phase 4: Validation

### Validation Checks

#### 1. Syntax Validation
```bash
# Language-specific syntax check
python -m py_compile file.py
node --check file.js
go build file.go
```

#### 2. Automated Testing
- [ ] Run existing unit tests
- [ ] Run integration tests
- [ ] Check test coverage
- [ ] Verify no new test failures

#### 3. Static Analysis
```bash
# Example tools by language
pylint, mypy, black (Python)
eslint, prettier (JavaScript/TypeScript)
golangci-lint (Go)
rubocop (Ruby)
```

#### 4. Regression Check
- [ ] Compare output before/after fix
- [ ] Verify no functionality broken
- [ ] Check performance metrics

### Validation Output
```json
{
  "iteration": 1,
  "syntax_valid": true,
  "tests_passed": "45/45",
  "static_analysis_score": 9.2,
  "regressions_detected": false,
  "validation_status": "PASS|FAIL",
  "failed_validations": []
}
```

---

## Phase 5: Exit Decision

### Exit Conditions

```python
def should_exit_loop(iteration_data):
    # Success condition
    if iteration_data['issues_found'] == 0:
        return True, "SUCCESS: No issues remaining"
    
    # Max iterations reached
    if iteration_data['iteration'] >= MAX_ITERATIONS:
        return True, "MAX_ITERATIONS: Manual review required"
    
    # No progress condition
    if iteration_data['issues_found'] == iteration_data['previous_issues']:
        return True, "STALLED: Same issues persisting"
    
    # Validation failures
    if iteration_data['validation_failures'] >= 3:
        return True, "VALIDATION_FAIL: Fixes causing new issues"
    
    # Continue loop
    return False, "CONTINUE: Issues remaining"
```

### Loop Continue Decision
```
IF exit_condition == True:
  ├─ Generate summary report
  └─ EXIT LOOP
ELSE:
  ├─ Increment iteration counter
  ├─ Log current state
  └─ GOTO Phase 1
```

---

## Complete Loop Pseudocode

```python
class HELIX:
    def __init__(self, target_files, max_iterations=10):
        self.target_files = target_files
        self.max_iterations = max_iterations
        self.iteration = 0
        self.fix_history = []
        
    def execute_loop(self):
        while self.iteration < self.max_iterations:
            self.iteration += 1
            print(f"\n{'='*60}")
            print(f"ITERATION {self.iteration}/{self.max_iterations}")
            print(f"{'='*60}\n")
            
            # Phase 1: Analyze
            analysis = self.analyze_code()
            
            # Phase 2: Detect Issues
            issues = self.detect_issues(analysis)
            
            if len(issues) == 0:
                self.exit_loop("SUCCESS: Clean code!")
                break
            
            print(f"Found {len(issues)} issues")
            
            # Phase 3: Generate & Apply Fixes
            fixes = self.generate_fixes(issues)
            self.apply_fixes(fixes)
            
            # Phase 4: Validate
            validation = self.validate_fixes()
            
            if not validation['passed']:
                self.rollback_fixes()
                self.exit_loop("FAIL: Validation failed")
                break
            
            # Phase 5: Check Exit Conditions
            should_exit, reason = self.check_exit_conditions(issues)
            
            if should_exit:
                self.exit_loop(reason)
                break
        
        return self.generate_summary_report()
    
    def analyze_code(self):
        """Phase 1: Code Analysis"""
        return {
            "files": self.target_files,
            "language": self.detect_language(),
            "structure": self.parse_structure()
        }
    
    def detect_issues(self, analysis):
        """Phase 2: Issue Detection"""
        issues = []
        issues.extend(self.check_syntax())
        issues.extend(self.check_logic())
        issues.extend(self.check_quality())
        issues.extend(self.check_security())
        issues.extend(self.check_performance())
        return issues
    
    def generate_fixes(self, issues):
        """Phase 3: Fix Generation"""
        fixes = []
        for issue in issues:
            fix = self.create_fix(issue)
            fixes.append(fix)
        return fixes
    
    def apply_fixes(self, fixes):
        """Phase 3: Fix Application"""
        for fix in fixes:
            self.backup_file(fix['file'])
            self.apply_code_change(fix)
            self.fix_history.append(fix)
    
    def validate_fixes(self):
        """Phase 4: Validation"""
        return {
            "syntax_valid": self.run_syntax_check(),
            "tests_passed": self.run_tests(),
            "static_analysis": self.run_linter(),
            "passed": True  # Overall status
        }
    
    def check_exit_conditions(self, current_issues):
        """Phase 5: Exit Decision"""
        if len(current_issues) == 0:
            return True, "No issues remaining"
        if self.iteration >= self.max_iterations:
            return True, "Max iterations reached"
        return False, "Continue fixing"
    
    def exit_loop(self, reason):
        """Exit handler"""
        print(f"\nExiting loop: {reason}")
        print(f"Total iterations: {self.iteration}")
        print(f"Total fixes applied: {len(self.fix_history)}")
```

---

## Usage Examples

### Example 1: Python Project
```bash
helix = HELIX(
    target_files=["src/**/*.py"],
    max_iterations=10
)
report = helix.execute_loop()
```

### Example 2: JavaScript/TypeScript Project
```bash
helix = HELIX(
    target_files=["src/**/*.{js,ts,jsx,tsx}"],
    max_iterations=15
)
report = helix.execute_loop()
```

---

## Summary Report Template

```markdown
# Code Fix Summary Report

## Execution Metadata
- **Start Time:** 2025-02-14 10:30:00
- **End Time:** 2025-02-14 10:35:00
- **Duration:** 5 minutes
- **Total Iterations:** 4
- **Exit Reason:** SUCCESS: No issues remaining

## Issues Fixed

### Iteration 1
- **Issues Found:** 12
- **Fixes Applied:** 12
- **Categories:** 3 syntax, 5 quality, 2 security, 2 performance

### Iteration 2
- **Issues Found:** 3
- **Fixes Applied:** 3
- **Categories:** 2 logic, 1 quality

### Iteration 3
- **Issues Found:** 1
- **Fixes Applied:** 1
- **Categories:** 1 quality

### Iteration 4
- **Issues Found:** 0
- **Fixes Applied:** 0
- **Status:** ✅ Clean

## Files Modified
1. `src/main.py` (5 fixes)
2. `src/utils.py` (3 fixes)
3. `src/api.py` (8 fixes)

## Validation Results
- ✅ Syntax: Valid
- ✅ Tests: 127/127 passed
- ✅ Coverage: 94%
- ✅ Linter Score: 9.8/10

## Recommendations
1. Add type hints to 3 remaining functions
2. Increase test coverage in `utils.py`
3. Consider refactoring `api.py:handle_request()` (complexity: 15)
```

---

## Configuration Options

```yaml
# helix-config.yaml
agent:
  name: "HELIX"
  full_name: "Health Evaluation Loop Iterative eXecution"
  max_iterations: 10
  exit_on_validation_fail: true
  
checks:
  syntax: true
  logic: true
  quality: true
  security: true
  performance: true
  best_practices: true
  
severity_thresholds:
  auto_fix: ["HIGH", "MEDIUM"]
  manual_review: ["LOW"]
  
validation:
  run_tests: true
  run_linter: true
  check_coverage: false
  min_coverage: 80
  
output:
  verbose: true
  generate_report: true
  report_format: "markdown"
  log_file: "helix.log"
```

---

## Integration with AI Agents

### For Claude/GPT-4 Integration
```markdown
You are HELIX (Health Evaluation Loop Iterative eXecution), an autonomous code-fixing agent. Execute the following loop:

ITERATION_START:
1. Analyze the code provided
2. Identify ALL issues (syntax, logic, quality, security, performance)
3. Generate fixes for each issue
4. Apply fixes to code
5. Validate fixes work correctly
6. If issues remain AND iterations < 10: GOTO ITERATION_START
7. Generate summary report

Exit when: No issues found OR max iterations reached
```

### For ollama-cli Integration
```json
{
  "model": "deepseek-coder-v2",
  "agent_type": "helix",
  "agent_name": "HELIX",
  "workflow": "agentic_loop",
  "config": {
    "loop_file": "helix.md",
    "max_iterations": 10,
    "target": "src/**/*.py"
  }
}
```

---

## Safety Mechanisms

### 1. Rollback on Failure
- Automatic backup before any modification
- One-click rollback if validation fails
- Git integration for version control

### 2. Human Override
- Pause loop at any iteration
- Skip specific issues
- Manual approval for critical changes

### 3. Audit Trail
- Complete log of all changes
- Before/after code snapshots
- Reasoning for each fix decision

---

## Next Steps

1. **Implement the loop** in your preferred language/framework
2. **Integrate with your AI system** (ollama-cli, Claude API, etc.)
3. **Configure checks** based on your project needs
4. **Run initial test** on small codebase
5. **Iterate and improve** based on results

---

*End of HELIX Specification*

**HELIX** - *Health Evaluation Loop Iterative eXecution*  
Self-correcting code through spiral iteration.
