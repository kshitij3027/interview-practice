package fulfill;

import java.util.*;

public final class InventoryService {
    private final Store store; public InventoryService(Store store){ this.store=store; }
    public Map<String,Object> inventory(String sku){ return Map.of("revision",store.inventoryRevision(),"items",store.inventory(sku).stream().map(i->i.toMap()).toList()); }
    public Map<String,Object> orders(){ return Map.of("orders",store.orders().stream().map(o->o.toMap()).toList(),"inventory_revision",store.inventoryRevision()); }
    public Map<String,Object> order(String id){ var order=store.order(id); if(order==null) return null; return Map.of("order",order.toMap(),"inventory_revision",store.inventoryRevision()); }
    public Store.AdjustmentResult adjust(String warehouseId,String sku,int delta,long expectedRevision,String reason){ return store.adjust(warehouseId,sku,delta,expectedRevision,reason); }
}
