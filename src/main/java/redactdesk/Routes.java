package redactdesk;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import redactdesk.Domain.DetailResult;
import redactdesk.Domain.ListResult;
import redactdesk.Domain.MutationResult;
import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.Map;

final class Routes implements HttpHandler {
    private final Store store; Routes(Store store) { this.store = store; }
    @Override public void handle(HttpExchange exchange) throws IOException {
        try { route(exchange); }
        catch (ApiException e) { Map<String, Object> error = new LinkedHashMap<>(); error.put("code", e.code); error.put("message", e.getMessage()); if (e.current != null) error.put("current", e.current); Http.json(exchange, e.status, Map.of("error", error)); }
        catch (Exception e) { Http.json(exchange, 500, Map.of("error", Map.of("code", "internal_error", "message", "unexpected server error"))); }
    }
    private void route(HttpExchange exchange) throws IOException {
        String method = exchange.getRequestMethod(); String path = exchange.getRequestURI().getPath();
        if (method.equals("OPTIONS")) { Http.noBody(exchange, 204); return; }
        if (method.equals("GET") && path.equals("/api/health")) { Http.json(exchange, 200, Map.of("ok", true)); return; }
        if (method.equals("GET") && path.equals("/api/documents")) {
            ListResult result = store.listDocuments(Http.query(exchange).get("status")); Http.json(exchange, 200, Map.of("datasetRevision", result.datasetRevision(), "documents", result.documents().stream().map(Domain::summaryToMap).toList())); return;
        }
        String[] parts = path.split("/");
        if (parts.length == 4 && parts[1].equals("api") && parts[2].equals("documents") && method.equals("GET")) {
            DetailResult result = store.getDocument(parts[3]); Http.json(exchange, 200, Map.of("datasetRevision", result.datasetRevision(), "document", Domain.documentToMap(result.document()))); return;
        }
        if (parts.length == 5 && parts[1].equals("api") && parts[2].equals("documents") && parts[4].equals("redactions") && method.equals("POST")) {
            Map<String, Object> body = Http.jsonBody(exchange);
            MutationResult result = store.addManualRedaction(parts[3], Http.integer(body, "page"), Http.integer(body, "start"), Http.integer(body, "end"), Http.string(body, "category"), Http.string(body, "note"), Http.integer(body, "expectedRevision"));
            Http.json(exchange, 201, Map.of("datasetRevision", result.datasetRevision(), "document", Domain.documentToMap(result.document()), "redaction", Domain.redactionToMap(result.redaction()))); return;
        }
        throw new ApiException(404, "not_found", "route not found");
    }
}
