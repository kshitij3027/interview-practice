package fulfill;

import fulfill.Models.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public final class Store {
    private final List<Warehouse> warehouses; private final Map<String,InventoryItem> inventory=new LinkedHashMap<>(); private final Map<String,Order> orders=new LinkedHashMap<>(); private long inventoryRevision=1;
    public Store(Path fixtureDir) throws IOException { warehouses=FixtureLoader.warehouses(fixtureDir.resolve("warehouses.csv")); for(InventoryItem item:FixtureLoader.inventory(fixtureDir.resolve("inventory.csv"))) inventory.put(key(item.warehouseId,item.sku),item); for(Order order:FixtureLoader.orders(fixtureDir.resolve("orders.json"))) orders.put(order.id,order); }
    private static String key(String warehouseId,String sku){ return warehouseId+"\u0000"+sku; }
    public synchronized long inventoryRevision(){ return inventoryRevision; }
    public synchronized List<Warehouse> warehouses(){ return List.copyOf(warehouses); }
    public synchronized List<Order> orders(){ return new ArrayList<>(orders.values()); }
    public synchronized Order order(String id){ return orders.get(id); }
    public synchronized InventoryItem item(String warehouseId,String sku){ return inventory.get(key(warehouseId,sku)); }
    public synchronized List<InventoryItem> inventory(String sku){ return inventory.values().stream().filter(i->sku==null||sku.isBlank()||i.sku.equalsIgnoreCase(sku.trim())).toList(); }
    public synchronized AdjustmentResult adjust(String warehouseId,String sku,int delta,long expectedRevision,String reason){
        if(reason==null||reason.isBlank()) return AdjustmentResult.error("invalid_reason","reason is required",inventoryRevision);
        if(expectedRevision!=inventoryRevision) return AdjustmentResult.error("stale_revision","inventory revision changed",inventoryRevision);
        InventoryItem item=item(warehouseId,sku); if(item==null) return AdjustmentResult.error("not_found","inventory item not found",inventoryRevision);
        int next=item.onHand+delta; if(next<item.reserved) return AdjustmentResult.error("below_reserved","on_hand cannot be less than reserved",inventoryRevision); if(next<0) return AdjustmentResult.error("negative_stock","on_hand cannot be negative",inventoryRevision);
        item.onHand=next; inventoryRevision++; return new AdjustmentResult(true,null,null,inventoryRevision,item.toMap());
    }
    public record AdjustmentResult(boolean ok,String code,String message,long revision,Map<String,Object> item){ static AdjustmentResult error(String code,String message,long revision){ return new AdjustmentResult(false,code,message,revision,null); } }
}
