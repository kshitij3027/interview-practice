package redactdesk;

final class TestSupport {
    static void equal(Object expected, Object actual, String message) { if (expected == null ? actual != null : !expected.equals(actual)) throw new AssertionError(message + " expected=" + expected + " actual=" + actual); }
    static void isTrue(boolean condition, String message) { if (!condition) throw new AssertionError(message); }
    static ApiException expectApi(String code, Runnable fn) { try { fn.run(); } catch (ApiException e) { equal(code, e.code, "unexpected error code"); return e; } throw new AssertionError("expected ApiException " + code); }
    private TestSupport() {}
}
