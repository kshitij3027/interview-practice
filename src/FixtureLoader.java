package fulfill;

import fulfill.Models.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public final class FixtureLoader {
    private FixtureLoader() {}
    public static List<Warehouse> warehouses(Path path) throws IOException {
        List<String> rows=Files.readAllLines(path); List<Warehouse> out=new ArrayList<>();
        for(int i=1;i<rows.size();i++){ if(rows.get(i).isBlank()) continue; String[] p=rows.get(i).split(",",-1); out.add(new Warehouse(p[0],p[1],p[2],Integer.parseInt(p[3]))); } return out;
    }
    public static List<InventoryItem> inventory(Path path) throws IOException {
        List<String> rows=Files.readAllLines(path); List<InventoryItem> out=new ArrayList<>();
        for(int i=1;i<rows.size();i++){ if(rows.get(i).isBlank()) continue; String[] p=rows.get(i).split(",",-1); out.add(new InventoryItem(p[0],p[1],Integer.parseInt(p[2]),Integer.parseInt(p[3]))); } return out;
    }
    @SuppressWarnings("unchecked") public static List<Order> orders(Path path) throws IOException {
        Object parsed=Json.parse(Files.readString(path)); List<Order> out=new ArrayList<>();
        for(Object raw:(List<Object>)parsed){ Map<String,Object> m=(Map<String,Object>)raw; List<OrderLine> lines=new ArrayList<>(); for(Object lineRaw:(List<Object>)m.get("lines")){ Map<String,Object> line=(Map<String,Object>)lineRaw; lines.add(new OrderLine((String)line.get("sku"),((Number)line.get("qty")).intValue())); } out.add(new Order((String)m.get("id"),(String)m.get("customer"),(String)m.get("shipping_zone"),(String)m.get("status"),((Number)m.get("revision")).longValue(),lines)); } return out;
    }
}
