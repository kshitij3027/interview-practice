package redactdesk;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

final class Csv {
    static List<Map<String, String>> read(Path path) throws IOException {
        List<String> lines = Files.readAllLines(path);
        if (lines.isEmpty()) return List.of();
        List<String> headers = parseLine(lines.get(0));
        List<Map<String, String>> rows = new ArrayList<>();
        for (int i = 1; i < lines.size(); i++) {
            if (lines.get(i).isBlank()) continue;
            List<String> values = parseLine(lines.get(i));
            if (values.size() != headers.size()) throw new IOException("Malformed CSV row " + (i + 1) + " in " + path);
            Map<String, String> row = new LinkedHashMap<>();
            for (int c = 0; c < headers.size(); c++) row.put(headers.get(c), values.get(c));
            rows.add(row);
        }
        return rows;
    }
    static List<String> parseLine(String line) {
        List<String> values = new ArrayList<>();
        StringBuilder current = new StringBuilder();
        boolean quoted = false;
        for (int i = 0; i < line.length(); i++) {
            char ch = line.charAt(i);
            if (ch == '"') {
                if (quoted && i + 1 < line.length() && line.charAt(i + 1) == '"') { current.append('"'); i++; }
                else quoted = !quoted;
            } else if (ch == ',' && !quoted) { values.add(current.toString()); current.setLength(0); }
            else current.append(ch);
        }
        values.add(current.toString());
        return values;
    }
    private Csv() {}
}
