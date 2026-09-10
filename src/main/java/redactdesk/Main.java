package redactdesk;

import com.sun.net.httpserver.HttpServer;
import java.nio.file.Path;

public final class Main {
    public static void main(String[] args) throws Exception { int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080")); Store store = Store.load(Path.of("fixtures")); HttpServer server = Server.create(port, store, Path.of("web")); server.start(); System.out.println("RedactDesk running at http://127.0.0.1:" + port); }
}
