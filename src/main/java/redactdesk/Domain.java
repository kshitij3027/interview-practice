package redactdesk;

import java.util.List;
import java.util.Map;

final class Domain {
    record Page(int number, String text) {}
    record Redaction(String id, int page, int start, int end, String category, String source, String note) {}
    record Suggestion(String id, String documentId, int page, int start, int end, String category, double confidence) {}
    record DocumentSnapshot(String id, String title, String status, int revision, List<Page> pages, List<Redaction> redactions) {}
    record DocumentSummary(String id, String title, String status, int revision, int redactionCount) {}
    record ListResult(long datasetRevision, List<DocumentSummary> documents) {}
    record DetailResult(long datasetRevision, DocumentSnapshot document) {}
    record MutationResult(long datasetRevision, DocumentSnapshot document, Redaction redaction) {}

    static Map<String, Object> summaryToMap(DocumentSummary d) {
        return Map.of("id", d.id(), "title", d.title(), "status", d.status(), "revision", d.revision(), "redactionCount", d.redactionCount());
    }
    static Map<String, Object> pageToMap(Page p) { return Map.of("number", p.number(), "text", p.text()); }
    static Map<String, Object> redactionToMap(Redaction r) {
        return Map.of("id", r.id(), "page", r.page(), "start", r.start(), "end", r.end(), "category", r.category(), "source", r.source(), "note", r.note());
    }
    static Map<String, Object> documentToMap(DocumentSnapshot d) {
        return Map.of("id", d.id(), "title", d.title(), "status", d.status(), "revision", d.revision(), "pages", d.pages().stream().map(Domain::pageToMap).toList(), "redactions", d.redactions().stream().map(Domain::redactionToMap).toList());
    }
}
