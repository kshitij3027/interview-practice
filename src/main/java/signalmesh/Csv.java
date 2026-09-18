package signalmesh;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

final class Csv {
    private Csv() {}

    static List<String[]> read(Path path, String... expectedHeader) throws IOException {
        List<String> lines = Files.readAllLines(path);
        if (lines.isEmpty()) throw new IllegalArgumentException(path + ": empty CSV");

        String[] header = split(lines.getFirst());
        if (!Arrays.equals(header, expectedHeader)) {
            throw new IllegalArgumentException(path + ": unexpected header " + Arrays.toString(header));
        }

        List<String[]> rows = new ArrayList<>();
        for (int i = 1; i < lines.size(); i++) {
            if (lines.get(i).isBlank()) continue;
            String[] row = split(lines.get(i));
            if (row.length != expectedHeader.length) {
                throw new IllegalArgumentException(path + ": line " + (i + 1) + " has wrong column count");
            }
            rows.add(row);
        }
        return rows;
    }

    private static String[] split(String line) {
        return Arrays.stream(line.split(",", -1)).map(String::trim).toArray(String[]::new);
    }
}
