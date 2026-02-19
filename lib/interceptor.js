import ontologyGraph from './schemas/legislative/ontology_graph.json' with { type: "json" };
import standardDataRules from './schemas/judiciary/standard_data_rules.json' with { type: "json" };
import { Parser } from 'expr-eval';

// ─── Sovereign Handshake (Node.js) ──────────────────────────────
// Computes SHA-256 hashes of legislative JSON files for integrity verification.
// Mirrors the Python `generate_project_hash()` implementation.

let _crypto = null;
let _fs = null;
let _path = null;

try {
    _crypto = await import('node:crypto');
    _fs = await import('node:fs');
    _path = await import('node:path');
} catch (e) {
    // Browser environment — crypto/fs/path not available, handshake disabled.
}

function computeDefinitionHash(schemasDir) {
    if (!_crypto || !_fs || !_path) return null;

    const schemaFiles = [
        'legislative/standard_metrics.json',
        'legislative/standard_dq_dimensions.json',
        'legislative/ontology_graph.json',
        'judiciary/standard_data_rules.json',
        'judiciary/root_cause_factors.json',
        'executive/business_process_maps.json',
        'executive/physical_data_map.json'
    ].sort();

    let comboString = '';

    for (const relPath of schemaFiles) {
        const fullPath = _path.join(schemasDir, relPath);
        try {
            const data = JSON.parse(_fs.readFileSync(fullPath, 'utf-8'));
            const canonical = JSON.stringify(data, Object.keys(data).sort(), 0)
                .replace(/\s+/g, ''); // Compact canonical form
            // Re-parse for deterministic key sorting
            const sorted = JSON.stringify(JSON.parse(canonical), null, 0);
            const hash = _crypto.createHash('sha256').update(sorted).digest('hex');
            comboString += hash;
        } catch (e) {
            console.warn(`Schema file load failed: ${relPath}: ${e.message}`);
            comboString += 'MISSING_FILE';
        }
    }

    return _crypto.createHash('sha256').update(comboString).digest('hex');
}

// ─── Exception Classes ──────────────────────────────────────────

export class ProcessBlockedException extends Error {
    constructor(message) {
        super(message);
        this.name = "ProcessBlockedException";
    }
}

export class SecurityException extends Error {
    constructor(message) {
        super(message);
        this.name = "SecurityException";
    }
}

// ─── Safe Expression Evaluator ──────────────────────────────────

const parser = new Parser();

// Register custom functions for rule evaluation
function regex_match(pattern, val) {
    if (!val) return false;
    try {
        return new RegExp(pattern).test(String(val));
    } catch (e) {
        console.warn(`regex_match failed: ${e.message}`);
        return false;
    }
}

function parse_date(val) {
    if (!val) return new Date(-8640000000000000).getTime();
    return new Date(val).getTime();
}

function today_fn() {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d.getTime();
}

// ─── Main Interceptor ───────────────────────────────────────────

export class OdgsInterceptor {
    constructor(schemasDir = null) {
        this.graph = ontologyGraph;
        this.rules = this._loadRules();
        this.schemasDir = schemasDir;
    }

    _loadRules() {
        const indexed = {};
        let rulesList = [];

        if (Array.isArray(standardDataRules)) {
            rulesList = standardDataRules;
        } else if (standardDataRules.rules && Array.isArray(standardDataRules.rules)) {
            rulesList = standardDataRules.rules;
        } else {
            rulesList = [standardDataRules];
        }

        rulesList.forEach(rule => {
            const rid = rule.rule_id;
            const urn = rule.urn || `urn:odgs:rule:${rid}`;
            indexed[urn] = rule;
        });
        return indexed;
    }

