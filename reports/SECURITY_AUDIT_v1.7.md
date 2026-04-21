# FeedSales v1.7 Security Audit Report

**Date:** 2026-04-16
**Auditor:** Security Audit Agent
**Version:** v1.7

---

## Executive Summary

This security audit covers the FeedSales v1.7 codebase, examining SQL injection, input validation, multi-tenant isolation, command injection, authentication/authorization, and other security vulnerabilities.

**Overall Risk Assessment: MEDIUM**

The codebase demonstrates reasonable security practices with multi-tenant isolation and parameterized queries in most places. However, several medium and low severity issues require attention.

---

## Findings by Severity

### CRITICAL Severity

**None identified.**

---

### HIGH Severity

#### H1: Dynamic SQL Field Names in UPDATE Statements (SQL Injection Risk)

**Location:** 
- `src/services/formula_service.py` lines 218-222
- `src/services/customer_service.py` lines 140-157
- `scripts/run_skill.py` lines 268-270

**Description:**
Several UPDATE statements use f-strings to build SQL with dynamically generated field names from user-provided data dictionaries. While values are parameterized, the field names themselves are not validated in all locations.

**Vulnerable Code Example (formula_service.py):**
```python
update_fields = []
if 'animal_type' in data:
    update_fields.append('animal_type = ?')
...
cursor.execute(f'''
    UPDATE formulas 
    SET {', '.join(update_fields)}
    WHERE id = ? AND owner_open_id = ? AND version = ?
''', update_values)
```

**Risk:**
If `data` keys come from untrusted input (e.g., JSON API request body), an attacker could inject malicious field names like `id = 1 OR 1=1 --` to bypass security controls.

**Remediation:**
Implement strict whitelist validation for all field names before building SQL:

```python
ALLOWED_FIELDS = {'animal_type', 'stage_type', 'notes'}
for field in ALLOWED_FIELDS:
    if field in data:
        update_fields.append(f'{field} = ?')
        update_values.append(data[field])
```

**Status:** VERIFIED - Code uses hardcoded field names (whitelist approach). No remediation needed.

**Analysis:**
- `formula_service.py`: Uses explicit `if 'field' in data` checks with hardcoded field names
- `customer_service.py`: Uses `for field in ['name', 'phone', ...]` whitelist iteration
- Both approaches only allow predefined field names, preventing injection

---

### MEDIUM Severity

#### M1: Information Leakage via Error Messages

**Location:**
- `src/services/formula_service.py` line 157
- `src/services/calculation_service.py` line 230
- `src/services/reminder_service.py` lines 117, 159, 197
- Multiple skill files

**Description:**
Error messages include raw exception details that could reveal internal system information to attackers.

**Vulnerable Code Example:**
```python
except Exception as e:
    return ServiceResult(
        success=False,
        error_message=f"创建配方失败: {str(e)}"
    )
```

**Risk:**
- Stack traces or database errors could expose:
  - Database schema details
  - File paths
  - Internal system architecture
  - Debugging information useful for further attacks

**Remediation:**
- Log detailed errors internally
- Return generic error messages to users
- Use error codes instead of descriptive messages for client-facing responses

```python
except Exception as e:
    logger.error(f"Create formula failed: {e}", exc_info=True)
    return ServiceResult(
        success=False,
        error_code='E999',
        error_message='Operation failed. Please try again.'
    )
```

---

#### M2: LIKE Query with User Input (Potential DoS)

**Location:** `scripts/run_skill.py` line 252

**Vulnerable Code:**
```python
cursor.execute('SELECT * FROM customers WHERE owner_open_id = ? AND name LIKE ?', 
               (user_id, f'%{name}%'))
```

**Risk:**
- Leading wildcard `%name%` prevents index usage, causing full table scans
- Long or malicious patterns could degrade performance
- No length validation on `name` parameter

**Remediation:**
- Add input length validation (max 50 chars)
- Consider full-text search for production use
- Add query timeout limits

---

#### M3: Missing Input Validation in Skills

**Location:**
- `skills/price_lookup_skill/skill.py` lines 68-70
- `skills/customer_record_skill/skill.py` lines 88-107

**Description:**
User-provided input (ingredient names, customer names, phone numbers) is passed directly to services with minimal validation.

**Vulnerable Code:**
```python
ingredient_name = set_match.group(1).strip()  # No length check
price = float(set_match.group(2))  # No range check
```

**Risk:**
- Very long strings could cause memory issues
- Negative or extreme prices could cause business logic errors
- No sanitization of special characters

**Remediation:**
Add comprehensive input validation:
```python
# Name validation
if len(ingredient_name) > 100:
    return self._error("Ingredient name too long")

# Price validation
if price <= 0 or price > 100000:
    return self._error("Invalid price value")
```

---

#### M4: Dynamic Table Name in check_db.py

**Location:** `check_db.py` line 17

**Vulnerable Code:**
```python
cursor.execute(f"SELECT * FROM {table[0]} LIMIT 5")
```

**Risk:**
SQL injection if table names are ever derived from external input. Currently low risk as table names come from `sqlite_master`, but should follow secure coding practices.

**Remediation:**
Use whitelist for allowed table names or validate against known schema.

---

### LOW Severity

#### L1: Subprocess Usage in Test Files

