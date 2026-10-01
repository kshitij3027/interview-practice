package screenflow;
import java.nio.file.Path;
import java.util.List;
public final class StarterTest {
  public static void main(String[] args)throws Exception{
    List<Models.Screen> seed=FixtureLoader.loadScreens(Path.of("fixtures/screens.csv"));
    check(seed.size()==6,"loads screens");
    ScreenStore store=new ScreenStore(seed);
    check(store.datasetRevision()==1,"dataset revision starts at 1");
    List<Models.Screen> all=store.list(null,null);
    check(all.get(0).venue.equals("Atlas Center")&&all.get(0).zone.equals("concourse"),"deterministic ordering");
    check(store.list("storefront","active").size()==2,"filters combine");
    Models.Screen lobby=store.get("s-lobby").orElseThrow();
    Models.MutationResult changed=store.updateMode("s-lobby","muted",lobby.revision);
    check(changed.changed&&changed.screen.revision==lobby.revision+1&&changed.datasetRevision==2,"mode change increments once");
    Models.MutationResult noop=store.updateMode("s-lobby","muted",changed.screen.revision);
    check(!noop.changed&&noop.datasetRevision==2,"same mode no-op");
    boolean stale=false;try{store.updateMode("s-lobby","normal",lobby.revision);}catch(ScreenStore.StaleRevisionException e){stale=e.current.revision==changed.screen.revision;}
    check(stale,"stale mode rejected");
    System.out.println("7/7 starter tests passed");
  }
  static void check(boolean c,String m){if(!c)throw new AssertionError(m);}
}
