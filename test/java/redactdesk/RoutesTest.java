package redactdesk;

import com.sun.net.httpserver.HttpServer;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Path;
import java.time.Duration;

public final class RoutesTest {
    public static void main(String[] args) throws Exception {
        Store store = Store.load(Path.of("fixtures")); HttpServer server = Server.create(0, store, Path.of("web")); server.start();
        try {
            int port = server.getAddress().getPort(); HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2)).build();
            var health = client.send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/health")).GET().build(), HttpResponse.BodyHandlers.ofString()); TestSupport.equal(200, health.statusCode(), "health status"); TestSupport.isTrue(health.body().contains("\"ok\":true"), "health body");
            var list = client.send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/documents?status=reviewing")).GET().build(), HttpResponse.BodyHandlers.ofString()); TestSupport.equal(200, list.statusCode(), "list status"); TestSupport.isTrue(list.body().contains("doc-100") && !list.body().contains("doc-300"), "reviewing filter");
            var post = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/documents/doc-100/redactions")).header("Content-Type", "application/json").POST(HttpRequest.BodyPublishers.ofString("{\"page\":1,\"start\":8,\"end\":18,\"category\":\"personal\",\"note\":\"Contact name\",\"expectedRevision\":2}")).build();
            var created = client.send(post, HttpResponse.BodyHandlers.ofString()); TestSupport.equal(201, created.statusCode(), "create status"); TestSupport.isTrue(created.body().contains("manual-100"), "created redaction id"); System.out.println("RoutesTest: 3/3 passed");
        } finally { server.stop(0); }
    }
}
