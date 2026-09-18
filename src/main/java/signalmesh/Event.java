package signalmesh;

import java.time.Instant;

public record Event(
        String eventId,
        String evidenceId,
        String accountA,
        String accountB,
        String relationType,
        Action action,
        Instant occurredAt) {

    public enum Action { ASSERT, RETRACT }

    public String pairKey() {
        return accountA.compareTo(accountB) <= 0
                ? accountA + "\u0000" + accountB
                : accountB + "\u0000" + accountA;
    }
}
