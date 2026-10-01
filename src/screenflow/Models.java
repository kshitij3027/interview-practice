package screenflow;
import java.util.*;
final class Models {
  static final class Screen {
    final String id, venue, zone, status, baselinePlaylist; String playbackMode; int revision;
    Screen(String id,String venue,String zone,String status,String baselinePlaylist,String playbackMode,int revision){this.id=id;this.venue=venue;this.zone=zone;this.status=status;this.baselinePlaylist=baselinePlaylist;this.playbackMode=playbackMode;this.revision=revision;}
    Map<String,Object> toMap(){Map<String,Object> m=new LinkedHashMap<>();m.put("id",id);m.put("venue",venue);m.put("zone",zone);m.put("status",status);m.put("baselinePlaylist",baselinePlaylist);m.put("playbackMode",playbackMode);m.put("revision",revision);return m;}
  }
  static final class MutationResult { final Screen screen; final boolean changed; final int datasetRevision; MutationResult(Screen s,boolean c,int d){screen=s;changed=c;datasetRevision=d;} }
  private Models(){}
}
