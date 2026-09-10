package redactdesk;

import redactdesk.Domain.DetailResult;
import redactdesk.Domain.DocumentSnapshot;
import redactdesk.Domain.DocumentSummary;
import redactdesk.Domain.ListResult;
import redactdesk.Domain.MutationResult;
import redactdesk.Domain.Page;
import redactdesk.Domain.Redaction;
import redactdesk.Domain.Suggestion;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

final class Store {
    private static final Set<String> CATEGORIES = Set.of("personal", "financial", "credentials");
    private static final class DocumentState {
        final String id; final String title; final String status; int revision;
        final List<Page> pages = new ArrayList<>(); final List<Redaction> redactions = new ArrayList<>();
        DocumentState(String id, String title, String status, int revision) { this.id = id; this.title = title; this.status = status; this.revision = revision; }
    }
    private final Map<String, DocumentState> documents = new LinkedHashMap<>();
    private final Map<String, List<Suggestion>> suggestionsByDocument = new HashMap<>();
    private long datasetRevision = 1; private int nextManualId = 100;
    static Store load(Path fixtureDir) throws IOException {
        Store store = new Store();
        for (Map<String, String> row : Csv.read(fixtureDir.resolve("documents.csv"))) {
            DocumentState doc = new DocumentState(row.get("document_id"), row.get("title"), row.get("status"), Integer.parseInt(row.get("revision"))); store.documents.put(doc.id, doc);
        }
        for (Map<String, String> row : Csv.read(fixtureDir.resolve("pages.csv"))) store.requireDocument(row.get("document_id")).pages.add(new Page(Integer.parseInt(row.get("page")), row.get("text")));
        for (Map<String, String> row : Csv.read(fixtureDir.resolve("redactions.csv"))) {
            DocumentState doc = store.requireDocument(row.get("document_id"));
            doc.redactions.add(new Redaction(row.get("redaction_id"), Integer.parseInt(row.get("page")), Integer.parseInt(row.get("start")), Integer.parseInt(row.get("end")), row.get("category"), row.get("source"), row.get("note")));
        }
        for (Map<String, String> row : Csv.read(fixtureDir.resolve("suggestions.csv"))) {
            Suggestion suggestion = new Suggestion(row.get("suggestion_id"), row.get("document_id"), Integer.parseInt(row.get("page")), Integer.parseInt(row.get("start")), Integer.parseInt(row.get("end")), row.get("category"), Double.parseDouble(row.get("confidence")));
            store.suggestionsByDocument.computeIfAbsent(suggestion.documentId(), ignored -> new ArrayList<>()).add(suggestion);
        }
        store.documents.values().forEach(doc -> { doc.pages.sort(Comparator.comparingInt(Page::number)); sortRedactions(doc.redactions); }); return store;
    }
    synchronized ListResult listDocuments(String status) {
        String normalized = status == null || status.isBlank() ? "all" : status.trim().toLowerCase();
        if (!Set.of("all", "reviewing", "approved").contains(normalized)) throw new ApiException(400, "invalid_status", "status must be all, reviewing, or approved");
        List<DocumentSummary> summaries = documents.values().stream().filter(doc -> normalized.equals("all") || doc.status.equals(normalized)).sorted(Comparator.comparing((DocumentState d) -> d.title.toLowerCase()).thenComparing(d -> d.id)).map(this::summary).toList();
        return new ListResult(datasetRevision, summaries);
    }
    synchronized DetailResult getDocument(String id) { return new DetailResult(datasetRevision, snapshot(requireDocument(id))); }
    synchronized List<Suggestion> getSuggestions(String documentId) { requireDocument(documentId); return List.copyOf(suggestionsByDocument.getOrDefault(documentId, List.of())); }
    synchronized MutationResult addManualRedaction(String id, int page, int start, int end, String category, String note, int expectedRevision) {
        DocumentState doc = requireDocument(id);
        if (doc.revision != expectedRevision) throw new ApiException(409, "stale_revision", "document revision changed", Domain.documentToMap(snapshot(doc)));
        if (!doc.status.equals("reviewing")) throw new ApiException(409, "document_locked", "approved documents cannot be changed");
        String normalizedCategory = category == null ? "" : category.trim().toLowerCase();
        if (!CATEGORIES.contains(normalizedCategory)) throw new ApiException(400, "invalid_category", "category must be personal, financial, or credentials");
        String normalizedNote = note == null ? "" : note.trim();
        if (normalizedNote.isEmpty() || normalizedNote.length() > 120) throw new ApiException(400, "invalid_note", "note must be 1-120 characters after trimming");
        Page target = doc.pages.stream().filter(p -> p.number() == page).findFirst().orElseThrow(() -> new ApiException(400, "invalid_page", "page does not exist"));
        if (start < 0 || end <= start || end > target.text().length()) throw new ApiException(400, "invalid_range", "range must be within the selected page");
        boolean overlaps = doc.redactions.stream().anyMatch(r -> r.page() == page && start < r.end() && end > r.start());
        if (overlaps) throw new ApiException(409, "range_overlap", "manual redactions may not overlap an existing redaction");
        Redaction redaction = new Redaction("manual-" + nextManualId++, page, start, end, normalizedCategory, "manual", normalizedNote);
        doc.redactions.add(redaction); sortRedactions(doc.redactions); doc.revision++; datasetRevision++;
        return new MutationResult(datasetRevision, snapshot(doc), redaction);
    }
    private DocumentState requireDocument(String id) { DocumentState doc = documents.get(id); if (doc == null) throw new ApiException(404, "document_not_found", "document not found"); return doc; }
    private DocumentSummary summary(DocumentState doc) { return new DocumentSummary(doc.id, doc.title, doc.status, doc.revision, doc.redactions.size()); }
    private DocumentSnapshot snapshot(DocumentState doc) { return new DocumentSnapshot(doc.id, doc.title, doc.status, doc.revision, List.copyOf(doc.pages), List.copyOf(doc.redactions)); }
    private static void sortRedactions(List<Redaction> redactions) { redactions.sort(Comparator.comparingInt(Redaction::page).thenComparingInt(Redaction::start).thenComparingInt(Redaction::end).thenComparing(Redaction::id)); }
}
