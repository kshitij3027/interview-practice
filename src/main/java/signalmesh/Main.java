package signalmesh;

import java.io.IOException;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;

public final class Main {
    private Main() {}

    public static void main(String[] args) throws Exception {
        if (args.length == 0 || args[0].equals("--help") || args[0].equals("help")) {
            usage();
            return;
        }

        String command = args[0];
        Map<String, String> options = parseOptions(args, 1);
        Dataset dataset = Loader.load(
                Path.of(required(options, "--accounts")),
                Path.of(required(options, "--policies")),
                Path.of(required(options, "--events")),
                Path.of(required(options, "--queries")));

        switch (command) {
            case "validate" -> validate(dataset);
            case "resolve" -> resolve(dataset);
            default -> {
                System.err.println("unknown command: " + command);
                usage();
                System.exit(2);
            }
        }
    }

    private static void validate(Dataset dataset) {
        System.out.printf(
                "validated %d accounts / %d policies / %d deduplicated events / %d queries%n",
                dataset.accounts().size(),
                dataset.policies().size(),
                dataset.events().size(),
                dataset.queries().size());
    }

    private static void resolve(Dataset dataset) {
        ExposureResolver resolver = new ExposureResolver(dataset);
        for (ExposureResolver.Result result : resolver.resolveAll(dataset.queries())) {
            System.out.println(toJson(result));
        }
    }

    private static String toJson(ExposureResolver.Result result) {
        StringBuilder out = new StringBuilder();
        out.append("{\"request_id\":\"").append(escape(result.requestId())).append("\"");
        out.append(",\"status\":\"").append(escape(result.status())).append("\"");
        if (result.reason() != null) {
            out.append(",\"reason\":\"").append(escape(result.reason())).append("\"");
        } else {
            out.append(",\"component_size\":").append(result.componentSize());
            out.append(",\"high_risk_count\":").append(result.highRiskCount());
            out.append(",\"risk_points\":").append(result.riskPoints());
            out.append(",\"representative\":\"").append(escape(result.representative())).append("\"");
        }
        return out.append('}').toString();
    }

    private static String escape(String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private static Map<String, String> parseOptions(String[] args, int start) throws IOException {
        Map<String, String> result = new HashMap<>();
        for (int i = start; i < args.length; i += 2) {
            if (i + 1 >= args.length || !args[i].startsWith("--")) {
                throw new IllegalArgumentException("expected --name value pairs");
            }
            result.put(args[i], args[i + 1]);
        }
        return result;
    }

    private static String required(Map<String, String> options, String name) {
        String value = options.get(name);
        if (value == null) throw new IllegalArgumentException("missing option " + name);
        return value;
    }

    private static void usage() {
        System.out.println("Usage: signalmesh.Main <validate|resolve> --accounts FILE --policies FILE --events FILE --queries FILE");
    }
}
