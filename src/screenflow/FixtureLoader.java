package screenflow;
import java.io.*;
import java.nio.file.*;
import java.util.*;

final class FixtureLoader {
  static List<Models.Screen> loadScreens(Path path) throws IOException {
    List<String> lines=Files.readAllLines(path);
    if(lines.isEmpty() || !lines.get(0).trim().equals("id,venue,zone,status,baseline_playlist,playback_mode,revision"))
      throw new IllegalArgumentException("unexpected screens.csv header");
    List<Models.Screen> out=new ArrayList<>(); Set<String> ids=new HashSet<>();
    for(int i=1;i<lines.size();i++){
      String line=lines.get(i).trim(); if(line.isEmpty()) continue;
      String[] p=line.split(",",-1); if(p.length!=7) throw new IllegalArgumentException("invalid screens.csv row "+(i+1));
      String id=p[0].trim(), venue=p[1].trim(), zone=p[2].trim(), status=p[3].trim(), playlist=p[4].trim(), mode=p[5].trim();
      int revision=parsePositive(p[6].trim(),"revision",i+1);
      if(id.isEmpty()||venue.isEmpty()||zone.isEmpty()||playlist.isEmpty()) throw new IllegalArgumentException("blank required field at row "+(i+1));
      if(!ids.add(id)) throw new IllegalArgumentException("duplicate screen id "+id);
      if(!Set.of("lobby","concourse","storefront").contains(zone)) throw new IllegalArgumentException("invalid zone at row "+(i+1));
      if(!Set.of("active","offline").contains(status)) throw new IllegalArgumentException("invalid status at row "+(i+1));
      if(!Set.of("normal","muted").contains(mode)) throw new IllegalArgumentException("invalid playback_mode at row "+(i+1));
      out.add(new Models.Screen(id,venue,zone,status,playlist,mode,revision));
    }
    if(out.isEmpty()) throw new IllegalArgumentException("screens fixture has no data rows");
    return out;
  }
  private static int parsePositive(String raw,String field,int row){
    try{int n=Integer.parseInt(raw);if(n<=0) throw new NumberFormatException();return n;}
    catch(NumberFormatException e){throw new IllegalArgumentException("invalid "+field+" at row "+row);}
  }
  private FixtureLoader(){}
}