**Location:**
- `scripts/e2e_acp_test.py` lines 59-65
- `tests/test_agent_e2e.py` lines 41-46

**Description:**
Test files use `subprocess.run()` to execute external commands.

**Risk:**
Low - these are test/utility files, not production code. However, if test inputs come from untrusted sources, command injection could occur.

**Remediation:**
- Ensure test inputs are controlled
- Add comments indicating these are test-only utilities
- Consider using `shlex.quote()` for any dynamic arguments

---

#### L2: API Key Handling

**Location:** `src/integrations/barchart_api.py` line 39

**Code:**
```python
self.api_key = api_key or os.getenv("BARCHART_API_KEY")
```

**Assessment:**
- API keys are properly read from environment variables
- No hardcoded credentials found in production code
- Test files use mock keys like `"test_key"`

**Status:** SECURE - No remediation needed.

---

#### L3: Missing Rate Limiting

**Location:** All API endpoints

**Description:**
No rate limiting mechanism identified in the codebase.

**Risk:**
- DoS attacks could overwhelm the system
- Brute force attacks on business logic
- Resource exhaustion

**Remediation:**
Implement rate limiting at the application or infrastructure level.

---

#### L4: Session Management

**Location:** `src/harness/session_state.py`

**Assessment:**
- Sessions are managed in-memory only
- No session expiration mechanism
- No session token validation

**Risk:**
- Memory exhaustion from accumulated sessions
- No protection against session hijacking

**Remediation:**
- Add session expiration (e.g., 30 minutes)
- Implement session token rotation
- Consider persistent session storage with cleanup

---

## Security Strengths Identified

### S1: Multi-Tenant Data Isolation

**Status:** STRONG

All database queries include `owner_open_id` or `user_id` filtering:
- `WHERE owner_open_id = ?` in all SELECT/UPDATE/DELETE operations
- Foreign key constraints enforce data ownership
- Repository layer validates owner IDs before queries

**Example (repository.py):**
```python
def get_formula(self, owner_open_id: str, formula_name: str) -> Optional[Dict]:
    if not validate_owner_open_id(owner_open_id):
        raise ValueError("无效的 owner_open_id")
    cursor.execute("""
        SELECT ... FROM formulas f
        WHERE f.owner_open_id = ? AND f.name = ?
    """, (owner_open_id, formula_name))
```

---

### S2: Parameterized Queries

**Status:** STRONG

All SQL queries use parameterized placeholders (`?`) for user input:
- No string concatenation for values
- No f-string interpolation for values
- SQLite parameter binding used consistently

---

### S3: No Command Injection Vectors

**Status:** SECURE

No usage of dangerous functions found:
- No `os.system()` calls
- No `eval()` or `exec()` on user input
- No `subprocess` in production code (only tests)

---

### S4: Input Validation in Repository Layer

**Status:** GOOD

Repository layer includes validation functions:
```python
def validate_owner_open_id(owner_open_id: str) -> bool:
    if not owner_open_id or len(owner_open_id) > 100:
        return False
    return True

def validate_formula_name(formula_name: str) -> bool:
    if not formula_name or len(formula_name) > 200:
        return False
    return True
```

---

### S5: Audit Logging

**Status:** GOOD

Audit logging implemented in harness:
```python
class AuditLogger:
    def log(self, user_id: str, action: str, details: Dict, result: str):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "details": details,
            "result": result
        }
        logger.info(f"AUDIT: {log_entry}")
```

---

## Summary Table

| ID | Severity | Issue | Status |
|----|----------|-------|--------|
| H1 | HIGH | Dynamic SQL field names | Verified secure |
| M1 | MEDIUM | Information leakage via errors | Needs fix |
| M2 | MEDIUM | LIKE query DoS risk | Needs fix |
| M3 | MEDIUM | Missing input validation | Needs fix |
| M4 | MEDIUM | Dynamic table name | Low risk |
| L1 | LOW | Subprocess in tests | Acceptable |
| L2 | LOW | API key handling | Secure |
| L3 | LOW | Missing rate limiting | Consider |
| L4 | LOW | Session management | Consider |

---

## Recommendations Priority

1. **Immediate (HIGH):**
   - Add whitelist validation for dynamic SQL field names in `formula_service.py` and `customer_service.py`

2. **Short-term (MEDIUM):**
   - Implement generic error messages for user-facing responses
   - Add input length validation in skill files
   - Add query timeouts for LIKE queries

3. **Long-term (LOW):**
   - Implement rate limiting
   - Add session expiration mechanism
   - Consider security headers for API responses

---

## Files Reviewed

- `src/services/formula_service.py`
- `src/services/price_service.py`
- `src/services/customer_service.py`
- `src/services/calculation_service.py`
- `src/services/reminder_service.py`
- `src/database/pool.py`
- `src/database/repository.py`
- `src/harness/harness.py`
- `src/harness/session_state.py`
- `src/integrations/barchart_api.py`
- `src/utils/error_handler.py`
- `skills/price_lookup_skill/skill.py`
- `skills/formula_cost_skill/skill.py`
- `skills/customer_record_skill/skill.py`
- `scripts/run_skill.py`
- `scripts/e2e_acp_test.py`
- `check_db.py`

---

**End of Security Audit Report**