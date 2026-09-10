package redactdesk;

final class ApiException extends RuntimeException {
    final int status; final String code; final Object current;
    ApiException(int status, String code, String message) { this(status, code, message, null); }
    ApiException(int status, String code, String message, Object current) { super(message); this.status = status; this.code = code; this.current = current; }
}
