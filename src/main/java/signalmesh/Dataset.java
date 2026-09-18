package signalmesh;

import java.util.List;
import java.util.Map;

public record Dataset(
        Map<String, Account> accounts,
        Map<String, Policy> policies,
        List<Event> events,
        List<Query> queries) {}
