package screenflow;
import com.sun.net.httpserver.HttpServer;
import java.nio.file.Path;
public final class Main {
  public static void main(String[] args)throws Exception{
    int port=args.length>0?Integer.parseInt(args[0]):8080;
    Path root=Path.of(".").toAbsolutePath().normalize();
    ScreenStore store=new ScreenStore(FixtureLoader.loadScreens(root.resolve("fixtures/screens.csv")));
    HttpServer server=new HttpApi(new ScreenService(store),root.resolve("web")).start(port);
    System.out.println("ScreenFlow listening on http://localhost:"+port);
    Runtime.getRuntime().addShutdownHook(new Thread(()->server.stop(0)));
  }
}
