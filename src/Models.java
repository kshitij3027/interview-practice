package fulfill;

import java.util.*;

public final class Models {
    private Models() {}

    public record Warehouse(String id, String name, String zone, int pickRank) {
        public Map<String,Object> toMap() { return Map.of("id",id,"name",name,"zone",zone,"pick_rank",pickRank); }
    }

    public static final class InventoryItem {
        public final String warehouseId; public final String sku; public int onHand; public int reserved;
        public InventoryItem(String warehouseId, String sku, int onHand, int reserved) { this.warehouseId=warehouseId; this.sku=sku; this.onHand=onHand; this.reserved=reserved; }
        public int available(){ return onHand-reserved; }
        public Map<String,Object> toMap(){ return Map.of("warehouse_id",warehouseId,"sku",sku,"on_hand",onHand,"reserved",reserved,"available",available()); }
    }

    public record OrderLine(String sku, int qty) { public Map<String,Object> toMap(){ return Map.of("sku",sku,"qty",qty); } }

    public static final class Order {
        public final String id; public final String customer; public final String shippingZone; public String status; public long revision; public final List<OrderLine> lines;
        public Order(String id,String customer,String shippingZone,String status,long revision,List<OrderLine> lines){ this.id=id;this.customer=customer;this.shippingZone=shippingZone;this.status=status;this.revision=revision;this.lines=List.copyOf(lines); }
        public Map<String,Object> toMap(){ return Map.of("id",id,"customer",customer,"shipping_zone",shippingZone,"status",status,"revision",revision,"lines",lines.stream().map(OrderLine::toMap).toList()); }
    }
}
