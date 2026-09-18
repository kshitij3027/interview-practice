package signalmesh;

import java.time.Instant;

public record Query(String requestId, String accountId, Instant asOf) {}
