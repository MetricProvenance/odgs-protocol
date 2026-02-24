import standardMetrics from '../../1_NORMATIVE_SPECIFICATION/schemas/legislative/standard_metrics.json' with { type: "json" };
import standardDqDimensions from '../../1_NORMATIVE_SPECIFICATION/schemas/legislative/standard_dq_dimensions.json' with { type: "json" };
import standardDataRules from '../../1_NORMATIVE_SPECIFICATION/schemas/judiciary/standard_data_rules.json' with { type: "json" };
import rootCauseFactors from '../../1_NORMATIVE_SPECIFICATION/schemas/judiciary/root_cause_factors.json' with { type: "json" };
import businessProcessMaps from '../../1_NORMATIVE_SPECIFICATION/schemas/executive/business_process_maps.json' with { type: "json" };
import physicalDataMap from '../../1_NORMATIVE_SPECIFICATION/schemas/executive/physical_data_map.json' with { type: "json" };
import ontologyGraph from '../../1_NORMATIVE_SPECIFICATION/schemas/legislative/ontology_graph.json' with { type: "json" };

import { OdgsInterceptor, ProcessBlockedException, SecurityException } from './interceptor.js';

export {
  standardMetrics,
  standardDataRules,
  standardDqDimensions,
  rootCauseFactors,
  businessProcessMaps,
  physicalDataMap,
  ontologyGraph,
  OdgsInterceptor,
  ProcessBlockedException,
  SecurityException
};

export default {
  standardMetrics,
  standardDataRules,
  standardDqDimensions,
  rootCauseFactors,
  businessProcessMaps,
  physicalDataMap,
  ontologyGraph,
  OdgsInterceptor,
  ProcessBlockedException,
  SecurityException
};
