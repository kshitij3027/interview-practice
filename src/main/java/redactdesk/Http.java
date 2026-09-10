package redactdesk;

import com.sun.net.httpserver.HttpExchange;
import java.io.IOException;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;

final class Http {
    static Map<String, String> query(HttpExchange exchange) {
        Map<String, String> out = new LinkedHashMap<>(); String raw = exchange.getRequestURI().getRawQuery(); if (raw == null || raw.isBlank()) return out;
        for (String pair : raw.split("&")) { String[] parts = pair.split("=", 2); out.put(decode(parts[0]), parts.length == 2 ? decode(parts[1]) : ""); } return out;
    }
    static Map<String, Object> jsonBody(HttpExchange exchange) throws IOException {
        String body = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
        try { return Json.parseObject(body); } catch (IllegalArgumentException e) { throw new ApiException(400, "invalid_json", e.getMessage()); }
    }
    static String string(Map<String, Object> body, String key) { Object value = body.get(key); if (!(value instanceof String s)) throw new ApiException(400, "invalid_request", key + " must be a string"); return s; }
    static int integer(Map<String, Object> body, String key) { Object value = body.get(key); if (!(value instanceof Number n)) throw new ApiException(400, "invalid_request", key + " must be an integer"); double d = n.doubleValue(); if (d != Math.rint(d)) throw new ApiException(400, "invalid_request", key + " must be an integer"); return n.intValue(); }
    static void json(HttpExchange exchange, int status, Object value) throws IOException { byte[] bytes = Json.stringify(value).getBytes(StandardCharsets.UTF_8); exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8"); exchange.getResponseHeaders().set("Cache-Control", "no-store"); exchange.sendResponseHeaders(status, bytes.length); exchange.getResponseBody().write(bytes); exchange.close(); }
    static void noBody(HttpExchange exchange, int status) throws IOException { exchange.sendResponseHeaders(status, -1); exchange.close(); }
    private static String decode(String value) { return URLDecoder.decode(value, StandardCharsets.UTF_8); }
    private Http() {}
}
