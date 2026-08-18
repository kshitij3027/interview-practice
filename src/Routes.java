package fulfill;

import com.sun.net.httpserver.*; import java.io.*; import java.util.*;

public final class Routes implements HttpHandler {
    private final InventoryService service; public Routes(InventoryService service){ this.service=service; }
    @Override @SuppressWarnings("unchecked") public void handle(HttpExchange ex) throws IOException {
        if(ex.getRequestMethod().equals("OPTIONS")){ HttpUtil.empty(ex,204); return; }
        try {
            String path=ex.getRequestURI().getPath(); String method=ex.getRequestMethod();
            if(method.equals("GET") && path.equals("/api/health")){ HttpUtil.json(ex,200,Map.of("ok",true)); return; }
            if(method.equals("GET") && path.equals("/api/orders")){ HttpUtil.json(ex,200,service.orders()); return; }
            if(method.equals("GET") && path.startsWith("/api/orders/")){ String id=path.substring("/api/orders/".length()); var body=service.order(id); if(body==null) HttpUtil.json(ex,404,Map.of("error","order_not_found")); else HttpUtil.json(ex,200,body); return; }
            if(method.equals("GET") && path.equals("/api/inventory")){ HttpUtil.json(ex,200,service.inventory(HttpUtil.query(ex.getRequestURI()).get("sku"))); return; }
            if(method.equals("POST") && path.equals("/api/inventory/adjust")){ Map<String,Object> b=(Map<String,Object>)Json.parse(HttpUtil.body(ex)); var r=service.adjust((String)b.get("warehouse_id"),(String)b.get("sku"),((Number)b.get("delta")).intValue(),((Number)b.get("expected_revision")).longValue(),(String)b.get("reason")); if(r.ok()) HttpUtil.json(ex,200,Map.of("revision",r.revision(),"item",r.item())); else HttpUtil.json(ex,r.code().equals("stale_revision")?409:400,Map.of("error",r.code(),"message",r.message(),"revision",r.revision())); return; }
            HttpUtil.json(ex,404,Map.of("error","not_found"));
        } catch(IllegalArgumentException e){ HttpUtil.json(ex,400,Map.of("error","bad_request","message",e.getMessage())); }
    }
}
