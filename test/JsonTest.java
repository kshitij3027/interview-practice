package fulfill;
import java.util.*;
public final class JsonTest { @SuppressWarnings("unchecked") public static void run(){ var parsed=(Map<String,Object>)Json.parse("{\"a\":1,\"b\":[true,\"x\"]}"); TestSupport.eq(1L,parsed.get("a"),"integer parse"); TestSupport.eq("x",((List<Object>)parsed.get("b")).get(1),"array parse"); TestSupport.eq("{\"ok\":true}",Json.stringify(Map.of("ok",true)),"stringify"); } }
