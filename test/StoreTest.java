package fulfill;
import java.nio.file.Path;
public final class StoreTest { public static void run() throws Exception { Store s=new Store(Path.of("fixtures")); TestSupport.eq(1L,s.inventoryRevision(),"initial inventory revision"); TestSupport.eq(4,s.warehouses().size(),"warehouses loaded"); TestSupport.eq(12,s.inventory(null).size(),"inventory loaded"); TestSupport.eq(4,s.orders().size(),"orders loaded"); TestSupport.eq(3,s.order("ord-1002").lines.size(),"duplicate sku lines are preserved in source order"); } }
