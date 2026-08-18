package fulfill;

import java.util.*;

public final class Json {
    private Json() {}

    public static Object parse(String text) { return new Parser(text).parse(); }

    public static String stringify(Object value) {
        if (value == null) return "null";
        if (value instanceof String s) return quote(s);
        if (value instanceof Number || value instanceof Boolean) return value.toString();
        if (value instanceof Map<?, ?> map) {
            StringJoiner j = new StringJoiner(",", "{", "}");
            for (var e : map.entrySet()) j.add(quote(String.valueOf(e.getKey())) + ":" + stringify(e.getValue()));
            return j.toString();
        }
        if (value instanceof Iterable<?> items) {
            StringJoiner j = new StringJoiner(",", "[", "]");
            for (Object item : items) j.add(stringify(item));
            return j.toString();
        }
        throw new IllegalArgumentException("Unsupported JSON value: " + value.getClass());
    }

    private static String quote(String s) { return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r") + "\""; }

    private static final class Parser {
        private final String s; private int i;
        Parser(String s) { this.s = s; }
        Object parse() { Object v = value(); ws(); if (i != s.length()) fail(); return v; }
        private Object value() {
            ws(); if (i >= s.length()) fail(); char c=s.charAt(i);
            if (c=='{') return object(); if (c=='[') return array(); if (c=='\"') return string();
            if (c=='t' && take("true")) return true; if (c=='f' && take("false")) return false; if (c=='n' && take("null")) return null;
            return number();
        }
        private Map<String,Object> object() {
            i++; Map<String,Object> m=new LinkedHashMap<>(); ws(); if (peek('}')) { i++; return m; }
            while (true) { ws(); String k=string(); ws(); expect(':'); m.put(k,value()); ws(); if (peek('}')) {i++; return m;} expect(','); }
        }
        private List<Object> array() {
            i++; List<Object> a=new ArrayList<>(); ws(); if (peek(']')) {i++; return a;}
            while (true) { a.add(value()); ws(); if (peek(']')) {i++; return a;} expect(','); }
        }
        private String string() {
            expect('\"'); StringBuilder b=new StringBuilder();
            while (i<s.length()) { char c=s.charAt(i++); if(c=='\"') return b.toString(); if(c=='\\'){ if(i>=s.length()) fail(); char e=s.charAt(i++); b.append(switch(e){case '\"'->'\"';case '\\'->'\\';case '/'->'/';case 'b'->'\b';case 'f'->'\f';case 'n'->'\n';case 'r'->'\r';case 't'->'\t';default->throw new IllegalArgumentException("Unsupported escape");}); } else b.append(c); }
            fail(); return null;
        }
        private Number number() {
            int start=i; if(peek('-')) i++; while(i<s.length() && Character.isDigit(s.charAt(i))) i++;
            if(i<s.length() && s.charAt(i)=='.'){i++; while(i<s.length()&&Character.isDigit(s.charAt(i))) i++;}
            String n=s.substring(start,i); if(n.isEmpty()||n.equals("-")) fail(); if (n.contains(".")) return Double.valueOf(n); return Long.valueOf(n);
        }
        private void ws(){ while(i<s.length() && Character.isWhitespace(s.charAt(i))) i++; }
        private boolean peek(char c){ return i<s.length() && s.charAt(i)==c; }
        private void expect(char c){ ws(); if(!peek(c)) fail(); i++; }
        private boolean take(String x){ if(s.startsWith(x,i)){i+=x.length();return true;}return false; }
        private void fail(){ throw new IllegalArgumentException("Invalid JSON near position " + i); }
    }
}
