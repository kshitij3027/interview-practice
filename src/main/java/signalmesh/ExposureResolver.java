package signalmesh;

import java.util.List;

public final class ExposureResolver {
    private final Dataset dataset;

    public ExposureResolver(Dataset dataset) {
        this.dataset = dataset;
    }

    public List<Result> resolveAll(List<Query> queries) {
        throw new UnsupportedOperationException("Implement the exposure cohort resolver");
    }

    public Dataset dataset() {
        return dataset;
    }

    public record Result(
            String requestId,
            String status,
            Integer componentSize,
            Integer highRiskCount,
            Long riskPoints,
            String representative,
            String reason) {

        public static Result resolved(
                String requestId,
                int componentSize,
                int highRiskCount,
                long riskPoints,
                String representative) {
            return new Result(requestId, "resolved", componentSize, highRiskCount, riskPoints, representative, null);
        }

        public static Result invalid(String requestId, String reason) {
            return new Result(requestId, "invalid", null, null, null, null, reason);
        }
    }
}
