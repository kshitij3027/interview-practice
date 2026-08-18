package fulfill;

import com.sun.net.httpserver.HttpExchange;
import java.io.*; import java.net.*; import java.nio.charset.StandardCharsets; import java.util.*;

public final class HttpUtil {
    private HttpUtil() {}
    public static Map<String,String> query(URI uri){ Map<String,String> out=new HashMap<>(); String q=uri.getRawQuery(); if(q==null) return out; for(String part:q.split("&")){String[] p=part.split("=",2); out.put(decode(p[0]),p.length>1?decode(p[1]):"");} return out; }
    private static String decode(String s){ return URLDecoder.decode(s,StandardCharsets.UTF_8); }
    public static String body(HttpExchange ex) throws IOException { return new String(ex.getRequestBody().readAllBytes(),StandardCharsets.UTF_8); }
    public static void json(HttpExchange ex,int status,Object body) throws IOException { byte[] bytes=Json.stringify(body).getBytes(StandardCharsets.UTF_8); ex.getResponseHeaders().set("Content-Type","application/json"); cors(ex); ex.sendResponseHeaders(status,bytes.length); try(OutputStream os=ex.getResponseBody()){os.write(bytes);} }
    public static void empty(HttpExchange ex,int status) throws IOException { cors(ex); ex.sendResponseHeaders(status,-1); ex.close(); }
    public static void cors(HttpExchange ex){ ex.getResponseHeaders().set("Access-Control-Allow-Origin","*"); ex.getResponseHeaders().set("Access-Control-Allow-Headers","Content-Type"); ex.getResponseHeaders().set("Access-Control-Allow-Methods","GET,POST,OPTIONS"); }
}
