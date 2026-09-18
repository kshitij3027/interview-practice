package signalmesh;

import java.nio.file.Path;
import java.time.Instant;

public final class StarterTest {
    public static void main(String[] args) throws Exception {
        Dataset dataset = Loader.load(
                Path.of("fixtures/accounts.csv"),
                Path.of("fixtures/policies.csv"),
                Path.of("fixtures/events.csv"),
                Path.of("fixtures/queries.csv"));

        check(dataset.accounts().size() == 8, "expected 8 accounts");
        check(dataset.policies().size() == 3, "expected 3 policies");
        check(dataset.events().size() == 12, "exact retry should be deduplicated");
        check(dataset.queries().size() == 11, "expected 11 queries");
        check(dataset.accounts().get("A100").highRisk(), "A100 should be high risk");
        check(dataset.policies().get("device").ttl().toMinutes() == 60, "device TTL should parse");
        check(dataset.queries().get(10).asOf().equals(Instant.parse("2026-09-18T10:00:00Z")),
                "offset timestamp should normalize to the same instant");

        Event first = dataset.events().getFirst();
        check(first.occurredAt().equals(Instant.parse("2026-09-18T09:00:00Z")),
                "events should be normalized into chronological order for consumers");

        System.out.println("StarterTest: 8/8 passed");
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
