package screenflow;
import java.util.*;
final class JsonUtil {
  static String stringify(Object v){
    if(v==null)return "null"; if(v instanceof String s)return quote(s); if(v instanceof Number||v instanceof Boolean)return v.toString();
    if(v instanceof Map<?,?> m){StringBuilder b=new StringBuilder("{");boolean first=true;for(var e:m.entrySet()){if(!first)b.append(',');first=false;b.append(quote(String.valueOf(e.getKey()))).append(':').append(stringify(e.getValue()));}return b.append('}').toString();}
    if(v instanceof Iterable<?> xs){StringBuilder b=new StringBuilder("[");boolean first=true;for(Object x:xs){if(!first)b.append(',');first=false;b.append(stringify(x));}return b.append(']').toString();}
    throw new IllegalArgumentException("unsupported JSON value");
  }
  static Map<String,String> parseFlatObject(String raw){return new Parser(raw).parse();}
  private static String quote(String s){StringBuilder b=new StringBuilder("\"");for(char c:s.toCharArray()){switch(c){case '"'->b.append("\\\"");case '\\'->b.append("\\\\");case '\n'->b.append("\\n");case '\r'->b.append("\\r");case '\t'->b.append("\\t");default->b.append(c);}}return b.append('"').toString();}
  private static final class Parser{
    final String s;int i=0;Parser(String s){this.s=s==null?"":s;}
    Map<String,String> parse(){skip();expect('{');Map<String,String> m=new LinkedHashMap<>();skip();if(peek('}')){i++;return m;}while(true){skip();String k=str();skip();expect(':');skip();String v=peek('"')?str():token();m.put(k,v);skip();if(peek('}')){i++;break;}expect(',');}skip();if(i!=s.length())throw new IllegalArgumentException("trailing JSON");return m;}
    String str(){expect('"');StringBuilder b=new StringBuilder();while(i<s.length()){char c=s.charAt(i++);if(c=='"')return b.toString();if(c=='\\'){if(i>=s.length())throw new IllegalArgumentException("bad escape");char e=s.charAt(i++);switch(e){case '"','\\','/'->b.append(e);case 'n'->b.append('\n');case 'r'->b.append('\r');case 't'->b.append('\t');default->throw new IllegalArgumentException("unsupported escape");}}else b.append(c);}throw new IllegalArgumentException("unterminated string");}
    String token(){int st=i;while(i<s.length()&&",}".indexOf(s.charAt(i))<0)i++;String t=s.substring(st,i).trim();if(t.isEmpty())throw new IllegalArgumentException("missing value");return t.equals("null")?"":t;}
    void skip(){while(i<s.length()&&Character.isWhitespace(s.charAt(i)))i++;}boolean peek(char c){return i<s.length()&&s.charAt(i)==c;}void expect(char c){if(!peek(c))throw new IllegalArgumentException("expected "+c);i++;}
  }
  private JsonUtil(){}
}