    /**
     * Intercepts data flow and enforces sovereign binding (v3.3).
     * @param {string} processUrn - The process lifecycle stage (e.g., "urn:odgs:process:O2C_S03").
     * @param {object} dataContext - The payload to validate.
     * @param {string|null} requiredIntegrityHash - The expected SHA-256 hash of the Legislative definition.
     * @returns {boolean} true if all rules pass.
     * @throws {ProcessBlockedException} if any HARD_STOP rule fails.
     * @throws {SecurityException} if the Sovereign Handshake fails.
     */
    intercept(processUrn, dataContext, requiredIntegrityHash = null) {

        // 1. SOVEREIGN HANDSHAKE — Validate Legislative Integrity
        if (requiredIntegrityHash && this.schemasDir) {
            const actualHash = computeDefinitionHash(this.schemasDir);
            if (actualHash && requiredIntegrityHash !== actualHash) {
                throw new SecurityException(
                    `Sovereign Handshake Failed: Legislative artifacts have been modified. ` +
                    `Expected hash ${requiredIntegrityHash.slice(0, 16)}..., ` +
                    `got ${actualHash.slice(0, 16)}...`
                );
            }
        }

        // 2. Identify Blocking Rules from the Graph
        const blockingRules = this._findBlockingRules(processUrn);

        if (blockingRules.length === 0) {
            return true;
        }

        // 3. Evaluate each Blocking Rule
        const violations = [];
        const warnings = [];

        for (const ruleUrn of blockingRules) {
            const ruleDef = this.rules[ruleUrn];
            if (!ruleDef) continue;

            const result = this._evaluateRule(ruleDef, dataContext);
            if (result.violation) {
                const severity = ruleDef.severity || "HARD_STOP";
                if (severity === "HARD_STOP") {
                    violations.push(result.violation);
                } else if (severity === "WARNING") {
                    warnings.push(result.violation);
                }
            }
        }

        // 4. ENFORCE
        if (violations.length > 0) {
            throw new ProcessBlockedException(
                `Governance Failure: ${JSON.stringify(violations)}`
            );
        }

        return true;
    }

    _findBlockingRules(targetProcessUrn) {
        const edges = this.graph.graph_edges || [];
        return edges
            .filter(edge => edge.target_urn === targetProcessUrn && edge.relationship === "BLOCKS_PROCESS")
            .map(edge => edge.source_urn);
    }

    /**
     * Evaluates a single rule against data using expr-eval (safe, no eval/Function).
     * @returns {{ violation: string|null }}
     */
    _evaluateRule(ruleDef, data) {
        const ruleId = ruleDef.rule_id;
        const ruleName = ruleDef.name;
        const logic = ruleDef.logic_expression;

        if (logic) {
            try {
                // Transpile Python boolean operators to JS-compatible
                let jsLogic = logic
                    .replace(/\band\b/g, "and")
                    .replace(/\bor\b/g, "or")
                    .replace(/\bnot\b/g, "not")
                    .replace(/r'([^']*)'/g, "'$1'")
                    .replace(/r"([^"]*)"/g, '"$1"');

                // Build evaluation context
                const evalContext = {
                    ...data,
                    value: data.value !== undefined
                        ? data.value
                        : (Object.keys(data).length === 1 ? Object.values(data)[0] : undefined),
                };

                // Register custom functions on the parser
                const p = new Parser();
                p.functions.regex_match = regex_match;
                p.functions.parse_date = parse_date;
                p.functions.today = today_fn;

                const isValid = p.evaluate(jsLogic, evalContext);

                if (!isValid) {
                    return { violation: `Rule ${ruleId} Failed: ${ruleName}` };
                }

            } catch (e) {
                // "Fail Closed" — treat execution errors as violations
                return { violation: `Rule ${ruleId} Execution Error: ${e.message}` };
            }
            return { violation: null };
        }

        // Legacy hardcoded fallback for Rule 2021 (Container ID Format)
        if (String(ruleId) === "2021") {
            const cid = data.container_id || "";
            const pattern = /^[A-Z]{4}[0-9]{7}$/;
            if (!pattern.test(cid)) {
                return { violation: `Rule ${ruleId} Failed: Value '${cid}' does not match pattern.` };
            }
        }

        return { violation: null };
    }
}
