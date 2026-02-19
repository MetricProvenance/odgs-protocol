#!/usr/bin/env node

/**
 * ODGS Post-Install Banner
 * Prints a breaking change notice during npm install.
 */

const RESET = "\x1b[0m";
const BOLD = "\x1b[1m";
const RED = "\x1b[31m";
const YELLOW = "\x1b[33m";
const CYAN = "\x1b[36m";

const banner = `
${BOLD}${RED}+---------------------------------------------------------------+
|              ODGS v3.3.0 (Sovereign Edition)                  |
|                                                               |${RESET}
${BOLD}${YELLOW}|  ⚠️  BREAKING CHANGES:                                        |
|      • URN Migration: Integer IDs → URN strings               |
|      • Sovereign Handshake: Integrity verification required   |
|      • Tri-Partite Binding: 3-hash audit trail                |
|                                                               |
|  Existing nodes MUST run \`odgs migrate\` immediately.          |
|  See: MIGRATION_GUIDE.md                                      |${RESET}
${BOLD}${CYAN}|                                                               |
|  🛡️  ENTERPRISE USERS:                                        |
|      Watch this repo → Releases Only for pre-notification.    |
|      https://github.com/MetricProvenance/odgs-protocol        |
+---------------------------------------------------------------+${RESET}
`;

console.error(banner);
