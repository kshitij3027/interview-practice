package fulfill;

import com.sun.net.httpserver.HttpServer; import java.net.*; import java.nio.file.*; import java.util.concurrent.Executors;

public final class App {
    public static void main(String[] args) throws Exception { int port=args.length>0?Integer.parseInt(args[0]):3001; Store store=new Store(Path.of("fixtures")); HttpServer server=HttpServer.create(new InetSocketAddress(port),0); server.createContext("/",new Routes(new InventoryService(store))); server.setExecutor(Executors.newFixedThreadPool(8)); server.start(); System.out.println("FulfillFlow API listening on http://localhost:"+port); }
}
