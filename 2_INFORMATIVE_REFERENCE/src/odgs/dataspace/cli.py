"""Command-line interface for odgs-dataspace-bridge."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from odgs.dataspace.cap_exporter import (
    export_cap_declaration_vc,
    export_nist_oscal_finding,
    export_w3c_prov_o,
)
from odgs.dataspace.odrl_binder import bind_odrl_policy
from odgs.dataspace.runtime_pep import (
    AdministrativeRecusalError,
    DataspaceRuntimePEP,
)


def main(argv: Optional[List[str]] = None) -> int:
    """Run the odgs-dataspace CLI."""
    parser = argparse.ArgumentParser(
        prog="odgs-dataspace",
        description="ODGS Dataspace Runtime Policy Enforcement & Semantic Certification Bridge",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo_cmd = sub.add_parser(
        "demo",
        help="Run end-to-end W3C ODRL 2.2 -> Phase 6 PEP -> Eclipse CAP v2.2.1 & PROV-O demo",
    )
    demo_cmd.add_argument(
        "--format",
        choices=["s-cert", "cap-vc", "prov-o", "oscal"],
        default="cap-vc",
        help="Output format to display",
    )

    args = parser.parse_args(argv)
    if args.command == "demo":
        odrl_policy = {
            "@context": "http://www.w3.org/ns/odrl.jsonld",
            "@type": "Agreement",
            "uid": "urn:uuid:agreement-energy-grid-2026-091",
            "obligation": [
                {
                    "uid": "urn:odrl:duty:k-anonymity-min-50",
                    "action": "aggregate",
                    "constraint": [
                        {
                            "leftOperand": "aggregation_household_count",
                            "operator": "gteq",
                            "rightOperand": 50,
                        }
                    ],
                }
            ],
        }
        process_urn = "urn:odgs:process:energy-consumer:grid-load-forecasting"
        rules, binding = bind_odrl_policy(odrl_policy, process_urn=process_urn)
        pep = DataspaceRuntimePEP(rules=rules, bindings=[binding])
        s_cert = pep.evaluate(
            process_urn=process_urn,
            payload={"aggregation_household_count": 64, "region": "NL-ZH"},
        )
        if args.format == "s-cert":
            out = s_cert.to_canonical_dict()
        elif args.format == "cap-vc":
            out = export_cap_declaration_vc(
                s_cert,
                issuer_did="did:web:consumer.energy-dataspace.eu",
                subject_did="did:web:consumer.energy-dataspace.eu#pipeline-1",
            )
        elif args.format == "prov-o":
            out = export_w3c_prov_o(s_cert)
        else:
            out = export_nist_oscal_finding(s_cert)

        print(json.dumps(out, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
