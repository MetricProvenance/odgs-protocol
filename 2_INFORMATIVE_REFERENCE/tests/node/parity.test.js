
import { describe, it, expect } from 'vitest';
import { OdgsInterceptor } from '../../src/interceptor.js';
import scenarios from '../fixtures/standard_scenarios.json';

describe('Protocol Parity (Node.js)', () => {
    const interceptor = new OdgsInterceptor();
    // Use a real blocked process from ontology_graph.json (Rule 2021 blocks O2C_S03)
    const processUrn = "urn:odgs:process:O2C_S03";

    scenarios.forEach((scenario) => {
        it(`Scenario ${scenario.id}: Should ${scenario.expected_result}`, () => {
            const context = scenario.input;

            if (scenario.expected_result === "PASS") {
                expect(() => interceptor.intercept(processUrn, context)).not.toThrow();
            } else if (scenario.expected_result === "BLOCK") {
                // We expect it to throw an error containing "BLOCK" or specific code
                expect(() => interceptor.intercept(processUrn, context)).toThrow();
            }
        });
    });
});
