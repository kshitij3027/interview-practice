package screenflow;
import java.util.*;

final class ScreenStore {
  private final Map<String,Models.Screen> screens=new LinkedHashMap<>();
  private int datasetRevision=1;
  ScreenStore(List<Models.Screen> seed){for(Models.Screen s:seed)screens.put(s.id,s);}
  synchronized int datasetRevision(){return datasetRevision;}
  synchronized List<Models.Screen> list(String zone,String status){
    List<Models.Screen> out=new ArrayList<>();
    for(Models.Screen s:screens.values()){
      if(zone!=null&&!zone.isBlank()&&!s.zone.equals(zone)) continue;
      if(status!=null&&!status.isBlank()&&!s.status.equals(status)) continue;
      out.add(copy(s));
    }
    out.sort(Comparator.comparing((Models.Screen s)->s.venue).thenComparing(s->s.zone).thenComparing(s->s.id));
    return out;
  }
  synchronized Optional<Models.Screen> get(String id){Models.Screen s=screens.get(id);return s==null?Optional.empty():Optional.of(copy(s));}
  synchronized Models.MutationResult updateMode(String id,String mode,int expectedRevision){
    Models.Screen s=screens.get(id); if(s==null) throw new IllegalArgumentException("unknown screen");
    if(!mode.equals("normal")&&!mode.equals("muted")) throw new IllegalArgumentException("mode must be normal or muted");
    if(s.revision!=expectedRevision) throw new StaleRevisionException(copy(s),datasetRevision);
    if(s.playbackMode.equals(mode)) return new Models.MutationResult(copy(s),false,datasetRevision);
    s.playbackMode=mode; s.revision++; datasetRevision++;
    return new Models.MutationResult(copy(s),true,datasetRevision);
  }
  private static Models.Screen copy(Models.Screen s){return new Models.Screen(s.id,s.venue,s.zone,s.status,s.baselinePlaylist,s.playbackMode,s.revision);}
  static final class StaleRevisionException extends RuntimeException{
    final Models.Screen current; final int datasetRevision;
    StaleRevisionException(Models.Screen current,int datasetRevision){super("stale screen revision");this.current=current;this.datasetRevision=datasetRevision;}
  }
}
