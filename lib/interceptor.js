import ontologyGraph from './schemas/legislative/ontology_graph.json' with { type: "json" };
import standardDataRules from './schemas/judiciary/standard_data_rules.json' with { type: "json" };

// Sovereign Handshake Logic (Simulated for JS)
// In a real Node environment, verification would hash the files.
// Here we at least accept the parameter to match Python signature.

export class ProcessBlockedException extends Error {
    constructor(message) {
        super(message);
        this.name = "ProcessBlockedException";
    }
}

export class OdgsInterceptor {
    constructor() {
        this.graph = ontologyGraph;
        this.rules = this._loadRules();
    }

    _loadRules() {
        // Index by URN for fast lookup
        const indexed = {};
        let rulesList = [];

        if (Array.isArray(standardDataRules)) {
            rulesList = standardDataRules;
        } else if (standardDataRules.rules && Array.isArray(standardDataRules.rules)) {
            rulesList = standardDataRules.rules;
        } else {
            // Single object fallback
            rulesList = [standardDataRules];
        }

        rulesList.forEach(rule => {
            // Standard format: urn:odgs:rule:{id}
            const rid = rule.rule_id;
            const urn = `urn:odgs:rule:${rid}`;
            indexed[urn] = rule;
        });
        return indexed;
    }

    /**
     * Intercepts data flow and enforces sovereign binding.
     * @param {string} processUrn - The process lifecycle stage (e.g., "urn:odgs:process:O2C").
     * @param {object} dataContext - The payload to validate.
     * @param {string|null} requiredIntegrityHash - [OPTIONAL] The SHA-256 hash of the Legislative definition.
     */
    intercept(processUrn, dataContext, requiredIntegrityHash = null) {
        if (requiredIntegrityHash) {
            // TODO for v2.1: Implement Node.js hashing parity
            console.warn("[ODGS] Integrity Hash provided but Node.js engine is in Client Mode. Verification skipped.");
        }

        console.log(`🛡️  Interceptor Active: Checking Access for Process [${processUrn}]`);

        // 1. Identify Blocking Rules from the Graph
        const blockingRules = this._findBlockingRules(processUrn);

        if (blockingRules.length === 0) {
            console.log("   ✅ No Hard Stop rules found for this process.");
            return true;
        }

        console.log(`   ⚠️  Found ${blockingRules.length} Potential Blocking Rules.`);

        // 2. Evaluate each Blocking Rule
        for (const ruleUrn of blockingRules) {
            const ruleDef = this.rules[ruleUrn];
            if (!ruleDef) {
                console.log(`   [warn] Rule definition not found for ${ruleUrn}, skipping.`);
                continue;
            }
            this._evaluateRule(ruleDef, dataContext);
        }

        console.log("   ✅ All Blocking Rules Passed. Access Granted.");
        return true;
    }

    _findBlockingRules(targetProcessUrn) {
        /**
         * Traverses the Ontology Graph to find edges where:
         * Source = Rule, Target = Process, Relationship = BLOCKS_PROCESS
         */
        const edges = this.graph.graph_edges || [];
        return edges
            .filter(edge => edge.target_urn === targetProcessUrn && edge.relationship === "BLOCKS_PROCESS")
            .map(edge => edge.source_urn);
    }

    _evaluateRule(ruleDef, data) {
        const ruleId = ruleDef.rule_id;
        const ruleName = ruleDef.name;
        console.log(`      🔎 Verifying Rule ${ruleId}: ${ruleName}`);

        // --- LOGIC DISPATCHER (Simulation of complex rule engine) ---

        // Logic for Rule 2021: ISO 6346 Container ID
        if (String(ruleId) === "2021") {
            const cid = data.container_id || "";
            // Regex: 4 letters, 7 numbers
            const pattern = /^[A-Z]{4}[0-9]{7}$/;

            if (!pattern.test(cid)) {
                throw new ProcessBlockedException(
                    `HARD STOP: Rule ${ruleId} Failed. Value '${cid}' does not match pattern ${pattern}. Process is BLOCKED.`
                );
            }
        } else {
            console.log(`      [info] No executable logic implemented for Rule ${ruleId}, passing by default.`);
        }
    }
}
