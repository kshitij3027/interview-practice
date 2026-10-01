package screenflow;

import com.sun.net.httpserver.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.Executors;

final class HttpApi {
  private final ScreenService service; private final Path webRoot;
  HttpApi(ScreenService service,Path webRoot){this.service=service;this.webRoot=webRoot;}
  HttpServer start(int port) throws IOException {
    HttpServer server=HttpServer.create(new InetSocketAddress(port),0);
    server.createContext("/",new Handler());server.setExecutor(Executors.newCachedThreadPool());server.start();return server;
  }
  private final class Handler implements HttpHandler {
    public void handle(HttpExchange ex) throws IOException {
      try{
        String path=ex.getRequestURI().getPath();
        if(path.startsWith("/api/")) handleApi(ex,path); else serveStatic(ex,path);
      }catch(ScreenStore.StaleRevisionException e){
        Map<String,Object> b=new LinkedHashMap<>();b.put("error","stale_revision");b.put("message",e.getMessage());b.put("datasetRevision",e.datasetRevision);b.put("current",e.current.toMap());sendJson(ex,409,b);
      }catch(IllegalArgumentException e){sendJson(ex,400,Map.of("error","bad_request","message",e.getMessage()));}
      catch(Exception e){e.printStackTrace();sendJson(ex,500,Map.of("error","internal_error","message","unexpected server error"));}
      finally{ex.close();}
    }
    private void handleApi(HttpExchange ex,String path) throws Exception {
      String method=ex.getRequestMethod();
      if(method.equals("GET")&&path.equals("/api/health")){sendJson(ex,200,Map.of("ok",true));return;}
      if(method.equals("GET")&&path.equals("/api/screens")){
        Map<String,String> q=query(ex);sendJson(ex,200,service.list(q.get("zone"),q.get("status")));return;
      }
      if(path.startsWith("/api/screens/")){
        String suffix=path.substring("/api/screens/".length());
        if(!suffix.contains("/")){
          if(!method.equals("GET")){methodNotAllowed(ex);return;}
          sendJson(ex,200,service.detail(decode(suffix)));return;
        }
        if(suffix.endsWith("/mode")&&method.equals("POST")){
          String id=decode(suffix.substring(0,suffix.length()-"/mode".length()));
          sleepBounded(query(ex).get("delay_ms"));
          Map<String,String> body=JsonUtil.parseFlatObject(readBody(ex));
          String mode=required(body,"mode");int expected=parseInt(required(body,"expectedRevision"),"expectedRevision");
          sendJson(ex,200,service.updateMode(id,mode,expected));return;
        }
      }
      sendJson(ex,404,Map.of("error","not_found","message","route not found"));
    }
    private void serveStatic(HttpExchange ex,String path) throws IOException {
      if(!ex.getRequestMethod().equals("GET")){methodNotAllowed(ex);return;}
      String rel=path.equals("/")?"index.html":path.substring(1);if(rel.contains("..")){sendJson(ex,400,Map.of("error","bad_path"));return;}
      Path file=webRoot.resolve(rel).normalize();if(!file.startsWith(webRoot)||!Files.exists(file)||Files.isDirectory(file)){sendJson(ex,404,Map.of("error","not_found"));return;}
      byte[] data=Files.readAllBytes(file);String type=rel.endsWith(".js")?"text/javascript; charset=utf-8":rel.endsWith(".css")?"text/css; charset=utf-8":"text/html; charset=utf-8";
      ex.getResponseHeaders().set("Content-Type",type);ex.sendResponseHeaders(200,data.length);ex.getResponseBody().write(data);
    }
    private void methodNotAllowed(HttpExchange ex) throws IOException {sendJson(ex,405,Map.of("error","method_not_allowed"));}
  }
  private static String required(Map<String,String>b,String k){String v=b.get(k);if(v==null||v.isBlank())throw new IllegalArgumentException("missing "+k);return v;}
  private static int parseInt(String raw,String f){try{return Integer.parseInt(raw);}catch(NumberFormatException e){throw new IllegalArgumentException(f+" must be an integer");}}
  private static void sleepBounded(String raw) throws InterruptedException {if(raw==null||raw.isBlank())return;int d=parseInt(raw,"delay_ms");if(d<0||d>2000)throw new IllegalArgumentException("delay_ms must be 0..2000");Thread.sleep(d);}
  private static String readBody(HttpExchange ex)throws IOException{return new String(ex.getRequestBody().readAllBytes(),StandardCharsets.UTF_8);}
  private static Map<String,String> query(HttpExchange ex){Map<String,String> out=new LinkedHashMap<>();String raw=ex.getRequestURI().getRawQuery();if(raw==null||raw.isBlank())return out;for(String part:raw.split("&")){String[] kv=part.split("=",2);out.put(decode(kv[0]),kv.length==2?decode(kv[1]):"");}return out;}
  private static String decode(String s){return URLDecoder.decode(s,StandardCharsets.UTF_8);}
  private static void sendJson(HttpExchange ex,int status,Object v)throws IOException{byte[] d=JsonUtil.stringify(v).getBytes(StandardCharsets.UTF_8);ex.getResponseHeaders().set("Content-Type","application/json; charset=utf-8");ex.sendResponseHeaders(status,d.length);ex.getResponseBody().write(d);}
}
