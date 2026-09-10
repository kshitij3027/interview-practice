package redactdesk;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

final class Server {
    private static final Map<String, String> CONTENT_TYPES = Map.of(".html", "text/html; charset=utf-8", ".js", "text/javascript; charset=utf-8", ".css", "text/css; charset=utf-8");
    static HttpServer create(int port, Store store, Path webDir) throws IOException { HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", port), 0); server.createContext("/api/", new Routes(store)); server.createContext("/", exchange -> serveStatic(exchange, webDir)); return server; }
    private static void serveStatic(HttpExchange exchange, Path webDir) throws IOException {
        if (!exchange.getRequestMethod().equals("GET")) { Http.noBody(exchange, 405); return; }
        String requested = exchange.getRequestURI().getPath(); if (requested.equals("/")) requested = "/index.html"; Path file = webDir.resolve(requested.substring(1)).normalize();
        if (!file.startsWith(webDir.normalize()) || !Files.isRegularFile(file)) { Http.noBody(exchange, 404); return; }
        byte[] bytes = Files.readAllBytes(file); String name = file.getFileName().toString(); String type = CONTENT_TYPES.entrySet().stream().filter(e -> name.endsWith(e.getKey())).map(Map.Entry::getValue).findFirst().orElse("application/octet-stream");
        exchange.getResponseHeaders().set("Content-Type", type); exchange.sendResponseHeaders(200, bytes.length); exchange.getResponseBody().write(bytes); exchange.close();
    }
    private Server() {}
}
