import standardMetrics from './schemas/legislative/standard_metrics.json' with { type: "json" };
import standardDqDimensions from './schemas/legislative/standard_dq_dimensions.json' with { type: "json" };
import standardDataRules from './schemas/judiciary/standard_data_rules.json' with { type: "json" };
import rootCauseFactors from './schemas/judiciary/root_cause_factors.json' with { type: "json" };
import businessProcessMaps from './schemas/executive/business_process_maps.json' with { type: "json" };
import physicalDataMap from './schemas/executive/physical_data_map.json' with { type: "json" };
import ontologyGraph from './schemas/legislative/ontology_graph.json' with { type: "json" };

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
