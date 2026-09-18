package signalmesh;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class Loader {
    private Loader() {}

    public static Dataset load(Path accountsPath, Path policiesPath, Path eventsPath, Path queriesPath)
            throws IOException {
        Map<String, Account> accounts = loadAccounts(accountsPath);
        Map<String, Policy> policies = loadPolicies(policiesPath);
        List<Event> events = loadEvents(eventsPath, accounts, policies);
        List<Query> queries = loadQueries(queriesPath);
        return new Dataset(Map.copyOf(accounts), Map.copyOf(policies), List.copyOf(events), List.copyOf(queries));
    }

    private static Map<String, Account> loadAccounts(Path path) throws IOException {
        Map<String, Account> result = new LinkedHashMap<>();
        for (String[] row : Csv.read(path, "account_id", "risk_tier", "risk_points")) {
            String id = required(row[0], "account_id");
            boolean highRisk;
            if (row[1].equals("high")) highRisk = true;
            else if (row[1].equals("standard")) highRisk = false;
            else throw new IllegalArgumentException("unknown risk_tier for " + id);

            long points = parseLong(row[2], "risk_points");
            if (points < 0) throw new IllegalArgumentException("negative risk_points for " + id);
            if (result.putIfAbsent(id, new Account(id, highRisk, points)) != null) {
                throw new IllegalArgumentException("duplicate account_id: " + id);
            }
        }
        return result;
    }

    private static Map<String, Policy> loadPolicies(Path path) throws IOException {
        Map<String, Policy> result = new LinkedHashMap<>();
        for (String[] row : Csv.read(path, "relation_type", "ttl_minutes")) {
            String type = required(row[0], "relation_type");
            long minutes = parseLong(row[1], "ttl_minutes");
            if (minutes <= 0) throw new IllegalArgumentException("ttl_minutes must be positive for " + type);
            if (result.putIfAbsent(type, new Policy(type, Duration.ofMinutes(minutes))) != null) {
                throw new IllegalArgumentException("duplicate relation_type: " + type);
            }
        }
        return result;
    }

    private static List<Event> loadEvents(
            Path path, Map<String, Account> accounts, Map<String, Policy> policies) throws IOException {
        Map<String, Event> byEventId = new LinkedHashMap<>();
        Map<String, EvidenceIdentity> evidenceIdentities = new HashMap<>();
        Map<String, Map<Instant, String>> eventAtInstant = new HashMap<>();

        for (String[] row : Csv.read(path,
                "event_id", "evidence_id", "account_a", "account_b", "relation_type", "action", "occurred_at")) {
            Event event = parseEvent(row);
            if (!accounts.containsKey(event.accountA()) || !accounts.containsKey(event.accountB())) {
                throw new IllegalArgumentException("event references unknown account: " + event.eventId());
            }
            if (event.accountA().equals(event.accountB())) {
                throw new IllegalArgumentException("self-link is invalid: " + event.eventId());
            }
            if (!policies.containsKey(event.relationType())) {
                throw new IllegalArgumentException("unknown relation_type: " + event.relationType());
            }

            Event existing = byEventId.get(event.eventId());
            if (existing != null) {
                if (!existing.equals(event)) {
                    throw new IllegalArgumentException("conflicting event_id: " + event.eventId());
                }
                continue;
            }
            byEventId.put(event.eventId(), event);

            EvidenceIdentity identity = new EvidenceIdentity(event.pairKey(), event.relationType());
            EvidenceIdentity priorIdentity = evidenceIdentities.putIfAbsent(event.evidenceId(), identity);
            if (priorIdentity != null && !priorIdentity.equals(identity)) {
                throw new IllegalArgumentException("evidence identity changed: " + event.evidenceId());
            }

            String priorAtInstant = eventAtInstant
                    .computeIfAbsent(event.evidenceId(), ignored -> new HashMap<>())
                    .putIfAbsent(event.occurredAt(), event.eventId());
            if (priorAtInstant != null) {
                throw new IllegalArgumentException("ambiguous same-instant events for evidence_id: " + event.evidenceId());
            }
        }

        List<Event> result = new ArrayList<>(byEventId.values());
        result.sort(Comparator.comparing(Event::occurredAt).thenComparing(Event::eventId));
        return result;
    }

    private static List<Query> loadQueries(Path path) throws IOException {
        List<Query> result = new ArrayList<>();
        Map<String, Boolean> ids = new HashMap<>();
        for (String[] row : Csv.read(path, "request_id", "account_id", "as_of")) {
            String requestId = required(row[0], "request_id");
            if (ids.putIfAbsent(requestId, Boolean.TRUE) != null) {
                throw new IllegalArgumentException("duplicate request_id: " + requestId);
            }
            result.add(new Query(requestId, required(row[1], "account_id"), parseInstant(row[2], "as_of")));
        }
        return result;
    }

    private static Event parseEvent(String[] row) {
        Event.Action action;
        try {
            action = Event.Action.valueOf(required(row[5], "action"));
        } catch (IllegalArgumentException e) {
            throw new IllegalArgumentException("invalid action: " + row[5]);
        }
        return new Event(
                required(row[0], "event_id"),
                required(row[1], "evidence_id"),
                required(row[2], "account_a"),
                required(row[3], "account_b"),
                required(row[4], "relation_type"),
                action,
                parseInstant(row[6], "occurred_at"));
    }

    private static Instant parseInstant(String raw, String field) {
        try {
            return OffsetDateTime.parse(required(raw, field)).toInstant();
        } catch (DateTimeParseException e) {
            throw new IllegalArgumentException("invalid RFC3339 " + field + ": " + raw);
        }
    }

    private static long parseLong(String raw, String field) {
        try {
            return Long.parseLong(required(raw, field));
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("invalid integer " + field + ": " + raw);
        }
    }

    private static String required(String raw, String field) {
        if (raw == null || raw.isBlank()) throw new IllegalArgumentException(field + " is required");
        return raw;
    }

    private record EvidenceIdentity(String pairKey, String relationType) {}
}
