import standardMetrics from './legislative/standard_metrics.json' with { type: "json" };
import standardDqDimensions from './legislative/standard_dq_dimensions.json' with { type: "json" };
import standardDataRules from './judiciary/standard_data_rules.json' with { type: "json" };
import rootCauseFactors from './judiciary/root_cause_factors.json' with { type: "json" };
import businessProcessMaps from './executive/business_process_maps.json' with { type: "json" };
import physicalDataMap from './executive/physical_data_map.json' with { type: "json" };
import ontologyGraph from './legislative/ontology_graph.json' with { type: "json" };

import { OdgsInterceptor, ProcessBlockedException } from './interceptor.js';

export {
  standardMetrics,
  standardDataRules,
  standardDqDimensions,
  rootCauseFactors,
  businessProcessMaps,
  physicalDataMap,
  ontologyGraph,
  OdgsInterceptor,
  ProcessBlockedException
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
  ProcessBlockedException
};
