package screenflow;
import java.util.*;

final class ScreenService {
  private final ScreenStore store;
  ScreenService(ScreenStore store){this.store=store;}
  Map<String,Object> list(String zone,String status){
    Map<String,Object> out=new LinkedHashMap<>();
    out.put("datasetRevision",store.datasetRevision());
    out.put("screens",store.list(zone,status).stream().map(Models.Screen::toMap).toList());
    return out;
  }
  Map<String,Object> detail(String id){
    Models.Screen s=store.get(id).orElseThrow(()->new IllegalArgumentException("unknown screen"));
    Map<String,Object> out=new LinkedHashMap<>();out.put("datasetRevision",store.datasetRevision());out.put("screen",s.toMap());return out;
  }
  Map<String,Object> updateMode(String id,String mode,int expectedRevision){
    Models.MutationResult r=store.updateMode(id,mode,expectedRevision);
    Map<String,Object> out=new LinkedHashMap<>();out.put("changed",r.changed);out.put("datasetRevision",r.datasetRevision);out.put("screen",r.screen.toMap());return out;
  }
}
