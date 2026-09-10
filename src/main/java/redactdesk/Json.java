package redactdesk;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

final class Json {
    static Object parse(String text) { return new Parser(text).parse(); }
    @SuppressWarnings("unchecked")
    static Map<String, Object> parseObject(String text) {
        Object value = parse(text);
        if (!(value instanceof Map<?, ?> map)) throw new IllegalArgumentException("JSON body must be an object");
        return (Map<String, Object>) map;
    }
    static String stringify(Object value) {
        if (value == null) return "null";
        if (value instanceof String s) return quote(s);
        if (value instanceof Number || value instanceof Boolean) return value.toString();
        if (value instanceof Map<?, ?> map) {
            StringBuilder out = new StringBuilder("{"); boolean first = true;
            for (var entry : map.entrySet()) { if (!first) out.append(','); first = false; out.append(quote(String.valueOf(entry.getKey()))).append(':').append(stringify(entry.getValue())); }
            return out.append('}').toString();
        }
        if (value instanceof Iterable<?> iterable) {
            StringBuilder out = new StringBuilder("["); boolean first = true;
            for (Object item : iterable) { if (!first) out.append(','); first = false; out.append(stringify(item)); }
            return out.append(']').toString();
        }
        throw new IllegalArgumentException("Unsupported JSON value: " + value.getClass());
    }
    private static String quote(String s) {
        StringBuilder out = new StringBuilder("\"");
        for (char ch : s.toCharArray()) {
            switch (ch) {
                case '"' -> out.append("\\\""); case '\\' -> out.append("\\\\"); case '\n' -> out.append("\\n"); case '\r' -> out.append("\\r"); case '\t' -> out.append("\\t");
                default -> { if (ch < 0x20) out.append(String.format("\\u%04x", (int) ch)); else out.append(ch); }
            }
        }
        return out.append('"').toString();
    }
    private static final class Parser {
        private final String text; private int i;
        Parser(String text) { this.text = text; }
        Object parse() { skip(); Object value = value(); skip(); if (i != text.length()) error("Unexpected trailing JSON"); return value; }
        private Object value() {
            skip(); if (i >= text.length()) error("Unexpected end of JSON"); char ch = text.charAt(i);
            return switch (ch) { case '{' -> object(); case '[' -> array(); case '"' -> string(); case 't' -> literal("true", true); case 'f' -> literal("false", false); case 'n' -> literal("null", null); default -> number(); };
        }
        private Map<String, Object> object() {
            expect('{'); skip(); Map<String, Object> map = new LinkedHashMap<>(); if (peek('}')) { i++; return map; }
            while (true) { skip(); String key = string(); skip(); expect(':'); map.put(key, value()); skip(); if (peek('}')) { i++; return map; } expect(','); }
        }
        private List<Object> array() {
            expect('['); skip(); List<Object> list = new ArrayList<>(); if (peek(']')) { i++; return list; }
            while (true) { list.add(value()); skip(); if (peek(']')) { i++; return list; } expect(','); }
        }
        private String string() {
            expect('"'); StringBuilder out = new StringBuilder();
            while (i < text.length()) { char ch = text.charAt(i++); if (ch == '"') return out.toString(); if (ch == '\\') { if (i >= text.length()) error("Bad string escape"); char esc = text.charAt(i++); switch (esc) { case '"', '\\', '/' -> out.append(esc); case 'b' -> out.append('\b'); case 'f' -> out.append('\f'); case 'n' -> out.append('\n'); case 'r' -> out.append('\r'); case 't' -> out.append('\t'); case 'u' -> { if (i + 4 > text.length()) error("Bad unicode escape"); out.append((char) Integer.parseInt(text.substring(i, i + 4), 16)); i += 4; } default -> error("Bad string escape"); } } else out.append(ch); }
            error("Unterminated string"); return null;
        }
        private Object number() {
            int start = i; if (peek('-')) i++; while (i < text.length() && Character.isDigit(text.charAt(i))) i++; if (peek('.')) { i++; while (i < text.length() && Character.isDigit(text.charAt(i))) i++; }
            if (i < text.length() && (text.charAt(i) == 'e' || text.charAt(i) == 'E')) { i++; if (peek('+') || peek('-')) i++; while (i < text.length() && Character.isDigit(text.charAt(i))) i++; }
            if (start == i) error("Expected JSON value"); String raw = text.substring(start, i);
            try { if (raw.contains(".") || raw.contains("e") || raw.contains("E")) return Double.parseDouble(raw); return Long.parseLong(raw); } catch (NumberFormatException e) { error("Bad number"); return null; }
        }
        private Object literal(String expected, Object value) { if (!text.startsWith(expected, i)) error("Bad literal"); i += expected.length(); return value; }
        private void skip() { while (i < text.length() && Character.isWhitespace(text.charAt(i))) i++; }
        private boolean peek(char ch) { return i < text.length() && text.charAt(i) == ch; }
        private void expect(char ch) { if (!peek(ch)) error("Expected '" + ch + "'"); i++; }
        private void error(String message) { throw new IllegalArgumentException(message + " at position " + i); }
    }
    private Json() {}
}
