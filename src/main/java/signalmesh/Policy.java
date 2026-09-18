package signalmesh;

import java.time.Duration;

public record Policy(String relationType, Duration ttl) {}
